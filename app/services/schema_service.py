from typing import Dict, Any
from sqlalchemy import inspect, text
from app.services.database_service import DatabaseService
import logging
from pathlib import Path
import asyncio

logger = logging.getLogger("semanticsql")

class SchemaService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    async def explore_schema(self, connection_id: str) -> None:
        """Asynchronously explore database schema and write to context file."""
        try:
            if connection_id not in self.db_service.engines:
                raise Exception(f"No active database connection for {connection_id}")

            engine = self.db_service.engines[connection_id]
            connection_info = self.db_service.connections[connection_id]
            db_type = connection_info["db_type"].lower()

            # Start schema exploration in background
            asyncio.create_task(self._explore_schema_background(engine, connection_id, db_type))
            
        except Exception as e:
            logger.error(f"Error starting schema exploration: {str(e)}")

    async def _explore_schema_background(self, engine, connection_id: str, db_type: str) -> None:
        """Background task to explore schema and write to context file."""
        try:
            inspector = inspect(engine)
            markdown_content = f"# Database Schema for {connection_id}\n\n"
            
            # Get tables and their columns
            markdown_content += "## Tables\n\n"
            for table_name in inspector.get_table_names():
                markdown_content += f"### {table_name}\n\n"
                
                # Get columns
                columns = inspector.get_columns(table_name)
                markdown_content += "Columns:\n"
                for col in columns:
                    markdown_content += f"- {col['name']} ({str(col['type'])})\n"
                markdown_content += "\n"

            # Get additional schema info based on database type
            if db_type == "mysql":
                await self._get_mysql_schema(engine, markdown_content)
            elif db_type == "postgres":
                await self._get_postgres_schema(engine, markdown_content)

            # Write to context file
            self._write_to_context(connection_id, markdown_content)
            
        except Exception as e:
            logger.error(f"Error in background schema exploration: {str(e)}")

    async def _get_mysql_schema(self, engine, markdown_content: str) -> str:
        """Get MySQL specific schema information."""
        try:
            with engine.connect() as conn:
                # Get views
                result = conn.execute(text("SHOW FULL TABLES WHERE Table_type = 'VIEW'"))
                views = [row[0] for row in result]
                if views:
                    markdown_content += "## Views\n\n"
                    for view in views:
                        markdown_content += f"### {view}\n"
                        result = conn.execute(text(f"SHOW CREATE VIEW {view}"))
                        for row in result:
                            markdown_content += f"```sql\n{row[1]}\n```\n\n"

                # Get procedures
                result = conn.execute(text("SHOW PROCEDURE STATUS WHERE Db = DATABASE()"))
                procedures = [(row[1], row[2]) for row in result]
                if procedures:
                    markdown_content += "## Procedures\n\n"
                    for proc_name, proc_type in procedures:
                        markdown_content += f"### {proc_name}\n"
                        result = conn.execute(text(f"SHOW CREATE PROCEDURE {proc_name}"))
                        for row in result:
                            markdown_content += f"```sql\n{row[2]}\n```\n\n"

        except Exception as e:
            logger.error(f"Error getting MySQL schema: {str(e)}")
        return markdown_content

    async def _get_postgres_schema(self, engine, markdown_content: str) -> str:
        """Get PostgreSQL specific schema information."""
        try:
            with engine.connect() as conn:
                # Get views
                result = conn.execute(text("""
                    SELECT table_name, view_definition 
                    FROM information_schema.views 
                    WHERE table_schema = 'public'
                """))
                views = result.fetchall()
                if views:
                    markdown_content += "## Views\n\n"
                    for view_name, definition in views:
                        markdown_content += f"### {view_name}\n"
                        markdown_content += f"```sql\n{definition}\n```\n\n"

                # Get functions
                result = conn.execute(text("""
                    SELECT proname, prosrc 
                    FROM pg_proc 
                    WHERE pronamespace = 'public'::regnamespace
                """))
                functions = result.fetchall()
                if functions:
                    markdown_content += "## Functions\n\n"
                    for func_name, definition in functions:
                        markdown_content += f"### {func_name}\n"
                        markdown_content += f"```sql\n{definition}\n```\n\n"

        except Exception as e:
            logger.error(f"Error getting PostgreSQL schema: {str(e)}")
        return markdown_content

    def _write_to_context(self, connection_id: str, content: str) -> None:
        """Write schema information to context file."""
        try:
            # Create resources directory if it doesn't exist
            Path("resources").mkdir(exist_ok=True)
            
            # Append to context file
            with open("resources/context.txt", "a", encoding="utf-8") as f:
                f.write(f"\n{content}\n")
            
            logger.info(f"Updated context file with schema information for {connection_id}")
            
        except Exception as e:
            logger.error(f"Error writing to context file: {str(e)}") 