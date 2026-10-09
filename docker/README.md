# MediLens AI - Docker Deployment Instructions

## Running the Complete Stack

To build and start all containers (PostgreSQL, FastAPI Backend, and React Frontend):

```bash
# From the project root:
docker compose up --build

# Or from this directory:
docker compose -f docker-compose.yml up --build
```

## Services Included
- **Database (`medilens_postgres`)**: PostgreSQL 16 Alpine on port `5432` with automatic DDL execution from `database/schema.sql`.
- **Backend API (`medilens_backend`)**: FastAPI server on port `8000` with hot-reload enabled.
- **Frontend App (`medilens_frontend`)**: Vite dev server on port `5173`.
