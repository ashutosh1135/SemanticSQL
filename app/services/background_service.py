import asyncio
from typing import Dict, Any
from sqlalchemy import inspect, text
from app.services.database_service import DatabaseService
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("semanticsql")

class BackgroundService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    async def start_schema_exploration(self, connection_id: str) -> None:
        """Start schema exploration in background."""
        try:
            if connection_id not in self.db_service.engines:
                logger.error(f"No active database connection for {connection_id}")
                return

            # Start background task
            asyncio.create_task(self._explore_schema(connection_id))
            
        except Exception as e:
            logger.error(f"Error starting schema exploration: {str(e)}")

    async def _explore_schema(self, connection_id: str) -> None:
        """Background task to explore schema and write to context file."""
        try:
            engine = self.db_service.engines[connection_id]
            connection_info = self.db_service.connections[connection_id]
            db_type = connection_info["db_type"].lower()

            # Get basic schema info
            inspector = inspect(engine)
            markdown_content = f"# Database Schema for {connection_id}\n\n"
            
            # Get tables
            tables = inspector.get_table_names()
            if not tables:
                logger.warning(f"No tables found in database {connection_id}")
                markdown_content += "No tables found in the database.\n"
            else:
                logger.info(f"Found {len(tables)} tables in database {connection_id}")
                markdown_content += f"## Tables ({len(tables)})\n\n"
                for table_name in tables:
                    markdown_content += f"### {table_name}\n\n"
                    columns = inspector.get_columns(table_name)
                    markdown_content += "Columns:\n"
                    for col in columns:
                        markdown_content += f"- {col['name']} ({str(col['type'])})\n"
                    
                    # Get primary keys
                    try:
                        pk = inspector.get_pk_constraint(table_name)
                        if pk and pk.get('constrained_columns'):
                            markdown_content += "\nPrimary Key: " + ", ".join(pk['constrained_columns']) + "\n"
                    except Exception as e:
                        logger.warning(f"Error getting primary key for {table_name}: {str(e)}")
                    
                    # Get foreign keys
                    try:
                        fks = inspector.get_foreign_keys(table_name)
                        if fks:
                            markdown_content += "\nForeign Keys:\n"
                            for fk in fks:
                                markdown_content += f"- {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}\n"
                    except Exception as e:
                        logger.warning(f"Error getting foreign keys for {table_name}: {str(e)}")
                    
                    markdown_content += "\n"

            # Get additional info based on database type
            if db_type == "mysql":
                markdown_content = await self._get_mysql_schema(engine, markdown_content)
            elif db_type == "postgres":
                markdown_content = await self._get_postgres_schema(engine, markdown_content)

            # Write to context file
            self._write_to_context(connection_id, markdown_content)
            
            # Start embedding process
            await self._start_embedding(connection_id)
            
        except Exception as e:
            logger.error(f"Error in schema exploration: {str(e)}")

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

        except Exception as e:
            logger.error(f"Error getting PostgreSQL schema: {str(e)}")
        return markdown_content

    def _write_to_context(self, connection_id: str, content: str) -> None:
        """Write schema information to context file."""
        try:
            # Create resources directory if it doesn't exist
            Path("resources").mkdir(exist_ok=True)
            
            # Clear existing content first
            with open("resources/context.txt", "w", encoding="utf-8") as f:
                f.write(f"# Schema for {connection_id}\n\n{content}\n")
            
            logger.info(f"Updated context file for {connection_id}")
            
            # Also write to a timestamped backup file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"resources/schema_{connection_id}_{timestamp}.md"
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Created schema backup at {backup_path}")
            
        except Exception as e:
            logger.error(f"Error writing to context file: {str(e)}")

    async def _start_embedding(self, connection_id: str) -> None:
        """Start embedding process for the schema."""
        try:
            # TODO: Implement embedding logic here
            logger.info(f"Starting embedding process for {connection_id}")
        except Exception as e:
            logger.error(f"Error in embedding process: {str(e)}") 