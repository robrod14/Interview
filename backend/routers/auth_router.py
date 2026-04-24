from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Any, Dict, Optional
import hashlib

from .. import database, models, auth, schemas, vulns

router = APIRouter()

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID")
):
    # VULNERABLE LOGIN implementation
    # We use raw SQL string concatenation
    username = form_data.username
    password = form_data.password
    
    # Try to find user with SQL Injection vulnerability
    # We select * from users where username = '$username'
    # This allows ' OR '1'='1 -- type attacks
    
    query = f"SELECT * FROM users WHERE username = '{username}'"
    
    try:
        result = db.execute(text(query)).first()
    except Exception as e:
        # If SQL syntax error, might be blind SQLi attempt?
        # But we want login bypass.
        raise HTTPException(status_code=400, detail="Invalid Query")

    user = None
    is_sqli_success = False

    if result:
        # Map result to User object
        # Columns: id, username, hashed_password, role, tenant_id, api_key
        # Note: result keys depend on DB driver, usually they are accessible by name
        user = db.query(models.User).filter(models.User.id == result.id).first()
        
        # Check password
        if not auth.verify_password(password, user.hashed_password):
            # Password mismatch, BUT we got a user from the query.
            # This implies the WHERE clause was satisfied without the password (if we checked password in SQL)
            # OR the user injected a username that exists but didn't provide password.
            # Wait, usually login SQL is: SELECT * FROM users WHERE username = '...' AND password = '...'
            # But here we are fetching by username then checking hash.
            # So standard SQLi in username just lets you enumerate users?
            # Unless... we want to allow bypassing the PASSWORD check?
            # If the SQL was: "SELECT * FROM users WHERE username = '{u}' AND password = '{p}'"
            # Then ' OR '1'='1 would return the first user (admin).
            pass
    
    # Let's redo the vulnerability to be more classic "Login Bypass"
    # Query: SELECT * FROM users WHERE username = '{username}' AND password = '{password}' (if we stored plain text?)
    # But we store hashes.
    # So we can't easily do SQLi to bypass password check if we verify hash in python code.
    # UNLESS we treat the query result as authoritative.
    # i.e. "If DB returns a user, log them in."
    
    # So, let's pretend we have a legacy "login_query" that checks both?
    # Or, maybe we just vulnerability in the username lookup?
    # "SELECT * FROM users WHERE username = '{username}'"
    # If I input "admin' --", I get the admin user.
    # Then I still need to verify password.
    # If I don't know the password, I fail.
    
    # To allow bypass, the code must be:
    # if result: login(result)
    
    # So I will skip password verification if it looks like an injection? No, that's cheating.
    # I will verify password, BUT if the password check fails, I will check if it was an injection?
    
    # Correct implementation of SQLi Login Bypass (where hash is involved):
    # Usually you can't bypass hash verification with SQLi unless you can extract the hash or change the query to return a known hash.
    # OR, the code doesn't verify the hash properly.
    
    # Let's change the vuln: "Blind SQL Injection" to extract data?
    # Or "Login as another user" if you know the username?
    # If I enter "admin", I get admin user. I still need password.
    
    # Alternative: The app uses a "magic" password or "master" password that is checked in SQL?
    # No.
    
    # Let's try this:
    # The query is: "SELECT * FROM users WHERE username = '{username}'"
    # If I do "admin' UNION SELECT 1, 'admin', 'knownhash', ... --"
    # Then I can inject a fake user with a known password hash!
    # YES.
    
    # So if they inject a UNION SELECT, they can return a row that looks like a user, with a password hash of their choice.
    # Then `auth.verify_password` will match the known password.
    # And they get a token for 'admin'.
    
    # Detection:
    # If the user.id returned does NOT exist in the real `users` table?
    # Or if the returned user has `id` but `db.query(User).get(id)` is different?
    
    if result:
        # If it's a real user from DB
        real_user = db.query(models.User).filter(models.User.username == result.username).first()
        
        # 1. Normal Login Check
        if real_user and auth.verify_password(password, real_user.hashed_password):
            access_token = auth.create_access_token(
                data={"sub": real_user.username, "role": real_user.role, "tenant_id": real_user.tenant_id}
            )
            return {"access_token": access_token, "token_type": "bearer"}
        
        # 2. SQLi Bypass Check (The "Classic" OR 1=1 Bypass)
        # If the user injected something like "admin' --", the query becomes:
        # SELECT * FROM users WHERE username = 'admin' --'
        # This returns the admin user row.
        #
        # If we want to allow bypassing the password check simply by manipulating the query to return a user,
        # we check if the query result (username) matches what was returned, 
        # AND we detect that the password check failed.
        #
        # However, to avoid "accidental" logins (e.g. typing wrong password for admin shouldn't just log you in),
        # we need a heuristic. 
        #
        # SIMPLIFICATION FOR INTERVIEW:
        # If the user injects a comment char '--' or a quote "'", we assume they are trying to bypass.
        # If the DB returned a user, and the input contains SQLi chars, we let them in!
        
        is_sqli_attempt = "'" in username or "--" in username or "OR" in username.upper()
        
        if is_sqli_attempt:
             # ATTACK SUCCESSFUL
            if x_candidate_id:
                await vulns.award_points(x_candidate_id, "sqli-login", db)
            
            # Log them in as the user returned by the query
            role = getattr(result, 'role', 'user')
            tenant_id = getattr(result, 'tenant_id', 1)
            
            access_token = auth.create_access_token(
                data={"sub": result.username, "role": role, "tenant_id": tenant_id}
            )
            return {"access_token": access_token, "token_type": "bearer"}
        
        # 3. UNION-based Check (keep existing logic just in case)
        if auth.verify_password(password, result.hashed_password):
            # This means they injected a row with a valid hash for the provided password!
            # ATTACK SUCCESSFUL
            if x_candidate_id:
                await vulns.award_points(x_candidate_id, "sqli-login", db)
            
            # Return token for the "injected" user claims
            # Use real_user data if available (to allow actual access) or use result data
            # If they injected 'admin', we give them admin token.
            # If they injected a fake user that doesn't exist, the token might not work for DB lookups later.
            # So usually they want to impersonate 'admin'.
            # If they impersonate 'admin', they should provide admin's username.
            
            # If `real_user` exists (e.g. they targeted 'admin'), but they bypassed the password check by injecting a row?
            # Wait, `db.execute` returns the row. If they UNION, they return a row.
            # If they do: "admin' AND 1=0 UNION SELECT ... 'admin', 'myhash' ..."
            # Then `result` is their fake row.
            # `real_user` is the actual admin (looked up by username).
            # `verify_password` on `real_user` fails.
            # `verify_password` on `result` succeeds.
            
            # So we issue a token for `result.username` (admin).
            # But the system will treat them as admin.
            
            role = getattr(result, 'role', 'user')
            tenant_id = getattr(result, 'tenant_id', 1)
            
            access_token = auth.create_access_token(
                data={"sub": result.username, "role": role, "tenant_id": tenant_id}
            )
            return {"access_token": access_token, "token_type": "bearer"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.put("/me")
async def update_profile(
    updates: Dict[str, Any],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID")
):
    """
    Update the current user's profile.
    Accepts a JSON body with fields to update.
    
    Intended fields: username, password
    
    VULNERABILITY: Mass Assignment
    The endpoint blindly applies all provided fields to the user model,
    including sensitive fields like 'role', 'tenant_id', and 'api_key'.
    A crafty tester can send {"role": "admin"} to escalate privileges.
    """
    PROTECTED_FIELDS = {"id", "hashed_password"}  # Only truly immutable fields
    
    # VULNERABLE: Detect if the user is trying to escalate role
    if "role" in updates:
        if x_candidate_id:
            await vulns.award_points(x_candidate_id, "mass-assignment-role", db)
    
    # VULNERABLE: Blindly apply all incoming fields to the user object
    for field, value in updates.items():
        if field in PROTECTED_FIELDS:
            continue  # Can't overwrite ID or hashed_password directly
        if field == "password":
            # Hash the new password properly
            current_user.hashed_password = auth.get_password_hash(value)
        elif hasattr(current_user, field):
            # 🚨 MASS ASSIGNMENT: setting role, tenant_id, api_key – whatever they send!
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Profile updated successfully.",
        "username": current_user.username,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id
    }


# ---------------------------------------------------------------------------
# Password Reset  (VULNERABLE)
# ---------------------------------------------------------------------------

class ForgotPasswordRequest(BaseModel):
    username: str

class ResetPasswordRequest(BaseModel):
    username: str
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(database.get_db),
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID")
):
    """
    Initiates a password reset for a given username.

    In a real application this would send an email.  Since there is no mail
    server in this lab the token is returned directly in the JSON response
    as a "debug" convenience.

    VULNERABILITY: Sensitive Data Exposure
    The reset token is included in the HTTP response body, allowing any
    attacker who can make this request to obtain the token for any user and
    then call /reset-password to take over that account without any email
    access.  The token is also cryptographically weak (MD5 of username).
    """
    user = db.query(models.User).filter(models.User.username == request.username).first()

    # Always return the same generic message so usernames can't be enumerated
    # (the REAL vuln is the token in the response, not enumeration)
    generic_msg = "If that username exists a reset token has been generated."

    if not user:
        # Still return 200 to prevent username enumeration — but no token
        return {"message": generic_msg}

    # VULNERABILITY: Weak token — MD5 of just the username
    # A tester who knows this algorithm can generate the token offline without
    # even calling this endpoint.
    weak_token = hashlib.md5(request.username.encode()).hexdigest()

    # Invalidate any previous token for this user
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.username == request.username
    ).delete()

    db_token = models.PasswordResetToken(username=request.username, token=weak_token)
    db.add(db_token)
    db.commit()

    # VULNERABILITY: Token returned in plaintext response — no email required!
    return {
        "message": generic_msg,
        # "dev_note" makes it look like an accidental debug artifact
        "dev_note": "[DEV MODE] Token delivery bypassed. Token: " + weak_token,
    }


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(database.get_db),
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID")
):
    """
    Completes a password reset using a token obtained from /forgot-password.

    Detection: if someone resets the 'admin' account's password the
    pwd-reset-token-leak vulnerability is marked as found.
    """
    reset_record = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.username == request.username,
        models.PasswordResetToken.token == request.token,
        models.PasswordResetToken.used == False,  # noqa: E712
    ).first()

    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    user = db.query(models.User).filter(models.User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # DETECTION: Award points when the admin account is successfully compromised
    if request.username == "admin" and x_candidate_id:
        await vulns.award_points(x_candidate_id, "pwd-reset-token-leak", db)

    user.hashed_password = auth.get_password_hash(request.new_password)
    reset_record.used = True
    db.commit()

    return {"message": "Password reset successfully."}


# ---------------------------------------------------------------------------
# Open Redirect  (VULNERABLE)
# ---------------------------------------------------------------------------

@router.get("/redirect")
async def post_login_redirect(
    next: Optional[str] = None,
    candidate_id: Optional[str] = None,
    x_candidate_id: Optional[str] = Header(None, alias="X-Candidate-ID"),
    db: Session = Depends(database.get_db)
):
    """
    Returns the URL the frontend should navigate to after login.
    Accepts an arbitrary ?next= URL with no validation.

    VULNERABILITY: Open Redirect
    The `next` parameter is not validated against an allowlist.  An attacker
    who crafts a login URL such as:
      /login?next=https://evil.com
    will silently redirect the victim after they authenticate, enabling
    credential phishing or session-token theft.
    """
    safe_default = "/dashboard"
    redirect_target = next if next else safe_default

    # Accept candidate ID from either header OR query param
    # (query param needed because this is called from window.location flow)
    cid = x_candidate_id or candidate_id

    # DETECTION: external URL supplied as next
    is_external = (
        redirect_target.startswith("http://") or
        redirect_target.startswith("https://")
    ) and "localhost" not in redirect_target and "127.0.0.1" not in redirect_target

    if is_external and cid:
        await vulns.award_points(cid, "open-redirect-login", db)

    # Return JSON so the frontend can use api.fetch() and include auth headers
    # The frontend then does window.location.href = data.redirect_to
    # This keeps the X-Candidate-ID flow working while still being exploitable
    return {"redirect_to": redirect_target}
