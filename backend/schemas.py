from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[int] = None

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    tenant_id: int
    role: str = "user"

class User(UserBase):
    id: int
    role: str
    tenant_id: int
    api_key: Optional[str] = None

    class Config:
        orm_mode = True

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    tenant_id: int
    owner_id: int

    class Config:
        orm_mode = True

class NoteBase(BaseModel):
    title: str
    content: str
    is_secret: bool = False

class NoteCreate(NoteBase):
    pass

class Note(NoteBase):
    id: int
    user_id: int
    tenant_id: int

    class Config:
        orm_mode = True

class Invoice(BaseModel):
    id: int
    amount: float
    status: str
    date: datetime
    tenant_id: int

    class Config:
        orm_mode = True

# Scoring Schemas
class Vulnerability(BaseModel):
    id: str
    name: str
    category: str
    points: int
    difficulty: str
    severity: str
    found: bool = False

    class Config:
        orm_mode = True

class Scoreboard(BaseModel):
    candidate_name: str
    total_points: int
    found_vulns: List[Vulnerability]

class CandidateSessionStart(BaseModel):
    candidate_name: str
