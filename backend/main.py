from fastapi import FastAPI, Depends, Request, Header, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import jwt
# from sse_starlette.sse import EventSourceResponse # Removing sse_starlette dependency to be explicit
import asyncio
import json

from . import models, database, vulns, schemas
from .routers import auth_router, invoices_router, notes_router, misc_router, admin_router

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

@app.get("/")
def read_root():
    return {"message": "Welcome to the Vulnerable SaaS API"}

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
