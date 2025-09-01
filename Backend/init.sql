-- GramOthi Database Initialization Script
-- This script creates the initial database structure

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance
-- These will be created automatically by SQLAlchemy, but you can add custom ones here

-- Grant permissions (adjust as needed for your setup)
GRANT ALL PRIVILEGES ON DATABASE gramothi TO gramothi_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO gramothi_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gramothi_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO gramothi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO gramothi_user;
