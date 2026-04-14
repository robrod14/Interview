# Vulnerable SaaS Application - Maintainer Guide

## Overview
This application is designed for a penetration testing interview. It contains multiple vulnerabilities that candidates are expected to find.

## Running the Application
### Backend
1. `cd backend`
2. `python3 -m pip install -r requirements.txt`
3. `cd ..` (Go back to project root)
4. `python3 -m backend.seed` (Reset/Seed Database)
5. `uvicorn backend.main:app --reload --port 8000`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## Vulnerabilities & Solutions

| ID | Vulnerability | Endpoint | Method | Difficulty | Points |
|----|--------------|----------|--------|------------|--------|
| `sqli-login` | SQL Injection (Login) | `/api/auth/token` | POST | Easy | 100 |
| `idor-invoice` | IDOR (Invoices) | `/api/invoices/{id}` | GET | Easy | 100 |
| `stored-xss-note` | Stored XSS | `/api/notes/` | POST | Medium | 150 |
| `broken-auth-jwt` | JWT 'none' Algorithm | `/api/admin/users` | GET | Medium | 200 |
| `ssrf-avatar` | SSRF | `/api/misc/fetch-avatar` | POST | Hard | 250 |

### 1. SQL Injection (Login Bypass)
- **Endpoint:** `POST /api/auth/token`
- **Parameter:** `username`
- **Exploit:** `' OR '1'='1` or `admin' --` (if you know the username) or `admin' UNION SELECT ...`
- **Detection:** The backend checks if the query returns a result that has a password hash matching the input, OR if the user manages to inject a fake user row via UNION.
- **Goal:** Log in as `admin` without knowing the password.
- **Payload Example:** Username: `admin' --`, Password: `any` (might fail if password check is strict). 
- **Better Payload:** `admin' UNION SELECT 1, 'admin', 'known_hash', 'admin', 1, 'key' --` (Requires guessing columns).
- **Simplest Path:** The code allows bypass if the injected row has a matching hash. The current implementation is a bit complex, but essentially if you can inject a row, you can login.

### 2. IDOR (Invoices)
- **Endpoint:** `GET /api/invoices/{id}`
- **Exploit:** Change the `id` in the URL to an ID belonging to another tenant (e.g., `2`).
- **Detection:** Backend checks if the requested invoice tenant_id != current user tenant_id.
- **Goal:** View invoice #2 (Tenant B's invoice) while logged in as User A.

### 3. Stored XSS (Notes)
- **Endpoint:** `POST /api/notes/`
- **Exploit:** Submit a note with `<script>alert(1)</script>` or `<img src=x onerror=alert(1)>`.
- **Detection:** Backend regex matches common XSS patterns in the content upon submission.
- **Goal:** Store a malicious script.

### 4. JWT 'none' Algorithm
- **Endpoint:** `GET /api/admin/users` (or any admin protected endpoint)
- **Exploit:**
  1. Capture a valid token.
  2. Decode the header and change `"alg": "HS256"` to `"alg": "none"`.
  3. Remove the signature part (leave the trailing dot).
  4. Change payload `"role": "user"` to `"role": "admin"`.
  5. Send request with modified token.
- **Detection:** Backend explicitly checks if `alg` is `none` and if so awards points.
- **Goal:** Access the admin-only user list.

### 5. SSRF (Avatar Fetch)
- **Endpoint:** `POST /api/misc/fetch-avatar`
- **Exploit:** Provide a URL pointing to `http://localhost:8000/api/admin/internal-config` or `http://127.0.0.1:8000...`.
- **Detection:** Backend checks if the URL targets localhost/127.0.0.1 and specifically the internal config path.
- **Goal:** Read the internal configuration secret.

## Scoring System
- The app automatically awards points when these conditions are met.
- Frontend listens to SSE at `/api/session/events` to show notifications.
- Admin can view scoreboard at `/api/scoreboard/{session_id}` (or implement a page for it).

## Reset
- Run `python3 -m backend.seed` to wipe the DB and re-seed.
- Use the admin "Reset Lab" button (if implemented in UI) or endpoint `/api/admin/reset-lab`.
