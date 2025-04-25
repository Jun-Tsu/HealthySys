import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_db():
    """Initialize SQLite database with programs, clients, and enrollments tables."""
    try:
        conn = sqlite3.connect('health_system.db')
        c = conn.cursor()

        # Create programs table
        c.execute('''CREATE TABLE IF NOT EXISTS programs
                     (program_id TEXT PRIMARY KEY,
                      name TEXT NOT NULL,
                      description TEXT)''')

        # Create clients table with indexes for search
        c.execute('''CREATE TABLE IF NOT EXISTS clients
                     (client_id TEXT PRIMARY KEY,
                      first_name TEXT NOT NULL,
                      last_name TEXT NOT NULL,
                      dob TEXT NOT NULL,
                      gender TEXT NOT NULL,
                      contact TEXT NOT NULL,
                      created_at TEXT NOT NULL)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_first_name ON clients(first_name)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_last_name ON clients(last_name)''')

        # Create enrollments table
        c.execute('''CREATE TABLE IF NOT EXISTS enrollments
                     (enrollment_id TEXT PRIMARY KEY,
                      client_id TEXT NOT NULL,
                      program_id TEXT NOT NULL,
                      enrollment_date TEXT NOT NULL,
                      FOREIGN KEY(client_id) REFERENCES clients(client_id),
                      FOREIGN KEY(program_id) REFERENCES programs(program_id))''')

        conn.commit()
        logging.info("Database initialized with programs, clients, and enrollments tables")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()