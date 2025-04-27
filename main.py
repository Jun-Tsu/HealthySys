import logging
from fastapi import FastAPI, HTTPException, Depends, status, Request
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
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import text
from os import getenv
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()
SECRET = getenv("JWT_SECRET")
if not SECRET:
    raise ValueError("JWT_SECRET not set in .env")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# SQLAlchemy Models
class Base(DeclarativeBase):
    pass

class User(SQLAlchemyBaseUserTableUUID, Base):
    role = Column(String, nullable=False, default="viewer")  # Roles: admin, staff, viewer

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    action = Column(String, nullable=False)
    details = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

# Database setup for fastapi-users
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///health_system.db"
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
        async with async_session_maker() as session:
            audit_log = AuditLog(user_id=str(user.id), action="register", details=f"Email: {user.email}")
            session.add(audit_log)
            await session.commit()

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600, token_audience=None)

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
logging.info("Using fastapi_users.current_user for authentication")

# RBAC Dependency
def require_role(role: str):
    def role_checker(user: User = Depends(get_current_user)):
        logging.info(f"Checking role: {role} for user: {user.id}")
        if user.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Operation requires {role} role")
        return user
    return role_checker

# Audit Logging Helper
async def log_action(user_id: str, action: str, details: str, session: AsyncSession):
    audit_log = AuditLog(user_id=user_id, action=action, details=details)
    session.add(audit_log)
    await session.commit()

# Lifespan with Admin Initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    init_db()
    await connect_db()
    # Initialize admin user if none exists
    async with async_session_maker() as session:
        async with session.begin():
            result = await session.execute(text("SELECT COUNT(*) FROM user WHERE role = 'admin'"))
            admin_count = result.scalar()
            if admin_count == 0:
                # Create admin@q.com with password admin1234
                user_manager = UserManager(SQLAlchemyUserDatabase(session, User))
                try:
                    admin_user = await user_manager.create(
                        BaseUserCreate(
                            email="admin@q.com",
                            password="admin1234",
                            is_active=True,
                            is_superuser=False,
                            is_verified=False
                        )
                    )
                    # Set role to admin
                    await session.execute(
                        text("UPDATE user SET role = 'admin' WHERE email = :email"),
                        {"email": "admin@q.com"}
                    )
                    await session.commit()
                    logging.info("Created admin user: admin@q.com")
                    await log_action("system", "init_admin", "Created admin@q.com", session)
                except Exception as e:
                    logging.error(f"Failed to create admin user: {e}")
    logging.info("Application startup complete")
    yield
    await disconnect_db()
    await engine.dispose()
    logging.info("Application shutdown complete")

# FastAPI App
app = FastAPI(title="Health Information System", lifespan=lifespan)

# Middleware for Audit Logging
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    logging.info(f"Middleware processing: {request.method} {request.url.path}")
    if request.url.path == "/auth/jwt/login":
        return await call_next(request)
    response = await call_next(request)
    user = None
    try:
        user = await get_current_user(request)
        logging.info(f"Middleware user: {user.id}")
    except Exception as e:
        logging.info(f"Middleware: No user authenticated or error: {str(e)}")
    if user:
        async with async_session_maker() as session:
            action = f"{request.method} {request.url.path}"
            details = f"Client IP: {request.client.host}"
            await log_action(str(user.id), action, details, session)
    return response

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

# Set Role Endpoint
class SetRoleRequest(BaseModel):
    email: str
    role: str

@app.post("/api/set-role", status_code=200)
async def set_user_role(
    request: SetRoleRequest,
    current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_async_session)
):
    """Update a user's role."""
    try:
        email = sanitize_input(request.email)
        role = sanitize_input(request.role)
        if role not in ["admin", "staff", "viewer"]:
            raise ValueError("Invalid role")
        async with session.begin():
            result = await session.execute(
                text("UPDATE user SET role = :role WHERE email = :email"),
                {"role": role, "email": email}
            )
            if result.rowcount == 0:
                raise ValueError("User not found")
            await session.commit()
        await log_action(
            str(current_user.id),
            "set_role",
            f"User: {email}, New Role: {role}",
            session
        )
        return {"message": f"Role updated for {email} to {role}"}
    circa ValueError as e:
        logging.error(f"Role update failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Role update failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to update role: {str(e)}")

# Temporary Init Admin Endpoint
class InitAdminRequest(BaseModel):
    email: str

@app.post("/api/init-admin", status_code=200)
async def init_admin(
    request: InitAdminRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """Temporarily set a user to admin (one-time use)."""
    try:
        email = sanitize_input(request.email)
        async with session.begin():
            result = await session.execute(
                text("UPDATE user SET role = 'admin' WHERE email = :email"),
                {"email": email}
            )
            if result.rowcount == 0:
                raise ValueError("User not found")
            await session.commit()
        await log_action(
            "system",
            "init_admin",
            f"Set {email} to admin",
            session
        )
        return {"message": f"User {email} set to admin"}
    except ValueError as e:
        logging.error(f"Init admin failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Init admin failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to set admin: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Health System API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/db-status")
async def db_status():
    return await check_db_status()

@app.post("/api/programs", response_model=ProgramResponse, status_code=201)
async def create_program_endpoint(
    program: ProgramCreate,
    current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new health program."""
    try:
        name = sanitize_input(program.name)
        description = sanitize_input(program.description) if program.description else None
        program_id = await create_program(name, description)
        await log_action(
            str(current_user.id),
            "create_program",
            f"Program ID: {program_id}, Name: {name}",
            session
        )
        return {"program_id": program_id, "name": name, "description": description}
    except ValueError as e:
        logging.error(f"Program creation failed: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logging.error(f"Program creation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create program: {str(e)}")

@app.post("/api/clients", response_model=ClientResponse, status_code=201)
async def create_client_endpoint(
    client: ClientCreate,
    current_user: User = Depends(require_role("staff")),
    session: AsyncSession = Depends(get_async_session)
):
    """Register a new client."""
    try:
        first_name = sanitize_input(client.first_name)
        last_name = sanitize_input(client.last_name)
        dob = sanitize_input(client.dob)
        gender = sanitize_input(client.gender)
        contact = sanitize_input(client.contact)
        hashed_contact = hash_contact(contact)
        client_id = await create_client(first_name, last_name, dob, gender, hashed_contact)
        await log_action(
            str(current_user.id),
            "create_client",
            f"Client ID: {client_id}, Name: {first_name} {last_name}",
            session
        )
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
async def create_enrollment_endpoint(
    enrollment: EnrollmentCreate,
    current_user: User = Depends(require_role("staff")),
    session: AsyncSession = Depends(get_async_session)
):
    """Enroll a client in a program."""
    try:
        enrollment_id = await create_enrollment(str(enrollment.client_id), str(enrollment.program_id))
        await log_action(
            str(current_user.id),
            "create_enrollment",
            f"Enrollment ID: {enrollment_id}, Client ID: {enrollment.client_id}, Program ID: {enrollment.program_id}",
            session
        )
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
async def search_clients_endpoint(
    search: SearchRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Search clients by first or last name."""
    try:
        search_term = sanitize_input(search.search_term)
        clients = await search_clients(search_term)
        await log_action(
            str(current_user.id),
            "search_clients",
            f"Search Term: {search_term}, Results: {len(clients)}",
            session
        )
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
async def get_client_profile_endpoint(
    client_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get client profile with enrolled programs."""
    try:
        profile = await get_client_profile(str(client_id))
        if not profile:
            raise ValueError("Client not found")
        await log_action(
            str(current_user.id),
            "get_client_profile",
            f"Client ID: {client_id}",
            session
        )
        return profile
    except ValueError as e:
        logging.error(f"Client profile fetch failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Client profile fetch failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch client profile: {str(e)}")