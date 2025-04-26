from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional
import re

class ProgramCreate(BaseModel):
    """Model for creating a health program."""
    name: str = Field(..., min_length=1, max_length=100, description="Program name")
    description: Optional[str] = Field(None, max_length=500, description="Program description")

class ProgramResponse(BaseModel):
    """Model for returning program details."""
    program_id: UUID
    name: str
    description: Optional[str]

class ClientCreate(BaseModel):
    """Model for registering a new client."""
    first_name: str = Field(..., min_length=1, max_length=50, description="Client's first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Client's last name")
    dob: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date of birth (YYYY-MM-DD)")
    gender: str = Field(..., min_length=1, max_length=20, description="Gender")
    contact: str = Field(..., min_length=1, max_length=100, description="Contact info (e.g., email or phone)")

class ClientResponse(BaseModel):
    """Model for returning client profile with enrolled programs."""
    client_id: UUID
    first_name: str
    last_name: str
    dob: str
    gender: str
    contact: str
    created_at: str
    programs: List[ProgramResponse]

class EnrollmentCreate(BaseModel):
    """Model for enrolling a client in a program."""
    client_id: UUID = Field(..., description="Client UUID")
    program_id: UUID = Field(..., description="Program UUID")

class EnrollmentResponse(BaseModel):
    """Model for returning enrollment details."""
    enrollment_id: UUID
    client_id: UUID
    program_id: UUID
    enrollment_date: str

class SearchRequest(BaseModel):
    """Model for searching clients."""
    search_term: str = Field(..., min_length=1, max_length=100, description="Search term for first or last name")