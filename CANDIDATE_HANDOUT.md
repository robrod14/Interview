# Interview Candidate Handout

## Scenario
You are a security engineer tasked with performing a penetration test on a new SaaS application "SaaSify". The application is in early beta and the developers have prioritized features over security.

Your goal is to identify and exploit as many vulnerabilities as possible within the 80-minute session.

## Scope
- **Target URL:** `http://localhost:3000` (Frontend), `http://localhost:8000` (API)
- **In Scope:** All endpoints under `/api`.
- **Out of Scope:** Denial of Service, Brute Force (unless logical bypass), Physical attacks.

## Credentials
You have been provided with a test account for "Tenant A":
- **Username:** `user_a`
- **Password:** `password_a`

There is another tenant "Tenant B" (`user_b`) and an Administrator (`admin`) on the system.

## Instructions
1. Open the application in your browser.
2. Enter your Name/ID to start the session.
3. Log in with the provided credentials.
4. Explore the application and API.
5. When you successfully exploit a vulnerability, the system will automatically detect it and award you points (displayed in the top right).

## Categories to Look For
- Injection (SQL, Command, etc.)
- Broken Access Control (IDOR, Privilege Escalation)
- Cryptographic Failures (JWT issues)
- Server-Side Request Forgery (SSRF)
- Cross-Site Scripting (XSS)

## Tools
- You may use Burp Suite, Postman, or any other standard tools.
- API Documentation might not be fully available, so exploration is key.
- Review the Network tab in your browser to understand the API.

Good luck!
