# Vulnerable SaaS App (Interview Lab)

This is a self-contained, vulnerable web application designed for conducting technical interviews for security engineering roles.

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+

### Setup & Run

1. **Backend:**
   ```bash
   # Install dependencies
   cd backend
   python3 -m pip install -r requirements.txt
   
   # Run app (from project root)
   cd ..
   python3 -m backend.seed
   uvicorn backend.main:app --reload --port 8000
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open http://localhost:3000

## Documentation
- [Maintainer Guide](./MAINTAINER_GUIDE.md) - **Contains Spoilers/Solutions**
- [Candidate Handout](./CANDIDATE_HANDOUT.md) - Give this to the candidate.

## Architecture
- **Backend:** FastAPI, SQLite, SQLAlchemy.
- **Frontend:** Next.js (App Router), TailwindCSS.
- **Auth:** JWT (Custom implementation for vulnerability).

## Features
- Automated scoring system via Server-Side Events.
- Real-time feedback for candidates.
- "SaaS" style dashboard.
