# PR Profile

Upload `.doc` / `.docx` feedback documents and get a self-contained **HTML performance-review report** per employee per year, generated (and incrementally updated) by AI.

---

## Requirements

- **Python 3.14.3**
- **Node.js 18+**

---

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `backend/.env` file:

```env
OPENAI_API_KEY=sk-...          # required for AI analysis; falls back to keyword patterns without it
AI_MODEL=gpt-4o
DATABASE_URL=sqlite:///./pr_profile.db   # default; change to PostgreSQL for production
```

### Frontend

```bash
cd frontend
npm install
```

---

## Running

Start both processes in separate terminals:

```bash
# Terminal 1  backend
cd backend
uvicorn app.main:app --reload
# API at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

```bash
# Terminal 2  frontend
cd frontend
npm run dev
# UI at http://localhost:3000
```

The Vite dev server proxies all `/api/*` calls to the backend automatically.

---

## Common user flow

1. **Open** `http://localhost:3000/submit-feedback`
2. **Upload** a `.docx` file  set employee name, review year, and document type (e.g. `pdp`, `client_feedback`)
3. The backend extracts text, runs AI analysis, and generates or updates the HTML report
4. **Repeat** for additional documents for the same employee+year  each upload re-analyses all documents together and updates the report
5. **View** the report at `http://localhost:3000/profile/<name>/<year>`  preview inline, download, or force-regenerate
6. **Year-over-year**: when documents exist for multiple years for the same employee, the report includes navigation between years and an AI-generated achievements comparison section

### Document types

| Value | Content |
|---|---|
| `pdp` | Personal Development Plan |
| `auto_feedback` | Self-assessment |
| `project_feedback` | Project-specific feedback |
| `client_feedback` | External client feedback |
| `company_function` | Committee / function feedback |
| `additional_feedback` | Any other source |
| `trainings` | Training certificates or course records |
| `project_activity` | Project description or activity log |

Multiple uploads of the same type appear as numbered subsections (e.g. **Client Feedback**, **Client Feedback 2**).

### Report sections

| Section | Source |
|---|---|
| Skills Summary | All documents |
| Certifications | All documents |
| Learning | All documents |
| Feedback | Feedback-type documents, one subsection per upload |
| Areas for Improvement | All documents |
| Activity | Project docs + inferred from feedback |
| Year-over-Year Achievements | AI comparison with previous year (when available) |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| 500 on page load | Restart the backend  DB migrations run automatically on startup |
| `ERR_CONNECTION_REFUSED` on `/api/*` | Backend is not running  start it first |
| Port conflict | Backend: `uvicorn app.main:app --reload --port 8001` (update `vite.config.js` proxy target). Frontend: `npm run dev -- --port 3001` |
