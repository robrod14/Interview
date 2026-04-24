from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    users = relationship("User", back_populates="tenant")
    projects = relationship("Project", back_populates="tenant")
    invoices = relationship("Invoice", back_populates="tenant")
    notes = relationship("Note", back_populates="tenant")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user") # 'admin' or 'user'
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    api_key = Column(String, nullable=True)
    display_name = Column(String, nullable=True)  # Used by CSRF demo endpoint

    tenant = relationship("Tenant", back_populates="users")
    projects = relationship("Project", back_populates="owner")
    notes = relationship("Note", back_populates="author")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    is_public = Column(Boolean, default=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))

    tenant = relationship("Tenant", back_populates="projects")
    owner = relationship("User", back_populates="projects")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    status = Column(String) # 'paid', 'pending'
    date = Column(DateTime, default=func.now())
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    
    tenant = relationship("Tenant", back_populates="invoices")

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text) # Vulnerable to XSS?
    user_id = Column(Integer, ForeignKey("users.id"))
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    is_secret = Column(Boolean, default=False)

    author = relationship("User", back_populates="notes")
    tenant = relationship("Tenant", back_populates="notes")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, ForeignKey("users.username"), index=True)
    token = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=func.now())
    used = Column(Boolean, default=False)

    user = relationship("User", foreign_keys=[username])


# Scoring System Models

class CandidateSession(Base):
    __tablename__ = "candidate_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_name = Column(String)
    start_time = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    found_vulns = relationship("FoundVulnerability", back_populates="session")

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(String, primary_key=True) # e.g. 'idor-1'
    name = Column(String)
    category = Column(String)
    difficulty = Column(String) # 'Easy', 'Medium', 'Hard'
    points = Column(Integer)
    severity = Column(String) # 'Low', 'Medium', 'High', 'Critical'
    description = Column(String)

class FoundVulnerability(Base):
    __tablename__ = "found_vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("candidate_sessions.id"))
    vulnerability_id = Column(String, ForeignKey("vulnerabilities.id"))
    found_at = Column(DateTime, default=func.now())

    session = relationship("CandidateSession", back_populates="found_vulns")
    vulnerability = relationship("Vulnerability")
