-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database user and permissions
-- (These may already exist, so we use IF NOT EXISTS where possible)

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE migration_db TO migration_user;

-- Create schemas if they don't exist
CREATE SCHEMA IF NOT EXISTS migration_assistant;
GRANT ALL ON SCHEMA migration_assistant TO migration_user;

-- Set search path
ALTER USER migration_user SET search_path TO migration_assistant, public;