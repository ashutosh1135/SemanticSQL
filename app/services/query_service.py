from typing import Dict, Any, List
from app.services.database_service import DatabaseService
from app.models.requests import GenerateQueryRequest
import logging
from pathlib import Path
from sqlalchemy import inspect
# Try to import generate_query, but provide a fallback if it's not working
try:
    from app.utils.query_generator import generate_query
    HAS_QUERY_GENERATOR = True
except Exception as e:
    import re
    HAS_QUERY_GENERATOR = False
    logging.error(f"Failed to import query_generator: {str(e)}")

logger = logging.getLogger("semanticsql")

class QueryService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    async def generate_sql_query(self, question: str) -> str:
        """Generate SQL query from natural language question."""
        try:
            # Get actual database tables if a connection is available
            actual_tables_info = ""
            try:
                connections = await self.db_service.list_connections()
                if connections:
                    connection = connections[0]
                    connection_id = connection.connection_id
                    
                    if connection_id in self.db_service.engines:
                        engine = self.db_service.engines[connection_id]
                        actual_tables = inspect(engine).get_table_names()
                        
                        # Create a simple schema from actual tables
                        actual_tables_info = "## Available Tables in Database\n"
                        for table in actual_tables:
                            actual_tables_info += f"- {table}\n"
                            
                            # Add column info for each table
                            columns = inspect(engine).get_columns(table)
                            actual_tables_info += "  Columns:\n"
                            for col in columns:
                                actual_tables_info += f"  - {col['name']} ({str(col['type'])})\n"
                            
                        logger.info(f"Providing {len(actual_tables)} actual tables to LLM")
            except Exception as e:
                logger.warning(f"Could not get database tables: {str(e)}")
            
            # Generate SQL query using the actual tables information
            if HAS_QUERY_GENERATOR:
                logger.info("Using LLM to generate SQL query")
                return generate_query(question, actual_tables_info)
            else:
                logger.warning("LLM not available, using fallback generator")
                return self._simple_query_generator(question, actual_tables_info)
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {str(e)}")
            raise Exception(f"Error generating SQL query: {str(e)}")

    def _simple_query_generator(self, question: str, schema_info: str) -> str:
        """Simple rule-based query generator for fallback."""
        # Extract table names from schema
        tables = []
        for line in schema_info.split("\n"):
            if line.startswith("- "):
                tables.append(line[2:].strip())
        
        if not tables:
            return "SELECT 1 /* No tables found in database */"
        
        # Default to first table if no tables mentioned
        target_table = tables[0]
        
        # Check if any table names are mentioned in the question
        for table in tables:
            if table.lower() in question.lower():
                target_table = table
                break
        
        # Simple query based on common question patterns
        if any(word in question.lower() for word in ["count", "how many"]):
            return f"SELECT COUNT(*) FROM {target_table}"
        else:
            return f"SELECT * FROM {target_table} LIMIT 10"

    async def execute_query(self, connection_id: str, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query on the specified database."""
        try:
            if connection_id not in self.db_service.engines:
                raise Exception(f"No active database connection for {connection_id}")
            
            return await self.db_service.execute_query(connection_id, query)
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            raise 