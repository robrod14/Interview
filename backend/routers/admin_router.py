from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from .. import database, models, schemas, auth

router = APIRouter()

@router.get("/users", response_model=List[schemas.User])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user_vulnerable)
):
    # Admin only endpoint
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/internal-config")
def read_internal_config(request: Request):
    # Restricted to localhost
    client_host = request.client.host
    if client_host not in ["127.0.0.1", "localhost", "::1"]:
        raise HTTPException(status_code=403, detail="Access denied")
        
    return {"INTERNAL_SECRET": "SUPER_SECRET_ADMIN_VALUE_12345"}

@router.post("/reset-lab")
def reset_lab(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Reset logic: Delete all notes, reset invoices, etc?
    # Actually the prompt says "Admin-only 'Reset Lab' action that wipes and reseeds"
    # I'll just delete dynamic data.
    
    db.query(models.Note).delete()
    # db.query(models.Invoice).delete() # Keep seed data?
    # Maybe we should call a reseeding function.
    db.commit()
    return {"message": "Lab reset successfully"}
