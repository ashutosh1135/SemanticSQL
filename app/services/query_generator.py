from typing import List, Dict, Any, Optional, Tuple
import uuid
import json
import logging
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from sqlalchemy.orm import Session

from app.services.embedder import generate_embeddings
from app.services.vector_store import query_vector_store, get_table_context
from app.config.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# LLM cache for performance optimization
_llm_cache = {}

def get_llm_model():
    """Returns a configured Gemini model using LangChain."""
    cache_key = f"{settings.GEMINI_MODEL}_{settings.MODEL_TEMPERATURE}"
    
    if cache_key not in _llm_cache:
        logger.info(f"Initializing LLM model {settings.GEMINI_MODEL}")
        if not settings.GEMINI_API_KEY:
            logger.warning("No GEMINI_API_KEY configured - AI features won't work properly")
            return None
            
        try:
            _llm_cache[cache_key] = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=settings.MODEL_TEMPERATURE,
                top_p=0.9,
                max_output_tokens=1024
            )
        except Exception as e:
            logger.error(f"Error initializing LLM model: {str(e)}")
            return None
            
    return _llm_cache[cache_key]

async def generate_query_from_search(
    user_query: str,
    db_session: Session,
    db_id: uuid.UUID,
    k: int = 5
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generates an SQL query based on semantic search over the schema metadata.
    
    Args:
        user_query: Natural language query from the user
        db_session: Database session
        db_id: Database ID to search against
        k: Number of top schema matches to consider
        
    Returns:
        Tuple of (generated SQL query, relevant schema metadata)
    """
    try:
        # Generate embeddings for the user query
        logger.info(f"Generating embedding for query: {user_query}")
        query_embedding = await generate_embeddings(user_query)
        
        # Perform semantic search to find relevant schema metadata
        logger.info(f"Searching for relevant schema metadata for DB {db_id}")
        relevant_schema = await query_vector_store(
            db_session=db_session,
            query_embedding=query_embedding,
            db_id=db_id,
            limit=k
        )

        if not relevant_schema:
            logger.warning(f"No relevant schema found for query: {user_query}")
            return "-- No relevant schema found for the query", []
        
        logger.info(f"Found {len(relevant_schema)} relevant schema items")
        
        # Identify relevant tables
        unique_tables = set()
        for item in relevant_schema:
            table_key = f"{item['schema_name']}.{item['table_name']}"
            unique_tables.add(table_key)
        
        logger.info(f"Identified {len(unique_tables)} unique tables: {', '.join(unique_tables)}")
        
        # Get detailed context for each relevant table
        table_contexts = []
        for table_key in unique_tables:
            schema_name, table_name = table_key.split(".")
            table_context = await get_table_context(
                db_session=db_session,
                db_id=db_id,
                table_name=table_name,
                schema_name=schema_name
            )
            table_contexts.extend(table_context)
        
        # Generate SQL query using LLM
        sql_query = await generate_sql_with_llm(user_query, table_contexts)
        
        return sql_query, relevant_schema
        
    except Exception as e:
        logger.error(f"Error generating query from search: {str(e)}", exc_info=True)
        return f"-- Error generating SQL: {str(e)}\n-- Query: {user_query}", []

async def generate_sql_with_llm(
    user_query: str,
    schema_metadata: List[Dict[str, Any]]
) -> str:
    """
    Generates SQL from natural language using LangChain and Gemini.
    
    Args:
        user_query: Natural language query from the user
        schema_metadata: List of relevant schema metadata
        
    Returns:
        Generated SQL query
    """
    llm = get_llm_model()
    if not llm or not settings.GEMINI_API_KEY:
        # If no API key, generate a simple placeholder query
        logger.warning("No LLM available - returning placeholder SQL")
        tables = list(set([item["table_name"] for item in schema_metadata]))
        return f"-- Placeholder query (no LLM API key)\nSELECT * FROM {tables[0] if tables else 'table'} LIMIT 10;"
    
    try:
        # Format schema metadata for the prompt
        formatted_schema = ""
        for item in schema_metadata:
            formatted_schema += f"- {item['description']}\n"
        
        logger.info(f"Generating SQL with LLM for query: {user_query}")
        
        # Create LangChain prompt template
        prompt_template = PromptTemplate(
            input_variables=["schema", "query"],
            template="""
You are an expert SQL database engineer. You need to convert a natural language query to a valid SQL query.

The database schema includes the following relevant information:
{schema}

User query: {query}

Generate a valid SQL query that answers the user's question. Only provide the SQL query, nothing else. 
Make sure the query is correct based on the schema information and use proper column and table names.
"""
        )
        
        chain = LLMChain(llm=llm, prompt=prompt_template)
        
        result = chain.run(schema=formatted_schema, query=user_query)
        
        sql_query = result.strip()
        
        # Handle code block formatting from the LLM
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        elif sql_query.startswith("```"):
            sql_query = sql_query.replace("```", "").strip()
        
        logger.info(f"Generated SQL query: {sql_query[:100]}...")
        return sql_query
    
    except Exception as e:
        logger.error(f"Error generating SQL with LLM: {str(e)}", exc_info=True)
        return f"-- Error generating SQL with LLM: {str(e)}\n-- Natural language query: {user_query}"

async def refine_query_with_llm(
    original_query: str, 
    user_feedback: str,
    schema_metadata: List[Dict[str, Any]]
) -> str:
    """
    Refines an existing SQL query based on user feedback.
    
    Args:
        original_query: The original SQL query
        user_feedback: User's feedback or correction
        schema_metadata: List of relevant schema metadata
        
    Returns:
        Refined SQL query
    """
    llm = get_llm_model()
    if not llm or not settings.GEMINI_API_KEY:
        logger.warning("No LLM available - cannot refine query")
        return f"-- Cannot refine query without LLM API key\n{original_query}"
    
    try:
        formatted_schema = ""
        for item in schema_metadata:
            formatted_schema += f"- {item['description']}\n"
        
        logger.info(f"Refining SQL with user feedback: {user_feedback[:100]}...")
        
        prompt_template = PromptTemplate(
            input_variables=["schema", "original_query", "feedback"],
            template="""
You are an expert SQL database engineer. You need to refine an existing SQL query based on user feedback.

The database schema includes the following relevant information:
{schema}

Original SQL query:
{original_query}

User feedback: {feedback}

Generate a revised SQL query that addresses the user's feedback. Only provide the SQL query, nothing else. 
Make sure the query is correct based on the schema information and use proper column and table names.
"""
        )
        
        chain = LLMChain(llm=llm, prompt=prompt_template)
        
        result = chain.run(
            schema=formatted_schema, 
            original_query=original_query, 
            feedback=user_feedback
        )
        
        sql_query = result.strip()
        
        # Handle code block formatting from the LLM
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        elif sql_query.startswith("```"):
            sql_query = sql_query.replace("```", "").strip()
        
        logger.info(f"Refined SQL query: {sql_query[:100]}...")
        return sql_query
    
    except Exception as e:
        logger.error(f"Error refining SQL with LLM: {str(e)}", exc_info=True)
        return f"-- Error refining SQL with LLM: {str(e)}\n{original_query}"
