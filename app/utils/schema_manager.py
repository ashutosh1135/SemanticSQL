from typing import Dict, Any
from sqlalchemy import MetaData, inspect
import json
import logging
from pathlib import Path

logger = logging.getLogger("semanticsql")

def extract_schema_info(engine) -> Dict[str, Any]:
    """Extract database schema information."""
    try:
        inspector = inspect(engine)
        schema_info = {
            "tables": {},
            "views": {},
            "procedures": {}
        }

        # Get all tables
        for table_name in inspector.get_table_names():
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({
                    "name": column.name,
                    "type": str(column.type),
                    "nullable": column.nullable,
                    "default": str(column.default) if column.default else None
                })
            
            # Get primary keys
            pk_constraint = inspector.get_pk_constraint(table_name)
            primary_keys = pk_constraint.get("constrained_columns", [])
            
            # Get foreign keys
            foreign_keys = []
            for fk in inspector.get_foreign_keys(table_name):
                foreign_keys.append({
                    "name": fk.get("name", ""),
                    "referred_table": fk.get("referred_table", ""),
                    "referred_columns": fk.get("referred_columns", []),
                    "constrained_columns": fk.get("constrained_columns", [])
                })

            schema_info["tables"][table_name] = {
                "columns": columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys
            }

        # Get all views
        for view_name in inspector.get_view_names():
            view_definition = inspector.get_view_definition(view_name)
            schema_info["views"][view_name] = {
                "definition": str(view_definition) if view_definition else None
            }

        # Get all procedures
        for proc_name in inspector.get_procedure_names():
            proc_definition = inspector.get_procedure_definition(proc_name)
            schema_info["procedures"][proc_name] = {
                "definition": str(proc_definition) if proc_definition else None
            }

        return schema_info

    except Exception as e:
        logger.error(f"Error extracting schema information: {str(e)}")
        raise

def update_context_file(connection_id: str, schema_info: Dict[str, Any], context_path: str = "resources/context.txt"):
    """Update the context file with new schema information."""
    try:
        # Create resources directory if it doesn't exist
        Path("resources").mkdir(exist_ok=True)
        
        # Read existing context if it exists
        existing_context = {}
        if Path(context_path).exists():
            with open(context_path, "r") as f:
                existing_context = json.loads(f.read() or "{}")

        # Update with new schema information
        existing_context[connection_id] = schema_info

        # Write back to file
        with open(context_path, "w") as f:
            json.dump(existing_context, f, indent=2)

        logger.info(f"Updated context file with schema information for connection {connection_id}")

    except Exception as e:
        logger.error(f"Error updating context file: {str(e)}")
        raise 