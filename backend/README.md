# PR Profile

Automated **employee performance-review profile generator**.  
Upload `.doc` / `.docx` feedback documents one at a time; the system extracts all content, analyses it with AI (or keyword patterns), and keeps a single self-contained **HTML report** up-to-date for each employee × review-year combination.

---

## Running the application

The project has two parts that must both be running:

| Part | Directory | Default URL |
|---|---|---|
| **Backend** (FastAPI) | `backend/` | `http://localhost:8000` |
| **Frontend** (React / Vite) | `frontend/` | `http://localhost:3000` |

### 1 · Start the backend

```powershell
cd backend
pip install -r requirements.txt   # first time only
uvicorn app.main:app --reload
```

> **Alternative:** `python run.py`

The API will be live at `http://localhost:8000`.  
The auto-generated Swagger UI (useful for testing without the frontend) is at `http://localhost:8000/docs`.

---

### 2 · Start the frontend

```powershell
cd frontend
npm install        # first time only
npm run dev
```

Open **http://localhost:3000** in your browser.

The Vite dev server automatically proxies every `/api/*` request to the backend on port 8000, so the two processes communicate without any extra configuration.

#### What you can do in the UI

| Page | URL | Actions |
|---|---|---|
| **Profiles list** | `http://localhost:3000/` | See all employee profiles; download any HTML report |
| **Upload** | `http://localhost:3000/submit-feedback` | Upload a `.doc`/`.docx` file — choose the employee name, review year and document type; the report is generated automatically after upload |
| **Profile detail** | `http://localhost:3000/profile/<name>/<year>` | Preview the generated HTML report inline; download it; force-regenerate it from all linked documents; rename the employee |

#### Troubleshooting

| Symptom | Fix |
|---|---|
| "Request failed with status code 500" on page load | The backend is running but the database schema is outdated. Restart the backend — migrations run automatically on startup. |
| `ERR_CONNECTION_REFUSED` on `/api/*` calls | The backend is not running. Start it first with `uvicorn app.main:app --reload`. |
| Port 3000 already in use | `npm run dev -- --port 3001` (or any free port). |
| Port 8000 already in use | `uvicorn app.main:app --reload --port 8001` and update `vite.config.js` proxy target accordingly. |

---

### 3 · Production build (optional)

To build the frontend as static files (e.g. to serve behind nginx):

```powershell
cd frontend
npm run build          # output goes to frontend/dist/
npm run preview        # local preview of the production build on http://localhost:4173
```

---

## How it works

```
Upload doc (person_name, review_year, upload_type)
        │
        ▼
  Text extraction  ──────────────────────────────────────┐
        │                                                 │
        ▼                                                 │
  Find / create PRProfile(person_name, year)             │
        │                                                 │
        ▼                                                 │
  Link file → PRProfile                                  │
        │                                                 │
        ▼                                                 │
  Collect ALL files for this profile ◄────────────────── ┘
        │
        ▼
  AI analysis  (OpenAI GPT if OPENAI_API_KEY is set;
                keyword patterns otherwise)
        │
        ├── Skills Summary  (from every document)
        ├── Certifications  (from every document)
        ├── Learning        (from every document)
        ├── Feedback        (grouped by upload type; numbered if duplicates)
        ├── Areas for improvement (from every document)
        └── Activity        (from project docs + inferred from feedback)
        │
        ▼
  Store HTML in PRProfile.html_report  (created / overwritten)
```

- **First upload** for a person+year → creates the profile and generates the HTML.
- **Each subsequent upload** → text is extracted, HTML is regenerated from **all** files linked to that profile.
- If a second `client_feedback` document is uploaded it appears as a separate **Client Feedback 2** subsection in the report.

---

## Example user flow: generate an HTML report from a PDP + client feedback

This walkthrough shows how to build a complete performance-review HTML for **Emma Laurent**, review year **2025**, using two documents: a Personal Development Plan and a client feedback letter.

**Endpoints used in this example:**

| Action | Endpoint |
|---|---|
| Upload a document | `POST http://localhost:8000/api/uploads/doc` |
| Download the HTML report | `GET  http://localhost:8000/api/profiles/html/Emma%20Laurent/2025` |
| List all profiles | `GET  http://localhost:8000/api/profiles/` |
| Force-regenerate HTML | `POST http://localhost:8000/api/profiles/html/Emma%20Laurent/2025/regenerate` |

> You can also try all endpoints interactively in the Swagger UI at **http://localhost:8000/docs**.

### Step 1 – Upload the PDP

```bash
curl -X POST http://localhost:8000/api/uploads/doc \
  -F "file=@Emma_Laurent_PDP_2025.docx" \
  -F "upload_type=pdp" \
  -F "person_name=Emma Laurent" \
  -F "review_year=2025"
```

Response:

```json
{
  "upload_id": 1,
  "pr_profile_id": 1,
  "employee_name": "Emma Laurent",
  "review_year": 2025,
  "files_in_profile": 1,
  "html_updated": true,
  "message": "Uploaded 'Emma_Laurent_PDP_2025.docx' for Emma Laurent (2025). HTML profile updated."
}
```

The system:
- Extracts text from the PDP
- Creates a new **PRProfile** for Emma Laurent / 2025
- Parses the PDP for skills, planned courses, certifications, and any development goals
- Generates the first version of the HTML report (Skills Summary, Learning, and Certifications sections will be populated)

---

### Step 2 – Upload the client feedback

```bash
curl -X POST http://localhost:8000/api/uploads/doc \
  -F "file=@Emma_Laurent_Client_Feedback_2025.docx" \
  -F "upload_type=client_feedback" \
  -F "person_name=Emma Laurent" \
  -F "review_year=2025"
```

Response:

```json
{
  "upload_id": 2,
  "pr_profile_id": 1,
  "employee_name": "Emma Laurent",
  "review_year": 2025,
  "files_in_profile": 2,
  "html_updated": true,
  "message": "Uploaded 'Emma_Laurent_Client_Feedback_2025.docx' for Emma Laurent (2025). HTML profile updated."
}
```

The system:
- Extracts text from the client feedback document
- Reuses the **same PRProfile** (id 1) – no duplicate is created
- Re-analyses **both documents together**: skills mentioned in the client feedback are added to the Skills Summary, any projects referenced go into Activity, improvement notes go into Areas for Improvement
- Adds a **Client Feedback** subsection under the Feedback section in the HTML
- **Overwrites** the stored HTML with the updated report

---

### Step 3 – Download the HTML report

```bash
curl "http://localhost:8000/api/profiles/html/Emma%20Laurent/2025" \
  -o "Emma_Laurent_2025_PR.html"
```

Or with Python:

```python
import requests

r = requests.get("http://localhost:8000/api/profiles/html/Emma Laurent/2025")
with open("Emma_Laurent_2025_PR.html", "wb") as f:
    f.write(r.content)
```

Open `Emma_Laurent_2025_PR.html` in any browser. The report contains:

| Section | What it contains after these two uploads |
|---|---|
| **Skills Summary** | Technical skills and languages extracted from both the PDP and the client feedback |
| **Certifications** | Certifications listed or pursued in the PDP |
| **Learning** | Courses and trainings from the PDP, grouped by year |
| **Feedback › Client Feedback** | Quotes and paraphrases from the client feedback document |
| **Areas for improvement** | Development goals from the PDP + any gaps noted in the client feedback |
| **Activity** | Projects referenced in the client feedback |

---

### Step 4 – Add more documents at any time

Upload additional feedback documents in the same way. Each upload incrementally updates the same HTML:

```bash
# Add a second client feedback (becomes "Client Feedback 2" in the report)
curl -X POST http://localhost:8000/api/uploads/doc \
  -F "file=@Emma_Laurent_Client_Feedback_Q4_2025.docx" \
  -F "upload_type=client_feedback" \
  -F "person_name=Emma Laurent" \
  -F "review_year=2025"

# Add auto-feedback
curl -X POST http://localhost:8000/api/uploads/doc \
  -F "file=@Emma_Laurent_Auto_Feedback_2025.docx" \
  -F "upload_type=auto_feedback" \
  -F "person_name=Emma Laurent" \
  -F "review_year=2025"
```

After each upload the HTML at `GET /api/profiles/html/Emma Laurent/2025` reflects all documents uploaded so far.

---

## Quick start

### Prerequisites

```
Python 3.10+
Node.js 18+
pip / npm
```

### Install – backend

```bash
cd backend
pip install -r requirements.txt
```

### Install – frontend

```bash
cd frontend
npm install
```

### Configure (optional)

Create a `.env` file in this directory:

```env
# LLM-powered extraction (optional – falls back to keyword patterns without it)
OPENAI_API_KEY=sk-...
AI_MODEL=gpt-4

# Database (SQLite is used by default – no extra setup needed)
DATABASE_URL=sqlite:///./pr_profile.db

# PostgreSQL example
# DATABASE_URL=postgresql+psycopg2://user:password@localhost/pr_profile
```

### Run – backend

```bash
cd backend
uvicorn app.main:app --reload
# or
python run.py
```

The API is available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Run – frontend (UI)

```bash
cd frontend
npm run dev
```

The UI is available at **http://localhost:3000**.

> The Vite dev server proxies all `/api/*` requests to `http://localhost:8000`, so
> the backend must be running first.

#### UI pages

| Page | URL | What you can do |
|---|---|---|
| **Profiles** | `http://localhost:3000/` | View all employee profiles, download HTML reports |
| **Upload** | `http://localhost:3000/submit-feedback` | Upload a `.doc`/`.docx` document with employee name, year and document type |
| **Profile detail** | `http://localhost:3000/profile/<name>/<year>` | Preview the generated HTML report, regenerate it, rename the employee |

#### Production build

```bash
cd frontend
npm run build        # outputs to frontend/dist/
npm run preview      # serve the production build locally
```

---

## Key endpoints

### Upload a document

```
POST /api/uploads/doc
Content-Type: multipart/form-data
```

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | ✓ | `.doc` or `.docx` file |
| `upload_type` | string | ✓ | See upload type reference below |
| `person_name` | string | ✓ | Employee full name, e.g. `Emma Laurent` |
| `review_year` | integer | ✓ | Four-digit year, e.g. `2025` |
| `uploaded_by_email` | string | | Email of the uploader (optional) |

**Example (curl):**

```bash
curl -X POST http://localhost:8000/api/uploads/doc \
  -F "file=@Emma_Laurent_Auto_Feedback_2025.docx" \
  -F "upload_type=auto_feedback" \
  -F "person_name=Emma Laurent" \
  -F "review_year=2025"
```

**Example (Python requests):**

```python
import requests

with open("Emma_Laurent_Auto_Feedback_2025.docx", "rb") as f:
    r = requests.post(
        "http://localhost:8000/api/uploads/doc",
        files={"file": ("auto_feedback.docx", f)},
        data={
            "upload_type": "auto_feedback",
            "person_name": "Emma Laurent",
            "review_year": 2025,
        },
    )
print(r.json())
```

**Response:**

```json
{
  "upload_id": 7,
  "pr_profile_id": 3,
  "employee_name": "Emma Laurent",
  "review_year": 2025,
  "files_in_profile": 3,
  "html_updated": true,
  "message": "Uploaded 'auto_feedback.docx' for Emma Laurent (2025). HTML profile updated."
}
```

---

### Download the HTML report

```
GET http://localhost:8000/api/profiles/html/{person_name}/{year}
```

> **Quick browser download:** open the URL directly in your browser, e.g.
> `http://localhost:8000/api/profiles/html/Emma%20Laurent/2025`  
> The browser will prompt you to save (or open) the HTML file.

Returns the latest self-contained HTML report as a downloadable file.
Spaces in the name must be URL-encoded as `%20`.

**Example (curl):**

```bash
curl "http://localhost:8000/api/profiles/html/Emma%20Laurent/2025" \
  -o "Emma_Laurent_2025_PR.html"
```

**Example (Python requests):**

```python
import requests

r = requests.get("http://localhost:8000/api/profiles/html/Emma%20Laurent/2025")
with open("Emma_Laurent_2025_PR.html", "wb") as f:
    f.write(r.content)
```

Open the saved file in any browser – no external dependencies.

---

### List all profiles

```
GET /api/profiles/
```

Returns a JSON array of all person+year profiles:

```json
[
  {
    "id": 3,
    "employee_name": "Emma Laurent",
    "year": 2025,
    "has_html": true,
    "files": 3
  }
]
```

---

### Force-regenerate HTML

```
POST /api/profiles/html/{person_name}/{year}/regenerate
```

Re-runs the full extraction and report generation from all currently linked files and updates the stored HTML.

---

## Upload type reference

| Value | Typical content |
|---|---|
| `company_function` | Feedback from company-wide function or committee work |
| `auto_feedback` | Automated / self-assessment feedback |
| `project_feedback` | Feedback tied to a specific project |
| `client_feedback` | Feedback from an external client |
| `additional_feedback` | Any other feedback source |
| `pdp` | Personal Development Plan |
| `trainings` | Training certificates or course records |
| `project_activity` | Project description or activity log |

Multiple uploads of the same type for the same person+year are each given their own numbered subsection in the HTML report (e.g. **Client Feedback**, **Client Feedback 2**, **Client Feedback 3**).

---

## HTML report sections

| Section | Source documents |
|---|---|
| **Skills Summary** | All documents (PDP, feedback, project docs, everything) |
| **Certifications** | All documents |
| **Learning** | All documents (grouped by year) |
| **Feedback** | Feedback-type documents, one subsection per upload |
| **Areas for improvement** | All documents |
| **Activity** | Project docs + inferred from feedback |

---

## Project structure

```
pr-profile/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── uploads.py        # POST /api/uploads/doc  (main upload endpoint)
│   │   │   ├── profiles.py       # GET /api/profiles/html/...  (HTML retrieval)
│   │   │   ├── documents.py      # Document processing helpers
│   │   │   └── ai_analysis.py    # AI analysis endpoints
│   │   ├── core/
│   │   │   ├── config.py         # Settings (env vars)
│   │   │   ├── database.py       # SQLAlchemy engine / session
│   │   │   ├── database_init.py  # Table creation + migrations
│   │   │   └── repositories.py   # PRProfileRepository, UploadedFileRepository
│   │   ├── models/
│   │   │   ├── pr_profile.py     # PRProfile table (employee_name, year, html_report)
│   │   │   └── file.py           # UploadedFile table
│   │   ├── services/
│   │   │   ├── report_generator.py    # HTML generation (LLM + pattern fallback)
│   │   │   ├── profile_consolidator.py# Pattern-based section extraction
│   │   │   ├── doc_processor.py       # .doc/.docx → plain text
│   │   │   └── ai_analyzer.py         # Keyword-based skill/achievement analysis
│   │   └── schemas/
│   │       └── file_upload.py    # Pydantic request/response models
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Dashboard.jsx      # Profiles list with download buttons
    │   │   ├── SubmitFeedback.jsx # Upload form (drag-and-drop)
    │   │   └── ViewProfile.jsx    # Report preview, regenerate, rename
    │   ├── services/
    │   │   └── api.js             # All API calls (axios)
    │   └── components/
    │       └── Navigation.jsx
    ├── index.html
    ├── vite.config.js             # Dev proxy: /api → localhost:8000
    └── package.json
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(unset)* | Enables LLM-powered extraction; falls back to pattern matching without it |
| `AI_MODEL` | `gpt-4` | OpenAI model to use |
| `DATABASE_URL` | `sqlite:///./pr_profile.db` | SQLAlchemy connection string |
| `DEBUG` | `false` | Enable FastAPI debug mode |
| `MAX_FILE_SIZE` | `50` | Maximum upload file size in MB |
