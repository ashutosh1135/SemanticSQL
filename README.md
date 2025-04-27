# SemanticSQL

SemanticSQL is a FastAPI application that allows users to connect to external databases, extract schema metadata, and use natural language to generate SQL queries. It leverages semantic search and embeddings to understand database schema structure and generate appropriate SQL however or whatever query you want on your personal database(s).

## Overview

SemanticSQL is a FastAPI application that allows users to connect to external databases, extract schema metadata, and use natural language to generate SQL queries. It leverages semantic search with vector embeddings to understand database schema structures and uses Google's Gemini AI model to generate appropriate SQL queries.

## Features

- **Database Connection Management**: Connect to various database types (PostgreSQL, MySQL, SQL Server, Oracle)
- **Schema Extraction**: Automatically extract and store schema metadata from connected databases
- **Semantic Search**: Find relevant tables and columns based on natural language queries
- **AI Query Generation**: Use LLMs to convert natural language to valid SQL
- **Query Execution**: Execute generated SQL against connected databases

## Architecture

The application is built with the following key components:

1. **FastAPI Backend**: Provides RESTful API endpoints for managing database connections and queries
2. **SQLAlchemy ORM**: Handles database operations with connection pooling for performance
3. **Vector Embeddings**: Uses sentence-transformers to generate embeddings for semantic search
4. **LLM Integration**: Integrates with Google's Gemini models for SQL generation
5. **Logging and Monitoring**: Comprehensive logging for monitoring and debugging

## Project Structure

```
semanticsql/
├── app/
│   ├── api/                # API routes
│   ├── config/             # Configuration settings
│   ├── db/                 # Database connection code
│   ├── models/             # Data models
│   ├── services/           # Business logic
│   └── utils/              # Utility functions
├── main.py                 # Application entry point
├── env.example             # Example environment variables
└── README.md               # This file
```

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Google Gemini API key (for AI features)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/semanticsql.git
   cd semanticsql
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. Start the application:
   ```bash
   uvicorn main:app --reload
   ```

6. Access the API at http://localhost:8000 and the interactive docs at http://localhost:8000/docs

## API Endpoints

### Connection Management

- `POST /api/v1/connections/`: Create a new database connection
- `GET /api/v1/connections/`: List all database connections
- `GET /api/v1/connections/{connection_id}`: Get connection details
- `DELETE /api/v1/connections/{connection_id}`: Delete a connection

### Query Operations

- `POST /api/v1/queries/generate`: Generate SQL from natural language
- `POST /api/v1/queries/execute`: Execute SQL against a database

## Usage Examples

### Connecting to a Database

```bash
curl -X POST "http://localhost:8000/api/v1/connections/" \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgres",
    "host": "localhost",
    "port": "5432",
    "database": "mydatabase",
    "username": "user",
    "password": "password"
  }'
```

### Generating SQL from Natural Language

```bash
curl -X POST "http://localhost:8000/api/v1/queries/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find all customers who made purchases last month",
    "connection_id": "YOUR_CONNECTION_ID"
  }'
```

## Development

### Running Tests

```bash
pytest
```

### Environment Variables

See `env.example` for all available configuration options.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Sentence Transformers](https://www.sbert.net/)
- [LangChain](https://langchain.com/)
- [Google Gemini AI](https://ai.google.dev/)
