from sqlalchemy.orm import Session
from . import models
import asyncio
import json

# In-memory event queue for SSE
# Map session_id -> asyncio.Queue
active_connections = {}

VULNERABILITIES = [
    {
        "id": "sqli-login",
        "name": "SQL Injection (Login Bypass)",
        "category": "Injection",
        "difficulty": "Easy",
        "points": 100,
        "severity": "High",
        "description": "Bypass authentication using SQL injection in the login form."
    },
    {
        "id": "idor-invoice",
        "name": "IDOR (Invoices)",
        "category": "Broken Access Control",
        "difficulty": "Easy",
        "points": 100,
        "severity": "High",
        "description": "Access an invoice belonging to another tenant."
    },
    {
        "id": "stored-xss-note",
        "name": "Stored XSS (Notes)",
        "category": "XSS",
        "difficulty": "Medium",
        "points": 150,
        "severity": "Medium",
        "description": "Store a malicious script in a note that executes when viewed."
    },
    {
        "id": "idor-delete-note",
        "name": "IDOR (Delete Note)",
        "category": "Broken Access Control",
        "difficulty": "Easy",
        "points": 100,
        "severity": "High",
        "description": "Delete a note belonging to another user."
    },
    {
        "id": "broken-auth-jwt",
        "name": "JWT None Algorithm",
        "category": "Broken Authentication",
        "difficulty": "Medium",
        "points": 200,
        "severity": "Critical",
        "description": "Forge a JWT token using the 'none' algorithm to impersonate admin."
    },
    {
        "id": "ssrf-avatar",
        "name": "SSRF (Avatar Upload)",
        "category": "SSRF",
        "difficulty": "Hard",
        "points": 250,
        "severity": "High",
        "description": "Server-side Request Forgery via avatar URL fetcher."
    }
]

async def award_points(session_id: str, vuln_id: str, db: Session):
    if not session_id:
        return
        
    # Check if session exists
    session = db.query(models.CandidateSession).filter(models.CandidateSession.id == session_id).first()
    if not session:
        return

    # Check if already found
    existing = db.query(models.FoundVulnerability).filter(
        models.FoundVulnerability.session_id == session_id,
        models.FoundVulnerability.vulnerability_id == vuln_id
    ).first()

    if existing:
        return # Already found

    # Mark as found
    found = models.FoundVulnerability(session_id=session_id, vulnerability_id=vuln_id)
    db.add(found)
    db.commit()
    
    # Get vuln details
    vuln = next((v for v in VULNERABILITIES if v["id"] == vuln_id), None)
    if not vuln:
        return

        # Notify via SSE
    if session_id in active_connections:
        # print(f"DEBUG: Session {session_id} is active. Sending SSE payload.")
        # Send raw JSON string without event name
        payload = json.dumps({
            "type": "vuln_found",
            "payload": {
                "vuln_id": vuln["id"],
                "name": vuln["name"],
                "points": vuln["points"]
            }
        })
        await active_connections[session_id].put(payload)
    else:
        print(f"DEBUG: Session {session_id} NOT found in active_connections. Keys: {list(active_connections.keys())}")
    
    print(f"VULNERABILITY FOUND: {vuln_id} by session {session_id}")

def init_vulns(db: Session):
    for v_data in VULNERABILITIES:
        existing = db.query(models.Vulnerability).filter(models.Vulnerability.id == v_data["id"]).first()
        if not existing:
            v = models.Vulnerability(**v_data)
            db.add(v)
    db.commit()
