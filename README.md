# SemanticSQL

SemanticSQL is a FastAPI application that allows users to connect to external databases, extract schema metadata, and use natural language to generate SQL queries. It leverages semantic search and embeddings to understand database schema structure and generate appropriate SQL however or whatever query you want on your personal database(s).

## Features

- **Database Connection Management**: Connect to various database types (PostgreSQL, MySQL, SQL Server, Oracle)
- **Schema Extraction**: Automatically extract and store schema metadata from connected databases
- **AI Query Generation**: Use LLMs to convert natural language to valid SQL
- **Query Execution**: Execute generated SQL against connected databases

## API Endpoints

### 1. Create Database Connection
Connect to an external database.

**Endpoint:** `POST /api/connect`

**Request Body:**
```json
{
    "db_type": "mysql",
    "db_name": "prod",
    "host": "bh-ai-database-identifier.cbkgq2y24ej6.us-east-1.rds.amazonaws.com",
    "port": "3306",
    "database": "bhdatabase",
    "username": "admin",
    "password": "Nopassw0rd#"
}
```

**Response:**
```json
{
    "message": "Database connected successfully",
    "connection_id": "conn_123"
}
```

### 2. List Database Connections
Get all available database connections.

**Endpoint:** `GET /api/connections`

**Response:**
```json
{
    "connections": [
        {
            "connection_id": "conn_123",
            "db_type": "mysql",
            "db_name": "prod",
            "host": "bh-ai-database-identifier.cbkgq2y24ej6.us-east-1.rds.amazonaws.com",
            "port": "3306",
            "database": "bhdatabase"
        }
    ]
}
```

### 3. Generate SQL Query
Convert natural language to SQL using AI.

**Endpoint:** `POST /api/generate-query`

**Request Body:**
```json
{
    "question": "what is my profit grouped by year?"
}
```

**Response:**
```json
{
    "query": "SELECT YEAR(created_at) as year, SUM(profit) as total_profit FROM sales GROUP BY YEAR(created_at) ORDER BY year"
}
```

### 4. Execute SQL Query
Execute a SQL query against the connected database.

**Endpoint:** `POST /api/execute-query`

**Request Body:**
```json
{
    "sql": "select * from products"
}
```

**Response:**
```json
{
    "results": [
        {
            "id": 1,
            "name": "Product A",
            "price": 99.99,
            "stock": 100
        },
        {
            "id": 2,
            "name": "Product B",
            "price": 149.99,
            "stock": 50
        }
    ]
}
```

## Error Handling

All endpoints return appropriate HTTP status codes and error messages:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid input data
- `500 Internal Server Error`: Server-side error

Error responses include a detailed message:
```json
{
    "detail": "Error message describing what went wrong"
}
```

## Development

### Environment Variables

Required environment variables:
```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=semanticsql
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# AI Models
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
MODEL_TEMPERATURE=0.1
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [LangChain](https://langchain.com/)
- [Google Gemini AI](https://ai.google.dev/)
