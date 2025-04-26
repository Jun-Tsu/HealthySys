import logging
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from db import connect_db, disconnect_db, init_db, check_db_status, create_program, create_client, create_enrollment, search_clients, get_client_profile
from models import ProgramCreate, ProgramResponse, ClientCreate, ClientResponse, EnrollmentCreate, EnrollmentResponse, SearchRequest
from utils import sanitize_input, hash_contact
from uuid import UUID
from typing import List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    init_db()  # Initialize schema
    await connect_db()  # Connect to database
    logging.info("Application startup complete")
    yield
    await disconnect_db()  # Disconnect from database
    logging.info("Application shutdown complete")

app = FastAPI(title="Health Information System", lifespan=lifespan)

@app.get("/")
async def root():
    logging.info("Root endpoint accessed")
    return {"message": "Health System API is running"}

@app.get("/db-status")
async def db_status():
    logging.info("Database status endpoint accessed")
    return await check_db_status()

@app.post("/api/programs", response_model=ProgramResponse, status_code=201)
async def create_program_endpoint(program: ProgramCreate):
    """Create a new health program."""
    try:
        # Sanitize inputs
        name = sanitize_input(program.name)
        description = sanitize_input(program.description) if program.description else None

        # Create program in database
        program_id = await create_program(name, description)

        # Return response
        return {"program_id": program_id, "name": name, "description": description}
    except ValueError as e:
        logging.error(f"Program creation failed: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logging.error(f"Program creation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create program: {str(e)}")

@app.post("/api/clients", response_model=ClientResponse, status_code=201)
async def create_client_endpoint(client: ClientCreate):
    """Register a new client."""
    try:
        # Sanitize inputs
        first_name = sanitize_input(client.first_name)
        last_name = sanitize_input(client.last_name)
        dob = sanitize_input(client.dob)
        gender = sanitize_input(client.gender)
        contact = sanitize_input(client.contact)

        # Hash contact for security
        hashed_contact = hash_contact(contact)

        # Create client in database
        client_id = await create_client(first_name, last_name, dob, gender, hashed_contact)

        # Return response
        return {
            "client_id": client_id,
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "gender": gender,
            "contact": contact,  # Return original contact, not hashed
            "created_at": datetime.utcnow().isoformat(),
            "programs": []
        }
    except ValueError as e:
        logging.error(f"Client creation failed: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logging.error(f"Client creation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create client: {str(e)}")

@app.post("/api/enrollments", response_model=EnrollmentResponse, status_code=201)
async def create_enrollment_endpoint(enrollment: EnrollmentCreate):
    """Enroll a client in a program."""
    try:
        # Create enrollment in database
        enrollment_id = await create_enrollment(str(enrollment.client_id), str(enrollment.program_id))

        # Return response
        return {
            "enrollment_id": enrollment_id,
            "client_id": enrollment.client_id,
            "program_id": enrollment.program_id,
            "enrollment_date": datetime.utcnow().isoformat()
        }
    except ValueError as e:
        logging.error(f"Enrollment creation failed: {e}")
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Enrollment creation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create enrollment: {str(e)}")

@app.post("/api/clients/search", response_model=List[ClientResponse])
async def search_clients_endpoint(search: SearchRequest):
    """Search clients by first or last name."""
    try:
        # Sanitize search term
        search_term = sanitize_input(search.search_term)

        # Search clients in database
        clients = await search_clients(search_term)

        # Return response with empty programs list (to be populated in profile endpoint)
        return [
            {
                "client_id": client["client_id"],
                "first_name": client["first_name"],
                "last_name": client["last_name"],
                "dob": client["dob"],
                "gender": client["gender"],
                "contact": client["contact"],  # Note: Hashed in DB, original returned for simplicity
                "created_at": client["created_at"],
                "programs": []
            }
            for client in clients
        ]
    except Exception as e:
        logging.error(f"Client search failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to search clients: {str(e)}")

@app.get("/api/clients/{client_id}", response_model=ClientResponse)
async def get_client_profile_endpoint(client_id: UUID):
    """Get client profile with enrolled programs."""
    try:
        # Get client profile from database
        profile = await get_client_profile(str(client_id))
        if not profile:
            raise ValueError("Client not found")

        # Return response
        return profile
    except ValueError as e:
        logging.error(f"Client profile fetch failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Client profile fetch failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch client profile: {str(e)}")