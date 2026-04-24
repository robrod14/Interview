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
    },
    {
        "id": "dom-xss-search",
        "name": "DOM-Based XSS (Notes Search)",
        "category": "XSS",
        "difficulty": "Hard",
        "points": 300,
        "severity": "High",
        "description": "Inject a payload via the ?q= URL parameter which is rendered unsafely into the DOM without sanitisation."
    },
    {
        "id": "mass-assignment-role",
        "name": "Mass Assignment (Privilege Escalation)",
        "category": "Broken Access Control",
        "difficulty": "Medium",
        "points": 200,
        "severity": "Critical",
        "description": "The profile update endpoint blindly applies all JSON fields, allowing a user to escalate their own role to admin."
    },
    {
        "id": "pwd-reset-token-leak",
        "name": "Password Reset Token Exposure",
        "category": "Sensitive Data Exposure",
        "difficulty": "Medium",
        "points": 200,
        "severity": "High",
        "description": "The forgot-password API returns the reset token directly in the JSON response, allowing an attacker to reset any user's password without email access."
    },
    {
        "id": "cmd-injection-ping",
        "name": "Command Injection (Network Ping)",
        "category": "Injection",
        "difficulty": "Hard",
        "points": 300,
        "severity": "Critical",
        "description": "The ping diagnostic endpoint passes user input directly to a shell command, enabling OS command injection."
    },
    {
        "id": "open-redirect-login",
        "name": "Open Redirect (Post-Login)",
        "category": "Broken Access Control",
        "difficulty": "Easy",
        "points": 125,
        "severity": "Medium",
        "description": "The post-login redirect endpoint accepts an arbitrary ?next= URL without validation, enabling phishing redirects."
    },
    {
        "id": "csrf-display-name",
        "name": "CSRF (Display Name Update)",
        "category": "Cross-Site Request Forgery",
        "difficulty": "Hard",
        "points": 250,
        "severity": "High",
        "description": "The display-name update endpoint authenticates via a session cookie with no CSRF token validation. A malicious page on any same-site origin can silently change the victim's display name."
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
