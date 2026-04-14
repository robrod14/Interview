from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import re
from .. import database, models, schemas, auth, vulns

router = APIRouter()

@router.post("", response_model=schemas.Note)
async def create_note(
    note: schemas.NoteCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID")
):
    # STORED XSS VULNERABILITY:
    # We save the content directly.
    # Detection: Check for XSS patterns
    
    xss_patterns = [
        r"<script>", 
        r"javascript:", 
        r"onload=", 
        r"onerror=", 
        r"alert\(",
        r"prompt\("
    ]
    
    is_xss = any(re.search(p, note.content, re.IGNORECASE) for p in xss_patterns)
    
    if is_xss:
        if x_candidate_id:
            await vulns.award_points(x_candidate_id, "stored-xss-note", db)

    db_note = models.Note(**note.dict(), user_id=current_user.id, tenant_id=current_user.tenant_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@router.get("", response_model=List[schemas.Note])
def read_notes(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    notes = db.query(models.Note).filter(models.Note.tenant_id == current_user.tenant_id).offset(skip).limit(limit).all()
    return notes

@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID")
):
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    # IDOR VULNERABILITY (Delete Note)
    # We allow deleting if the note exists, but we fail to check ownership properly
    # or we "accidentally" allow it.
    
    if note.user_id != current_user.id:
        # Detected IDOR attempt
        if x_candidate_id:
            await vulns.award_points(x_candidate_id, "idor-delete-note", db)
        
        # We proceed to delete it anyway to allow the exploit
        db.delete(note)
        db.commit()
        return {"message": "Note deleted"}

    # Normal deletion
    db.delete(note)
    db.commit()
    return {"message": "Note deleted"}
