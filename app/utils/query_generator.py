from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config.config import settings
from app.utils.llm import chat_model
from app.models.requests import GenerateQueryRequest
import logging

logger = logging.getLogger("semanticsql")

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a SQL expert. Generate valid SQL queries based on the user's request and the available tables in the database.

IMPORTANT: 
1. Only use tables and columns that are listed in the 'Available Tables in Database' section.
2. If the user mentions tables that don't exist in the available tables list, use the closest matching tables instead.
3. Return a raw SQL query without markdown formatting or explanations.
4. If you can't generate a valid query with the available tables, explain that in SQL comments."""),
    ("user", "{input}")
])

# Create chain
chain = prompt | chat_model | StrOutputParser()

def generate_query(question: str, schema_info: str) -> str:
    """Generate SQL query from natural language."""
    try:
        # Check if we have schema info
        if not schema_info or "Available Tables in Database" not in schema_info:
            return "/* No database schema available. Please connect to a database first. */"
        
        # Combine schema info with query
        full_prompt = f"""
Database Tables:
{schema_info}

User Question: {question}

Generate an SQL query that uses ONLY the tables and columns listed above, even if the question mentions other tables.
"""
        
        # Generate query
        response = chain.invoke({"input": full_prompt})
        return response.strip()
        
    except Exception as e:
        logger.error(f"Error generating SQL query: {str(e)}")
        raise 