#!/bin/bash
# PostgreSQL initialization script
# This runs automatically when the container first starts

set -e

echo "Initializing PostgreSQL database..."

# Create extensions if needed
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create useful extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;

    -- Log initialization
    SELECT 'Database initialized successfully' as status;
EOSQL

echo "✓ PostgreSQL initialization complete"
