from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

logger = logging.getLogger("semanticsql")

async def extract_schema(session: AsyncSession) -> dict:
    """Extract database schema and metadata."""
    try:
        inspector = inspect(session.get_bind())
        
        # Get all schemas
        schemas = await session.execute(text("SELECT schema_name FROM information_schema.schemata"))
        schema_list = [row[0] for row in schemas]
        
        schema_info = {}
        for schema in schema_list:
            if schema in ['pg_catalog', 'information_schema']:
                continue
                
            tables = await session.execute(text(f"""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = '{schema}'
            """))
            
            schema_info[schema] = {}
            for table in tables:
                table_name = table[0]
                table_type = table[1]
                
                # Get columns
                columns = await session.execute(text(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = '{schema}' AND table_name = '{table_name}'
                """))
                
                # Get foreign keys
                fks = await session.execute(text(f"""
                    SELECT
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = '{schema}'
                    AND tc.table_name = '{table_name}'
                """))
                
                schema_info[schema][table_name] = {
                    "type": table_type,
                    "columns": [
                        {
                            "name": col[0],
                            "type": col[1],
                            "nullable": col[2] == 'YES'
                        } for col in columns
                    ],
                    "foreign_keys": [
                        {
                            "constraint": fk[0],
                            "column": fk[1],
                            "references": {
                                "table": fk[2],
                                "column": fk[3]
                            }
                        } for fk in fks
                    ]
                }
        
        return schema_info
        
    except Exception as e:
        logger.error(f"Error extracting schema: {e}")
        raise

async def save_schema_to_file(schema_info: dict, file_path: str):
    """Save schema information to a file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(schema_info, f, indent=2)
        logger.info(f"Schema information saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving schema to file: {e}")
        raise 