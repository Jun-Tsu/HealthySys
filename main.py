import logging
from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from db import connect_db, disconnect_db, init_db, check_db_status, create_program, create_client, create_enrollment, search_clients, get_client_profile
from models import ProgramCreate, ProgramResponse, ClientCreate, ClientResponse, EnrollmentCreate, EnrollmentResponse, SearchRequest
from utils import sanitize_input, hash_contact
from uuid import UUID
from typing import List, AsyncGenerator
from datetime import datetime
from fastapi_users import FastAPIUsers, BaseUserManager, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from fastapi_users.schemas import BaseUser, BaseUserCreate
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from os import getenv
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SECRET = getenv("JWT_SECRET")
if not SECRET:
    raise ValueError("JWT_SECRET not set in .env")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# SQLAlchemy User Model
class Base(DeclarativeBase):
    pass

class User(SQLAlchemyBaseUserTableUUID, Base):
    pass

# Database setup for fastapi-users
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/health_system.db")
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

# FastAPI-Users configuration
class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request=None):
        logging.info(f"User {user.id} has registered.")

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)

get_current_user = fastapi_users.current_user(active=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    init_db()
    await connect_db()
    logging.info("Application startup complete")
    yield
    await disconnect_db()
    await engine.dispose()
    logging.info("Application shutdown complete")

app = FastAPI(title="Health Information System", lifespan=lifespan)

# Authentication routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(BaseUser, BaseUserCreate),
    prefix="/auth",
    tags=["auth"]
)

@app.get("/")
async def root():
    return {"message": "Health System API is running"}

@app.get("/db-status")
async def db_status():
    return await check_db_status()

@app.post("/api/programs", response_model=ProgramResponse, status_code=201)
async def create_program_endpoint(program: ProgramCreate, current_user: User = Depends(get_current_user)):
    """Create a new health program."""
    try:
        name = sanitize_input(program.name)
        description = sanitize_input(program.description) if program.description else None
        program_id = await create_program(name, description)
        return {"program_id": program_id, "name": name, "description": description}
    except ValueError as e:
        logging.error(f"Program creation failed: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logging.error(f"Program creation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create program: {str(e)}")

@app.post("/api/clients", response_model=ClientResponse, status_code=201)
async def create_client_endpoint(client: ClientCreate, current_user: User = Depends(get_current_user)):
    """Register a new client."""
    try:
        first_name = sanitize_input(client.first_name)
        last_name = sanitize_input(client.last_name)
        dob = sanitize_input(client.dob)
        gender = sanitize_input(client.gender)
        contact = sanitize_input(client.contact)
        hashed_contact = hash_contact(contact)
        client_id = await create_client(first_name, last_name, dob, gender, hashed_contact)
        return {
            "client_id": client_id,
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "gender": gender,
            "contact": contact,
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
async def create_enrollment_endpoint(enrollment: EnrollmentCreate, current_user: User = Depends(get_current_user)):
    """Enroll a client in a program."""
    try:
        enrollment_id = await create_enrollment(str(enrollment.client_id), str(enrollment.program_id))
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
async def search_clients_endpoint(search: SearchRequest, current_user: User = Depends(get_current_user)):
    """Search clients by first or last name."""
    try:
        search_term = sanitize_input(search.search_term)
        clients = await search_clients(search_term)
        return [
            {
                "client_id": client["client_id"],
                "first_name": client["first_name"],
                "last_name": client["last_name"],
                "dob": client["dob"],
                "gender": client["gender"],
                "contact": client["contact"],
                "created_at": client["created_at"],
                "programs": []
            }
            for client in clients
        ]
    except Exception as e:
        logging.error(f"Client search failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to search clients: {str(e)}")

@app.get("/api/clients/{client_id}", response_model=ClientResponse)
async def get_client_profile_endpoint(client_id: UUID, current_user: User = Depends(get_current_user)):
    """Get client profile with enrolled programs."""
    try:
        profile = await get_client_profile(str(client_id))
        if not profile:
            raise ValueError("Client not found")
        return profile
    except ValueError as e:
        logging.error(f"Client profile fetch failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Client profile fetch failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch client profile: {str(e)}")