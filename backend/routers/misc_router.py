from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
import requests
import re
import subprocess
from typing import Optional
from sqlalchemy.orm import Session
from .. import vulns, database, models, auth

router = APIRouter()

class UrlRequest(BaseModel):
    url: str

class PingRequest(BaseModel):
    host: str

@router.post("/fetch-avatar")
async def fetch_avatar(
    request: UrlRequest,
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID")
):
    # SSRF VULNERABILITY
    # We fetch whatever URL is provided.
    
    url = request.url
    
    # Detection logic
    # If they try to access localhost or 127.0.0.1
    # especially targeting our internal admin port/path
    
    target_indicators = ["localhost", "127.0.0.1", "0.0.0.0", "[::1]"]
    
    # Check if it's an SSRF attempt against local infrastructure
    is_ssrf_attempt = any(t in url for t in target_indicators)
    
    # If they are targeting the specific internal endpoint
    if is_ssrf_attempt and "internal-config" in url:
        # High value target hit
        if x_candidate_id:
            # We need a db session to award points
            db = database.SessionLocal()
            try:
                await vulns.award_points(x_candidate_id, "ssrf-avatar", db)
            finally:
                db.close()

    # Check for File Protocol (LFI via SSRF)
    if url.startswith("file://"):
        # This is what the user specifically asked for: allow file:///etc/passwd
        # If they access /etc/passwd, award points.
        if "/etc/passwd" in url:
             if x_candidate_id:
                db = database.SessionLocal()
                try:
                    await vulns.award_points(x_candidate_id, "ssrf-avatar", db)
                finally:
                    db.close()
        
        # Actually try to read the file (simulated or real)
        # Since we are running on host/container, we might not want to expose REAL /etc/passwd if sensitive,
        # but for an interview lab running in a container/vm, it's fine.
        # However, if running on user's mac directly (as I am now), reading /etc/passwd is real.
        # I'll strip the prefix and read.
        file_path = url[7:] # strip file://
        try:
            with open(file_path, "r") as f:
                content = f.read()
                return {
                    "status": 200,
                    "content_length": len(content),
                    "data": content[:500]
                }
        except Exception as e:
             return {"error": f"Failed to read file: {str(e)}"}
    
    try:
        # Real fetch
        # Set timeout to 5 seconds to handle slower connections
        resp = requests.get(url, timeout=5)
        
        # Check content type
        content_type = resp.headers.get("Content-Type", "")
        
        # If it's an image, return base64 so frontend can display it
        if "image" in content_type:
            import base64
            b64_img = base64.b64encode(resp.content).decode('utf-8')
            return {
                "status": resp.status_code,
                "content_length": len(resp.content),
                "is_image": True,
                "image_data": f"data:{content_type};base64,{b64_img}",
                "data": "[Image Content Binary]" # Don't dump binary to text field
            }
            
        return {
            "status": resp.status_code,
            "content_length": len(resp.content),
            "is_image": False,
            "data": resp.text[:500] # Leak data
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/search")
async def search_notes(
    q: Optional[str] = Query(None, description="Search query for notes"),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID")
):
    """
    Search notes by keyword.

    Returns matching notes and reflects the raw search term back in the response.
    The frontend renders `search_term` directly via dangerouslySetInnerHTML.

    VULNERABILITY: DOM-Based XSS
    The `q` parameter is reflected into the response as `search_term` without
    sanitisation. The frontend reads the ?q= URL parameter and injects it into
    the DOM via dangerouslySetInnerHTML, allowing script execution when a victim
    visits a crafted URL such as:
      /dashboard/notes?q=<img src=x onerror=alert(1)>
    """
    if not q:
        return {"results": [], "search_term": "", "count": 0}

    # BLACKLIST: strip <script> tags FIRST before any detection or response.
    # Candidates who use <script>alert(1)</script> will have their payload
    # removed here — the sanitized string is what gets returned AND checked.
    # This intentionally forces candidates to use non-script XSS vectors such
    # as <img src=x onerror=alert(1)> or <svg onload=alert(1)>.
    sanitized_term = re.sub(
        r'<script[\s\S]*?>[\s\S]*?</script>', '', q, flags=re.IGNORECASE
    )
    # Also strip lone opening <script ...> tags with no closing tag
    sanitized_term = re.sub(r'<script[^>]*/?>', '', sanitized_term, flags=re.IGNORECASE)

    # DETECTION: check the SANITIZED string, not the raw input.
    # Points are only awarded if a working XSS payload survived the blacklist.
    # <script> payloads are stripped above so they will never match here.
    xss_patterns = [
        r"javascript:",
        r"onerror=",
        r"onload=",
        r"ontoggle=",
        r"onfocus=",
        r"<img[\s]",
        r"<svg[\s>]",
        r"<iframe",
        r"<details",
        r"alert\(",
        r"prompt\(",
        r"confirm\(",
    ]
    is_xss = any(re.search(p, sanitized_term, re.IGNORECASE) for p in xss_patterns)

    if is_xss and x_candidate_id:
        await vulns.award_points(x_candidate_id, "dom-xss-search", db)

    # Search the user's own tenant notes (access controlled here)
    results = (
        db.query(models.Note)
        .filter(
            models.Note.tenant_id == current_user.tenant_id,
            models.Note.content.contains(q)
            | models.Note.title.contains(q)
        )
        .limit(20)
        .all()
    )

    return {
        # VULNERABLE: sanitized_term is reflected back and the frontend renders
        # it with dangerouslySetInnerHTML — but only non-script payloads survive.
        "search_term": sanitized_term,
        "count": len(results),
        "results": [
            {"id": n.id, "title": n.title, "content": n.content[:200]}
            for n in results
        ],
    }


@router.post("/ping")
async def ping_host(
    request: PingRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID")
):
    """
    Network diagnostics: pings a hostname or IP and returns the output.

    VULNERABILITY: Command Injection
    User-supplied input is passed directly to the shell without sanitisation.
    An attacker can inject arbitrary OS commands by appending shell metacharacters:
      host = "127.0.0.1; whoami"
      host = "127.0.0.1 && cat /etc/passwd"
      host = "127.0.0.1 | id"
    """
    host = request.host

    # DETECTION: shell metacharacters indicate injection attempt
    injection_chars = [";", "&&", "||", "|", "`", "$(", ">", "<", "\n", "\r"]
    is_injection = any(ch in host for ch in injection_chars)

    if is_injection and x_candidate_id:
        await vulns.award_points(x_candidate_id, "cmd-injection-ping", db)

    try:
        # VULNERABLE: shell=True with unsanitised input
        result = subprocess.run(
            f"ping -c 2 {host}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            "host": host,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"host": host, "error": "Command timed out after 10 seconds."}
    except Exception as e:
        return {"host": host, "error": str(e)}
