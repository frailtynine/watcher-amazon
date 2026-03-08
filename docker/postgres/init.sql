-- Create test database if it doesn't already exist
SELECT 'CREATE DATABASE newswatcher_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'newswatcher_test')\gexec
