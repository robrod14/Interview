from fastapi import APIRouter, Depends, Request, Form, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional

from .. import database, models, vulns
from ..auth import SECRET_KEY, ALGORITHM

router = APIRouter()


def _user_from_cookie(request: Request, db: Session) -> Optional[models.User]:
    """
    Authenticate a request using the 'token' cookie.

    VULNERABILITY: This function intentionally reads the JWT from a browser
    cookie instead of the Authorization header.  Cookies are sent automatically
    by the browser on every same-site request — including cross-origin HTML
    form submissions — making any endpoint that relies solely on cookie auth
    vulnerable to CSRF.
    """
    token = request.cookies.get("token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
        return db.query(models.User).filter(models.User.username == username).first()
    except JWTError:
        return None


@router.get("/display-name")
async def get_display_name(
    request: Request,
    db: Session = Depends(database.get_db),
):
    """
    Returns the current user's display name.
    Uses cookie-based auth (same vulnerable path as update-display-name).
    """
    user = _user_from_cookie(request, db)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    return {
        "username": user.username,
        "display_name": user.display_name or user.username,
    }


@router.post("/update-display-name")
async def update_display_name(
    request: Request,
    db: Session = Depends(database.get_db),
    # Form fields — standard HTML forms send application/x-www-form-urlencoded
    display_name: Optional[str] = Form(None),
    candidate_id: Optional[str] = Form(None),
    # Also accept JSON body fields for API clients
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID"),
):
    """
    Updates the authenticated user's display name.

    VULNERABILITY: Cross-Site Request Forgery (CSRF)
    ─────────────────────────────────────────────────
    This endpoint authenticates requests using ONLY the 'token' session cookie.
    There is no CSRF token, no Origin/Referer validation, and no SameSite=Strict
    restriction on the cookie.

    Because the JWT token is stored as a plain cookie (set by js-cookie without
    SameSite=Strict), ANY HTML page on a same-site origin — including pages
    served directly from this backend on port 8000 — can submit a form that the
    browser will accompany with the victim's session cookie, changing their
    display name without their knowledge or consent.

    Attack vector:
      1. Attacker serves malicious HTML at http://localhost:8000/poc/csrf
      2. Victim (already logged in at localhost:3000) visits that page
      3. Hidden form auto-submits to http://localhost:3000/api/account/update-display-name
      4. Browser sends 'token' cookie automatically (same-site: localhost)
      5. No Authorization header required — cookie auth succeeds
      6. Display name silently changed

    Indicators of the vulnerability:
      • No X-CSRF-Token / XSRF-TOKEN header or form field required
      • Endpoint accepts application/x-www-form-urlencoded (classic HTML form)
      • Cookie has no SameSite=Strict attribute
      • No Referer/Origin validation in the handler
    """
    # ── Authenticate via cookie (the vulnerable path) ──────────────────────
    user = _user_from_cookie(request, db)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    # ── Handle both form-encoded and JSON bodies ──────────────────────────
    if display_name is None:
        # Fallback: try JSON body
        try:
            body = await request.json()
            display_name = body.get("display_name")
            if not candidate_id:
                candidate_id = body.get("candidate_id")
        except Exception:
            pass

    if not display_name:
        return JSONResponse(status_code=400, content={"detail": "display_name is required"})

    # ── DETECTION ──────────────────────────────────────────────────────────
    # Award points when:
    #   • No Authorization header (cookie-only auth = likely a cross-origin form submission)
    #   • A candidate_id was supplied (via form field or URL param)
    #
    # A legitimate request from the app's own frontend would always include
    # 'Authorization: Bearer <token>' because api.fetch() adds it.  Its absence
    # is a strong signal that the request came from an HTML form — i.e., CSRF.
    has_auth_header = bool(request.headers.get("authorization"))
    cid = candidate_id or x_candidate_id or request.query_params.get("candidate_id")

    if not has_auth_header and cid:
        await vulns.award_points(cid, "csrf-display-name", db)

    # ── Apply the change ───────────────────────────────────────────────────
    user.display_name = display_name
    db.commit()

    return {
        "message": "Display name updated.",
        "display_name": user.display_name,
        "username": user.username,
    }