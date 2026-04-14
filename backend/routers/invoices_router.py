from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import database, models, schemas, auth, vulns

router = APIRouter()

@router.get("", response_model=List[schemas.Invoice])
def read_invoices(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Safe endpoint: only returns own tenant's invoices
    invoices = db.query(models.Invoice).filter(models.Invoice.tenant_id == current_user.tenant_id).offset(skip).limit(limit).all()
    return invoices

@router.get("/{invoice_id}", response_model=schemas.Invoice)
async def read_invoice(
    invoice_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID")
):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # IDOR VULNERABILITY:
    # We check if invoice exists, but we DO NOT check if it belongs to the user's tenant.
    # OR we check it but only for "logging" the vuln, and then return it anyway.
    
    if invoice.tenant_id != current_user.tenant_id:
        # IDOR DETECTED
        if x_candidate_id:
            await vulns.award_points(x_candidate_id, "idor-invoice", db)
        
        # We return it anyway to allow exploitation
        return invoice
        
    return invoice
