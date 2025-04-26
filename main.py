import logging
from fastapi import FastAPI, HTTPException
from db import connect_db, disconnect_db, init_db, check_db_status, create_program, create_client, create_enrollment
from models import ProgramCreate, ProgramResponse, ClientCreate, ClientResponse, EnrollmentCreate, EnrollmentResponse
from utils import sanitize_input, hash_contact
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Health Information System")

@app.on_event("startup")
async def startup_event():
    init_db()  # Initialize schema
    await connect_db()  # Connect to database

@app.on_event("shutdown")
async def shutdown_event():
    await disconnect_db()  # Disconnect from database

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
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Enrollment creation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create enrollment: {str(e)}")