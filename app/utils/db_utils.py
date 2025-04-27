from sqlalchemy import create_engine, inspect
from typing import List, Dict
from sqlmodel import Session
import urllib.parse

async def create_connection_string(db_type: str, username: str, password: str, host: str, port: int, database: str) -> str:
    """Create SQLAlchemy connection string based on DB type."""
    password = urllib.parse.quote_plus(password)  # encode special characters
    if db_type == "postgres":
        return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
    elif db_type == "mysql":
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    elif db_type == "sqlserver":
        return f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
    elif db_type == "oracle":
        return f"oracle+cx_oracle://{username}:{password}@{host}:{port}/{database}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

async def get_schema_metadata(connection_string: str) -> List[Dict]:
    """Connect to DB and extract table/column metadata."""
    engine = await create_engine(connection_string)
    inspector = inspect(engine)

    schema_info = []
    schemas = inspector.get_schema_names()

    for schema in schemas:
        tables = inspector.get_table_names(schema=schema)
        for table in tables:
            columns = inspector.get_columns(table_name=table, schema=schema)
            for column in columns:
                schema_info.append({
                    "schema_name": schema,
                    "table_name": table,
                    "column_name": column["name"],
                    "data_type": str(column.get("type")),
                    "is_primary_key": column.get("primary_key", False),
                    "is_foreign_key": False,  # set later if needed
                    "foreign_table": None,
                    "foreign_column": None
                })
    return schema_info
