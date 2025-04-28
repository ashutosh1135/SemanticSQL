# Running SemanticSQL with Docker

This guide explains how to set up and run SemanticSQL using Docker and Docker Compose.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system
- Google Gemini API key (for AI features)

## Setup Instructions

1. **Create a .env file**

   Copy the example environment file to create your own configuration:

   ```bash
   cp env.example .env
   ```

   Edit the `.env` file to add your own Gemini API key and modify any other settings as needed.

2. **Building and starting the application**

   Run the following command to build and start the application:

   ```bash
   docker-compose up -d
   ```

   This will:
   - Build the application using the multi-stage Dockerfile
   - Start a PostgreSQL database with pgvector extension
   - Connect the application to the database
   - Expose the application on port 8000

3. **Accessing the application**

   Once the containers are running, you can access:
   - API: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`

4. **Viewing logs**

   To see the application logs:

   ```bash
   docker-compose logs -f app
   ```

   To see database logs:

   ```bash
   docker-compose logs -f db
   ```

## Development with Docker

The Docker setup includes development-friendly features:

- The `app` directory is mounted as a volume, so changes to code in that directory will be reflected without rebuilding the container
- Debug mode is enabled by default
- PostgreSQL data is persisted in a Docker volume

## Stopping the Application

To stop the application:

```bash
docker-compose down
```

To stop and remove volumes (this will delete all database data):

```bash
docker-compose down -v
```

## Production Deployment

For production deployment, modify the following:

1. Set appropriate environment variables in the `.env` file:
   - `APP_ENV=production`
   - `APP_DEBUG=false`
   - Set a strong `SECRET_KEY`

2. Consider using Docker Swarm or Kubernetes for orchestration
3. Set up proper SSL termination
4. Use a more robust PostgreSQL setup with replication 