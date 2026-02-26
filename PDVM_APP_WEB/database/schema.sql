-- PDVM Database Schema
-- PostgreSQL 18

-- Create database (run this separately in pgAdmin)
-- CREATE DATABASE pdvm_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create index on username and email
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- PDVM Entries table
CREATE TABLE IF NOT EXISTS pdvm_entries (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    category VARCHAR(100),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_pdvm_entries_user_id ON pdvm_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_pdvm_entries_status ON pdvm_entries(status);
CREATE INDEX IF NOT EXISTS idx_pdvm_entries_category ON pdvm_entries(category);

-- Audit Log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(100),
    record_id INTEGER,
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on user_id and created_at
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Create a trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to pdvm_entries table
DROP TRIGGER IF EXISTS update_pdvm_entries_updated_at ON pdvm_entries;
CREATE TRIGGER update_pdvm_entries_updated_at
    BEFORE UPDATE ON pdvm_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert a default admin user (password: admin123)
-- Hashed with bcrypt
INSERT INTO users (username, email, hashed_password, full_name, is_superuser)
VALUES (
    'admin',
    'admin@pdvm.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lM7QjL7R5W2q',
    'Administrator',
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- Sample data
INSERT INTO pdvm_entries (title, description, status, category, user_id)
SELECT 
    'Sample Entry ' || i,
    'This is a sample entry for testing purposes',
    CASE WHEN i % 3 = 0 THEN 'completed' 
         WHEN i % 3 = 1 THEN 'active' 
         ELSE 'pending' END,
    CASE WHEN i % 2 = 0 THEN 'Category A' ELSE 'Category B' END,
    (SELECT id FROM users WHERE username = 'admin')
FROM generate_series(1, 10) AS i
WHERE EXISTS (SELECT 1 FROM users WHERE username = 'admin');
