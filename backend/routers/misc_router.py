from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import requests
from typing import Optional
from .. import vulns, database

router = APIRouter()

class UrlRequest(BaseModel):
    url: str

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
