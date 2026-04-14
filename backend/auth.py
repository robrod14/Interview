from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import models, schemas, database, vulns
import asyncio

# SECRET_KEY should be weak for cracking? Or hardcoded?
# "secrets exposed in client-side JS/config" -> Maybe I'll put it in a config endpoint?
SECRET_KEY = "interview-secret-key-123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Standard secure verification
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        # If standard decoding fails, check for NONE alg vulnerability attempt
        try:
             # Try decoding without verification to check headers
             unverified_header = jwt.get_unverified_header(token)
             alg = unverified_header.get('alg', '').lower()
             
             if alg == 'none':
                 # Re-decode with verify_signature=False to get payload
                 payload = jwt.decode(token, None, options={"verify_signature": False})
                 
                 # DETECT VULN
                 # DETECT VULN
                 if x_candidate_id:
                    # We need to run this async, but we are in sync function? 
                    # Wait, get_current_user_vulnerable is async.
                    # But get_current_user is SYNC!
                    # So we cannot await here!
                    # We should probably just log it or fire-and-forget?
                    # Or use asyncio.create_task if there is a running loop?
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(vulns.award_points(x_candidate_id, "broken-auth-jwt", db))
                        else:
                            loop.run_until_complete(vulns.award_points(x_candidate_id, "broken-auth-jwt", db))
                    except RuntimeError:
                         # If no loop?
                         asyncio.run(vulns.award_points(x_candidate_id, "broken-auth-jwt", db))
                 
                 username = payload.get("sub")
                 if username is None:
                     raise credentials_exception
                 
                 token_data = schemas.TokenData(username=username)
                 
                 # Look up user
                 user = db.query(models.User).filter(models.User.username == token_data.username).first()
                 if user is None:
                     raise credentials_exception
                     
                 # Privilege Escalation Logic
                 if "role" in payload:
                     user.role = payload["role"]
                     
                 return user
        except Exception:
             pass
             
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# Vulnerable version for specific endpoints or if we want global vulnerability
async def get_current_user_vulnerable(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(database.get_db),
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID")
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check "none" algorithm FIRST
    try:
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get('alg', '').lower()
        
        if alg == 'none':
             # Allow "none" alg -> Decode without verification
             payload = jwt.decode(token, None, options={"verify_signature": False})
             
             # DETECT VULN
             if x_candidate_id:
                 await vulns.award_points(x_candidate_id, "broken-auth-jwt", db)
                 
             username = payload.get("sub")
             if username is None:
                 raise credentials_exception
             
             # User Lookup
             user = db.query(models.User).filter(models.User.username == username).first()
             if user is None:
                 raise credentials_exception
                 
             # Privilege Escalation
             if "role" in payload:
                 user.role = payload["role"]
                 
             return user
    except Exception:
        # If any error in manual "none" check, fall through to standard check
        pass

    # Standard Verification (Safe)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    
    return user
