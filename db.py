import sqlite3
import logging
from databases import Database
from uuid import uuid4
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global database instance
database = Database('sqlite:///health_system.db')

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
        logging.info("Database available")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()

async def connect_db():
    """Connect to the database."""
    try:
        await database.connect()
        logging.info("Database connected")
        logging.info("Database available for async queries")
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise

async def disconnect_db():
    """Disconnect from the database."""
    try:
        await database.disconnect()
        logging.info("Database disconnected")
    except Exception as e:
        logging.error(f"Database disconnection failed: {e}")
        raise

async def check_db_status():
    """Check if database is available and tables exist."""
    try:
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('programs', 'clients', 'enrollments')"
        tables = await database.fetch_all(query)
        table_names = [table['name'] for table in tables]
        return {
            "status": "available",
            "tables": table_names,
            "message": "Database is initialized and connected"
        }
    except Exception as e:
        logging.error(f"Database status check failed: {e}")
        return {
            "status": "unavailable",
            "tables": [],
            "message": f"Database error: {str(e)}"
        }

async def create_program(name: str, description: str | None) -> str:
    """Create a new program in the database and return its ID."""
    try:
        program_id = str(uuid4())
        query = """
            INSERT INTO programs (program_id, name, description)
            VALUES (:program_id, :name, :description)
        """
        values = {"program_id": program_id, "name": name, "description": description}
        await database.execute(query, values)
        logging.info(f"Program created: {program_id}")
        return program_id
    except Exception as e:
        logging.error(f"Failed to create program: {e}")
        raise

async def create_client(first_name: str, last_name: str, dob: str, gender: str, contact: str) -> str:
    """Create a new client in the database and return its ID."""
    try:
        # Check for existing client with same details
        query_check = """
            SELECT client_id FROM clients
            WHERE first_name = :first_name
            AND last_name = :last_name
            AND dob = :dob
            AND gender = :gender
            AND contact = :contact
        """
        values_check = {
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "gender": gender,
            "contact": contact
        }
        existing_client = await database.fetch_one(query_check, values_check)
        if existing_client:
            raise ValueError(f"Client already exists with ID: {existing_client['client_id']}")

        client_id = str(uuid4())
        created_at = datetime.utcnow().isoformat()
        query = """
            INSERT INTO clients (client_id, first_name, last_name, dob, gender, contact, created_at)
            VALUES (:client_id, :first_name, :last_name, :dob, :gender, :contact, :created_at)
        """
        values = {
            "client_id": client_id,
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "gender": gender,
            "contact": contact,
            "created_at": created_at
        }
        await database.execute(query, values)
        logging.info(f"Client created: {client_id}")
        return client_id
    except ValueError as e:
        logging.error(f"Client creation failed: {e}")
        raise
    except Exception as e:
        logging.error(f"Failed to create client: {e}")
        raise

async def check_client_exists(client_id: str) -> bool:
    """Check if a client exists in the database."""
    try:
        query = "SELECT 1 FROM clients WHERE client_id = :client_id"
        result = await database.fetch_one(query, {"client_id": client_id})
        return bool(result)
    except Exception as e:
        logging.error(f"Failed to check client existence: {e}")
        raise

async def check_program_exists(program_id: str) -> bool:
    """Check if a program exists in the database."""
    try:
        query = "SELECT 1 FROM programs WHERE program_id = :program_id"
        result = await database.fetch_one(query, {"program_id": program_id})
        return bool(result)
    except Exception as e:
        logging.error(f"Failed to check program existence: {e}")
        raise

async def create_enrollment(client_id: str, program_id: str) -> str:
    """Create a new enrollment in the database and return its ID."""
    try:
        # Validate client and program existence
        if not await check_client_exists(client_id):
            raise ValueError("Client does not exist")
        if not await check_program_exists(program_id):
            raise ValueError("Program does not exist")

        enrollment_id = str(uuid4())
        enrollment_date = datetime.utcnow().isoformat()
        query = """
            INSERT INTO enrollments (enrollment_id, client_id, program_id, enrollment_date)
            VALUES (:enrollment_id, :client_id, :program_id, :enrollment_date)
        """
        values = {
            "enrollment_id": enrollment_id,
            "client_id": client_id,
            "program_id": program_id,
            "enrollment_date": enrollment_date
        }
        await database.execute(query, values)
        logging.info(f"Enrollment created: {enrollment_id}")
        return enrollment_id
    except Exception as e:
        logging.error(f"Failed to create enrollment: {e}")
        raise

async def search_clients(search_term: str) -> list[dict]:
    """Search clients by first or last name."""
    try:
        search_term = f"%{search_term}%"
        query = """
            SELECT client_id, first_name, last_name, dob, gender, contact, created_at
            FROM clients
            WHERE first_name LIKE :search_term OR last_name LIKE :search_term
        """
        results = await database.fetch_all(query, {"search_term": search_term})
        return [
            {
                "client_id": result["client_id"],
                "first_name": result["first_name"],
                "last_name": result["last_name"],
                "dob": result["dob"],
                "gender": result["gender"],
                "contact": result["contact"],
                "created_at": result["created_at"]
            }
            for result in results
        ]
    except Exception as e:
        logging.error(f"Failed to search clients: {e}")
        raise

async def get_client_profile(client_id: str) -> dict | None:
    """Get client profile with enrolled programs."""
    try:
        # Fetch client details
        client_query = """
            SELECT client_id, first_name, last_name, dob, gender, contact, created_at
            FROM clients
            WHERE client_id = :client_id
        """
        client = await database.fetch_one(client_query, {"client_id": client_id})
        if not client:
            return None

        # Fetch enrolled programs
        programs_query = """
            SELECT p.program_id, p.name, p.description
            FROM programs p
            JOIN enrollments e ON p.program_id = e.program_id
            WHERE e.client_id = :client_id
        """
        programs = await database.fetch_all(programs_query, {"client_id": client_id})

        # Construct response
        return {
            "client_id": client["client_id"],
            "first_name": client["first_name"],
            "last_name": client["last_name"],
            "dob": client["dob"],
            "gender": client["gender"],
            "contact": client["contact"],
            "created_at": client["created_at"],
            "programs": [
                {
                    "program_id": program["program_id"],
                    "name": program["name"],
                    "description": program["description"]
                }
                for program in programs
            ]
        }
    except Exception as e:
        logging.error(f"Failed to get client profile: {e}")
        raise