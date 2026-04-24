from fastapi import FastAPI, Depends, Request, Header, Query, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import jwt
# from sse_starlette.sse import EventSourceResponse # Removing sse_starlette dependency to be explicit
import asyncio
import json

from . import models, database, vulns, schemas
from .routers import auth_router, invoices_router, notes_router, misc_router, admin_router, account_router

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Vulnerable SaaS App", description="Interview Grade Vulnerable App")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local testing ease
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init Vulns
@app.on_event("startup")
def startup_event():
    db = database.SessionLocal()
    vulns.init_vulns(db)
    # Seed initial data if needed?
    # We will use a separate reset command usually, but good to have basics
    db.close()

# Routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(invoices_router.router, prefix="/api/invoices", tags=["invoices"])
app.include_router(notes_router.router, prefix="/api/notes", tags=["notes"])
app.include_router(misc_router.router, prefix="/api/misc", tags=["misc"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["admin"])
app.include_router(account_router.router, prefix="/api/account", tags=["account"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Vulnerable SaaS API"}


# ---------------------------------------------------------------------------
# CSRF Proof-of-Concept attacker page
# Served from port 8000 — a DIFFERENT origin than the frontend (port 3000).
# localhost:8000 and localhost:3000 share the same *site* (localhost) so
# the browser sends SameSite=Lax cookies on the cross-origin POST.
# ---------------------------------------------------------------------------
@app.get("/poc/csrf", response_class=HTMLResponse, include_in_schema=False)
async def csrf_poc_page(candidate_id: str = ""):
    """
    A simulated attacker page that exploits the CSRF vulnerability in
    POST /api/account/update-display-name.

    Access at: http://localhost:8000/poc/csrf?candidate_id=<your_session_id>
    """
    return HTMLResponse(content=f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>You've won a prize! 🎉</title>
  <style>
    body {{ font-family: sans-serif; background: #1a1a2e; color: #eee;
           display: flex; align-items: center; justify-content: center;
           height: 100vh; margin: 0; }}
    .card {{ background: #16213e; border: 2px solid #e94560; border-radius: 12px;
             padding: 40px; max-width: 480px; text-align: center; }}
    h1 {{ color: #e94560; }}
    p  {{ color: #a8a8b3; line-height: 1.6; }}
    button {{ background: #e94560; color: white; border: none; padding: 14px 32px;
              font-size: 1.1rem; border-radius: 8px; cursor: pointer; margin-top: 20px; }}
    button:hover {{ background: #c73652; }}
    .note {{ font-size: 0.75rem; color: #555; margin-top: 16px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>🎁 Congratulations!</h1>
    <p>You have been selected as our lucky visitor.<br>
       Click below to <strong>claim your free prize</strong>!</p>

    <!--
      CSRF ATTACK FORM
      ─────────────────
      This form is hosted at http://localhost:8000 (attacker-controlled server).
      It targets http://localhost:3000 (the victim application).

      The browser will automatically attach the victim's `token` cookie when
      the form submits because localhost:8000 and localhost:3000 are
      considered the SAME SITE by the browser (same scheme + host, different
      port).  Since the cookie has no SameSite=Strict attribute, it is sent
      with this cross-origin POST — no Authorization header needed.

      The server-side endpoint has no CSRF token check and no Origin/Referer
      validation, so the attack succeeds silently.
    -->
    <form
      id="csrf-form"
      action="http://localhost:3000/api/account/update-display-name"
      method="POST"
      enctype="application/x-www-form-urlencoded"
    >
      <input type="hidden" name="display_name" value="CSRF_PWNED" />
      <input type="hidden" name="candidate_id" value="{candidate_id}" />
      <button type="submit">🎉 Claim My Prize!</button>
    </form>

    <p class="note">
      This page is part of the interview lab.<br>
      Served from <strong>:8000</strong> (attacker origin) &rarr;
      attacking <strong>:3000</strong> (victim app).
    </p>
  </div>
</body>
</html>
""")

# Session Management
@app.post("/api/session/start")
def start_session(session_data: schemas.CandidateSessionStart, db: Session = Depends(database.get_db)):
    session = models.CandidateSession(candidate_name=session_data.candidate_name)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "candidate_name": session.candidate_name}

@app.get("/api/session/events")
async def message_stream(request: Request, session_id: str = Query(None)):
    if not session_id:
        # Just a dummy stream if no session
        async def dummy_gen():
            yield f"data: {json.dumps({'type': 'keepalive', 'data': 'no_session'})}\n\n"
        return StreamingResponse(dummy_gen(), media_type="text/event-stream")

    if session_id not in vulns.active_connections:
        vulns.active_connections[session_id] = asyncio.Queue()

    async def event_generator():
        # print(f"DEBUG: Starting SSE stream for {session_id}")
        queue = vulns.active_connections[session_id]
        while True:
            # Check disconnection
            if await request.is_disconnected():
                # print(f"DEBUG: Client {session_id} disconnected")
                break
                
            try:
                # Wait for event
                # print(f"DEBUG: Waiting for event for {session_id}...")
                event = await asyncio.wait_for(queue.get(), timeout=5.0) 
                # print(f"DEBUG: Yielding event for {session_id}: {event}")
                # Manually format SSE message with double newline
                yield f"data: {event}\n\n"
            except asyncio.TimeoutError:
                # print(f"DEBUG: Sending keepalive for {session_id}")
                # Send generic keepalive as JSON string
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
            except Exception as e:
                print(f"DEBUG: Error in SSE stream for {session_id}: {e}")
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/scoreboard/{session_id}")
def get_scoreboard(session_id: str, db: Session = Depends(database.get_db)):
    session = db.query(models.CandidateSession).filter(models.CandidateSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    found = db.query(models.FoundVulnerability).filter(models.FoundVulnerability.session_id == session_id).all()
    total_points = 0
    found_list = []
    
    for f in found:
        v = db.query(models.Vulnerability).filter(models.Vulnerability.id == f.vulnerability_id).first()
        if v:
            total_points += v.points
            found_list.append(v)
            
    return {
        "candidate_name": session.candidate_name,
        "total_points": total_points,
        "found_vulns": found_list
    }
