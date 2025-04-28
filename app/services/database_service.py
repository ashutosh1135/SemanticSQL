from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text, inspect
from app.models.requests import DatabaseConnectionRequest
from app.models.responses import DatabaseConnection
import logging
import os
from pathlib import Path

logger = logging.getLogger("semanticsql")

class DatabaseService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not DatabaseService._initialized:
            self.connections: Dict[str, Any] = {}
            self.engines: Dict[str, Any] = {}
            self._load_persistent_connections()
            DatabaseService._initialized = True

    async def connect(self, request: DatabaseConnectionRequest) -> Dict[str, str]:
        """Connect to a database."""
        try:
            # Create connection string based on database type
            if request.db_type.lower() == "mysql":
                connection_string = f"mysql+pymysql://{request.username}:{request.password}@{request.host}:{request.port}/{request.database}"
            elif request.db_type.lower() == "postgres":
                connection_string = f"postgresql://{request.username}:{request.password}@{request.host}:{request.port}/{request.database}"
            else:
                raise ValueError(f"Unsupported database type: {request.db_type}")
            
            # Create engine with proper settings for result handling
            engine = create_engine(
                connection_string,
                future=True,  # Use SQLAlchemy 2.0 style
                # Set other SQLAlchemy options as needed
                pool_size=5,
                max_overflow=10
            )
            
            # Test connection
            with engine.connect() as conn:
                # Execute a simple query to test the connection
                conn.execute(text("SELECT 1"))
                logger.info(f"Connection test successful for {request.db_type}_{request.database}")
            
            # Store connection
            connection_id = f"{request.db_type}_{request.database}"
            self.connections[connection_id] = {
                "connection_id": connection_id,
                "db_type": request.db_type,
                "db_name": request.db_name,
                "host": request.host,
                "port": request.port,
                "database": request.database,
                "username": request.username
            }
            self.engines[connection_id] = engine
            
            # Save connections to a persistent file
            self._save_persistent_connections()
            
            return {"connection_id": connection_id}
            
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise

    async def list_connections(self) -> List[DatabaseConnection]:
        """List all database connections."""
        try:
            if not self.connections:
                logger.warning("No active database connections found")
                return []
                
            logger.info(f"Returning {len(self.connections)} active connections")
            return [
                DatabaseConnection(**connection)
                for connection in self.connections.values()
            ]
        except Exception as e:
            logger.error(f"Error listing connections: {str(e)}")
            raise

    async def execute_query(self, connection_id: str, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query."""
        try:
            if connection_id not in self.engines:
                logger.error(f"No active database connection for {connection_id}")
                raise Exception(f"No active database connection for {connection_id}")
            
            logger.info(f"Executing query on connection {connection_id}: {sql}")    
            engine = self.engines[connection_id]
            
            try:
                with engine.connect() as connection:
                    result = connection.execute(text(sql))
                    
                    # Fix: Properly convert result rows to dictionaries
                    columns = result.keys()
                    logger.debug(f"Query result columns: {columns}")
                    
                    result_rows = []
                    for row in result:
                        # Convert row to a dictionary of column name: value pairs
                        try:
                            # First try the mapping accessor
                            row_dict = {col: row[col] for col in columns}
                        except Exception as mapping_err:
                            try:
                                # Fall back to index-based access
                                row_dict = {columns[i]: row[i] for i in range(len(columns))}
                            except Exception as idx_err:
                                logger.error(f"Error converting row to dict (index-based): {str(idx_err)}")
                                # Last resort - convert row to a string representation
                                row_dict = {"row_data": str(row)}
                                
                        result_rows.append(row_dict)
                    
                    logger.info(f"Query executed successfully, returned {len(result_rows)} rows")
                    return result_rows
                    
            except Exception as query_err:
                # Log the specific query error
                logger.error(f"SQL execution error: {str(query_err)}")
                # Check if it's a table not found error
                error_msg = str(query_err).lower()
                if "table" in error_msg and ("not exist" in error_msg or "doesn't exist" in error_msg):
                    # Get tables that do exist
                    inspector = inspect(engine)
                    available_tables = inspector.get_table_names()
                    logger.info(f"Available tables: {available_tables}")
                    raise Exception(f"{str(query_err)}. Available tables: {', '.join(available_tables)}")
                else:
                    raise
                
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
    
    def _save_persistent_connections(self) -> None:
        """Save connections to a persistent file (without passwords)."""
        try:
            # Create resources directory if it doesn't exist
            Path("resources").mkdir(exist_ok=True)
            
            # Save connections without sensitive info
            connections_data = {}
            for conn_id, conn_info in self.connections.items():
                # Create a copy without password
                conn_data = conn_info.copy()
                conn_data.pop("password", None)  # Remove password if present
                connections_data[conn_id] = conn_data
            
            import json
            with open("resources/connections.json", "w") as f:
                json.dump(connections_data, f, indent=2)
                
            logger.info(f"Saved {len(connections_data)} connections to persistent storage")
        except Exception as e:
            logger.error(f"Failed to save connections: {str(e)}")
    
    def _load_persistent_connections(self) -> None:
        """Load connections from persistent file."""
        try:
            connections_file = Path("resources/connections.json")
            if not connections_file.exists():
                logger.info("No persistent connections file found")
                return
                
            import json
            with open(connections_file, "r") as f:
                connections_data = json.load(f)
            
            logger.info(f"Found {len(connections_data)} connections in persistent storage")
            
            # Add connections to the service (engines won't be loaded)
            for conn_id, conn_info in connections_data.items():
                self.connections[conn_id] = conn_info
                
                try:
                    # Try to recreate engine if connection details are available
                    if all(k in conn_info for k in ["db_type", "host", "port", "database", "username"]):
                        # We don't have password in storage, so log this fact
                        logger.warning(f"Can't automatically reconnect to {conn_id} - password needed")
                except Exception as e:
                    logger.error(f"Error recreating engine for {conn_id}: {str(e)}")
                
            logger.info(f"Loaded {len(connections_data)} connections from persistent storage")
            logger.warning("Note: Connection engines not loaded - reconnect required")
        except Exception as e:
            logger.error(f"Failed to load connections: {str(e)}") 