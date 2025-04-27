from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.schema_models import TableSchema
from app.services.db_connector import extract_database_schema
from app.models.connection_models import DatabaseConnection
from app.utils.text_formatter import format_schema_text

async def extract_schema_metadata(connection: DatabaseConnection) -> List[Dict[str, Any]]:
    """
    Extracts tables and columns information from the connected database.
    
    Args:
        connection: DatabaseConnection model object
        
    Returns:
        List of dictionaries containing schema metadata
    """
    return await extract_database_schema(connection)

async def save_schema_metadata(
    db_session: Session, 
    db_id: uuid.UUID, 
    metadata: List[Dict[str, Any]]
) -> List[TableSchema]:
    """
    Saves extracted schema metadata to the database.
    
    Args:
        db_session: Database session
        db_id: UUID of the database connection
        metadata: List of schema metadata dictionaries
        
    Returns:
        List of saved TableSchema objects
    """
    schema_records = []
    
    for item in metadata:
        schema_record = TableSchema(
            db_id=db_id,
            schema_name=item["schema_name"],
            table_name=item["table_name"],
            column_name=item["column_name"],
            is_primary_key=item.get("is_primary_key", False),
            is_foreign_key=item.get("is_foreign_key", False),
            foreign_table=item.get("foreign_table"),
            foreign_column=item.get("foreign_column"),
            description=f"Column {item['column_name']} of type {item['data_type']} in table {item['table_name']}",
            created_at=datetime.now().isoformat()
        )
        
        db_session.add(schema_record)
        schema_records.append(schema_record)
    
    db_session.commit()
    
    for record in schema_records:
        db_session.refresh(record)
    
    return schema_records

async def format_metadata(metadata: List[Dict[str, Any]]) -> str:
    """
    Formats the extracted metadata into readable text for embedding.
    
    Args:
        metadata: List of schema metadata dictionaries
        
    Returns:
        Formatted text representation of schema
    """
    return await format_schema_text(metadata)

async def generate_embedding_texts(metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepares metadata in a format suitable for embedding.
    
    Args:
        metadata: List of schema metadata dictionaries
        
    Returns:
        List of dicts with schema_name, table_name, column_name and description
    """
    embedding_texts = []
    
    # Group by table for table-level embeddings
    tables = {}
    for item in metadata:
        table_key = f"{item['schema_name']}.{item['table_name']}"
        if table_key not in tables:
            tables[table_key] = {
                "schema_name": item["schema_name"],
                "table_name": item["table_name"],
                "columns": []
            }
        
        tables[table_key]["columns"].append(item)
    
    # Create embedding texts for tables
    for table_key, table_info in tables.items():
        # Table-level description
        columns_text = ", ".join([col["column_name"] for col in table_info["columns"]])
        table_description = f"Table {table_info['table_name']} in schema {table_info['schema_name']} with columns: {columns_text}"
        
        embedding_texts.append({
            "schema_name": table_info["schema_name"],
            "table_name": table_info["table_name"],
            "column_name": None,  # No specific column
            "description": table_description
        })
        
        # Column-level descriptions
        for column in table_info["columns"]:
            column_description = f"Column {column['column_name']} of type {column['data_type']} in table {column['table_name']}"
            if column.get("is_primary_key"):
                column_description += " (Primary Key)"
            if column.get("is_foreign_key"):
                column_description += f" (Foreign Key to {column.get('foreign_table')}.{column.get('foreign_column')})"
                
            embedding_texts.append({
                "schema_name": column["schema_name"],
                "table_name": column["table_name"],
                "column_name": column["column_name"],
                "description": column_description
            })
    
    return embedding_texts
