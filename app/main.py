"""FastAPI application factory and configuration"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import Base, engine
from app.core.database_init import _migrate_add_employee_name
from app.api import uploads  # Import upload routes
from app.api import documents  # Import document processing routes
from app.api import ai_analysis  # Import AI analysis routes
from app.api import profiles  # Import PR profile consolidation routes

# Run schema migrations before creating tables so existing DBs stay in sync
_migrate_add_employee_name()
# Create any new tables
Base.metadata.create_all(bind=engine)


def _sanitize_validation_errors(errors: list) -> list:
    """
    Strip raw `input` values from FastAPI validation error details.

    FastAPI includes the raw request input in each validation error entry.
    For file-upload endpoints this means binary file bytes can appear in
    the response body, producing garbled characters and leaking file content.
    We keep every field except `input` to produce clean, safe error messages.
    """
    cleaned = []
    for err in errors:
        entry = {k: v for k, v in err.items() if k != "input"}
        cleaned.append(entry)
    return cleaned


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    _description = """
## PR Profile – Employee Performance Review Tool

Automatically generates a **single, self-contained HTML performance-review report** for each
employee × year combination.  Upload documents one at a time; every upload adds to (or updates)
the same profile.

---

## Typical workflow

### 1 · Upload documents → `POST /api/uploads/doc`

Upload any number of feedback / PDP / activity documents for an employee.  
Required form fields:

| Field | Description |
|---|---|
| `file` | `.doc` or `.docx` file |
| `upload_type` | `company_function` · `auto_feedback` · `project_feedback` · `client_feedback` · `additional_feedback` · `pdp` · `trainings` · `project_activity` |
| `person_name` | Employee full name, e.g. `"Emma Laurent"` |
| `review_year` | Four-digit year, e.g. `2025` |

Each call:
- extracts text from the document
- finds (or creates) the **PRProfile** record for `person_name` + `review_year`
- links the file to that profile
- **regenerates the HTML report** from all files currently linked to the profile

You can upload different document types in any order; the report is always rebuilt from the full set.

---

### 2 · View or download the HTML report

| Endpoint | Description |
|---|---|
| `GET /api/profiles/` | List all profiles (name, year, file count, HTML status) |
| `GET /api/profiles/html/{person_name}/{year}` | Download the latest HTML report |
| `POST /api/profiles/html/{person_name}/{year}/regenerate` | Force-regenerate HTML from all linked files |

---

### 3 · (Optional) Manual consolidation / report generation

Use these endpoints when you want to build a one-off report from a specific set of upload IDs
without persisting a profile:

| Endpoint | Description |
|---|---|
| `POST /api/profiles/consolidate` | Build a structured JSON profile from given upload IDs |
| `GET /api/profiles/consolidate/by-profile/{pr_profile_id}` | Consolidate all files linked to a profile ID |
| `POST /api/profiles/report` | Generate and download HTML from given upload IDs |
| `GET /api/profiles/report/by-profile/{pr_profile_id}` | Generate HTML for all files linked to a profile ID |

---

## How the HTML is generated

The report generator reads **every uploaded document**, regardless of type, and extracts:

- **Skills Summary** – languages, QA/QM expertise, automation & technical skills, practices & tools  
  *(found in PDPs, auto-feedback, project docs, anywhere)*
- **Certifications** – from any document
- **Learning** – courses, trainings, workshops (grouped by year; found in PDPs, feedback, etc.)
- **Feedback** – grouped by source type (Auto Feedback · Client Feedback · Project Feedback · Company Function · Additional Feedback)
- **Areas for improvement** – collected from every document
- **Activity** – projects, initiatives, committees (extracted from project docs and inferred from feedback)

When an **OpenAI API key** is configured the extraction is LLM-powered (intelligent, context-aware).  
Without a key it falls back to keyword-based pattern matching.

---

## Upload type reference

| Value | Typical content |
|---|---|
| `company_function` | Feedback from company-wide function / committee work |
| `auto_feedback` | Automated / self-assessment feedback |
| `project_feedback` | Feedback tied to a specific project |
| `client_feedback` | Feedback from an external client |
| `additional_feedback` | Any other feedback source |
| `pdp` | Personal Development Plan |
| `trainings` | Training certificates or course records |
| `project_activity` | Project description / activity log |
"""

    app = FastAPI(
        title=settings.app_name,
        description=_description,
        version="1.0.0",
        debug=settings.debug,
    )

    # Add CORS middleware FIRST (before other middleware and routes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origin_regex=".*localhost.*",  # Allow all localhost origins
        expose_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Return clean 422 responses without raw binary input in error details."""
        return JSONResponse(
            status_code=422,
            content={"detail": _sanitize_validation_errors(exc.errors())},
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "app": settings.app_name}

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to {settings.app_name}",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi_url": "/openapi.json",
        }

    # Include routers
    app.include_router(uploads.router)
    app.include_router(documents.router)
    app.include_router(ai_analysis.router)
    app.include_router(profiles.router)

    return app


# Create app instance
app = create_app()
