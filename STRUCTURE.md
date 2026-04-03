# PR Profile - Complete Project Structure

## 📁 Directory Tree

```
pr-profile/
├── backend/                       # ◄ The running application server
│   ├── app/
│   │   ├── main.py                # FastAPI application factory + lifespan
│   │   ├── api/                   # HTTP route handlers
│   │   │   ├── uploads.py         # POST /api/uploads/doc  (primary upload flow)
│   │   │   ├── profiles.py        # GET/POST /api/profiles/ (list, HTML, regenerate, rename)
│   │   │   ├── documents.py       # POST /api/documents/   (section extraction)
│   │   │   ├── ai_analysis.py     # POST /api/ai/          (on-demand AI analysis)
│   │   │   └── info.py            # GET  /api/info/        (version, health)
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic Settings (reads .env)
│   │   │   ├── constants.py       # UploadType enum, _FEEDBACK_TYPES, MAX_FILE_SIZE_MB
│   │   │   ├── database.py        # SQLAlchemy engine, session factory, get_db()
│   │   │   ├── database_init.py   # Alembic-free schema creation on startup
│   │   │   ├── repositories.py    # Data-access objects (PRProfileRepository, etc.)
│   │   │   ├── security.py        # JWT utilities (not enforced in current build)
│   │   │   ├── error_handler.py   # Centralised exception → HTTP response mapping
│   │   │   └── version.py         # App version string
│   │   ├── models/                # SQLAlchemy ORM models
│   │   │   ├── pr_profile.py      # PRProfile: (employee_name, year, html_report, yoy_analysis)
│   │   │   ├── file.py            # UploadedFile: text, hash, file_type, status
│   │   │   ├── user.py            # User (scaffolded; not enforced)
│   │   │   ├── feedback.py        # Feedback (scaffolded)
│   │   │   ├── project_activity.py
│   │   │   └── function_activity.py
│   │   ├── schemas/               # Pydantic request/response models
│   │   │   ├── file_upload.py     # SmartUploadResponse, UploadTypeEnum, …
│   │   │   ├── profile.py         # ConsolidatedProfileResponse
│   │   │   ├── ai_analysis.py     # SkillAnalysis, AchievementAnalysis, …
│   │   │   └── document_processing.py
│   │   ├── services/              # Business-logic layer
│   │   │   ├── report_generator.py          # HTML report builder (LLM + verbatim feedback)
│   │   │   ├── profile_consolidator.py      # Pattern-based fallback extraction
│   │   │   ├── ai_analyzer.py               # On-demand skill/achievement AI analysis
│   │   │   ├── doc_processor.py             # .doc/.docx → plain text (python-docx / antiword)
│   │   │   ├── document_processor.py        # Section-level extraction from plain text
│   │   │   ├── file_processing_orchestrator.py  # Upload pipeline coordinator
│   │   │   ├── year_over_year_analyzer.py   # LLM year-over-year comparison
│   │   │   └── pdf_processor.py             # PDF stub (not used in current build)
│   │   └── utils/
│   │       ├── file_validation.py   # Magic-byte checks, secure_filename, save helpers
│   │       └── file_upload.py       # FileUploadManager (disk I/O helpers)
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_main.py
│   │   ├── test_upload.py
│   │   ├── test_ai_analyzer.py
│   │   └── test_document_processing.py
│   ├── uploads/                   # Uploaded .docx files saved to disk
│   ├── run.py                     # `python run.py` entry point
│   └── requirements.txt
│
├── app/                           # Mirror of backend/app/ — kept in sync
│   └── …                          # (same structure as backend/app/)
│
├── frontend/                      # React + Vite SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navigation.jsx     # Top nav bar
│   │   │   ├── VersionBadge.jsx   # Displays app version
│   │   │   └── VersionInfo.jsx    # Detailed version info panel
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx      # Profile list, download buttons
│   │   │   ├── SubmitFeedback.jsx # Upload form (name, year, type, file)
│   │   │   └── ViewProfile.jsx    # Inline HTML report preview + download
│   │   ├── services/
│   │   │   └── api.js             # Axios client, all API call helpers
│   │   ├── hooks/
│   │   │   ├── useApi.js          # Generic API call hook
│   │   │   └── useAuth.js         # Auth state (scaffolded)
│   │   ├── App.jsx                # React Router wrapper
│   │   └── main.jsx               # Vite entry point
│   ├── package.json
│   └── vite.config.js             # Dev proxy: /api/* → localhost:8000
│
├── test_docs_comprehensive/       # Test .docx documents for 3 personas
│   ├── 13_Elena_Rodriguez_2025_ClientFeedback.docx
│   ├── 13_Elena_Rodriguez_2025_PDP.docx
│   ├── 13_Elena_Rodriguez_2025_ProjectFeedback.docx
│   ├── 14_James_Park_2025_ClientFeedback.docx
│   ├── 14_James_Park_2025_PDP.docx
│   ├── 14_James_Park_2025_ProjectFeedback.docx
│   ├── 15_Priya_Sharma_2025_ClientFeedback.docx
│   ├── 15_Priya_Sharma_2025_PDP.docx
│   ├── 15_Priya_Sharma_2025_ProjectFeedback.docx
│   └── README.md
│
├── tests/                         # Root-level tests (mirror backend/tests/)
├── .env                           # Local secrets (not committed)
├── .env.example                   # Environment variable template
├── docker-compose.yml             # Backend + SQLite service orchestration
├── Dockerfile                     # Backend container image
├── generate_test_dataset_comprehensive.py  # Generates test .docx files
├── README.md                      # Project documentation
├── STRUCTURE.md                   # This file
└── USER_REQUIREMENTS.md           # Functional requirements specification
```

---

## 🗄️ Database Schema

The database is SQLite by default (`pr_profile.db`). Schema is created automatically on startup via `database_init.py`.

### Key tables

| Table | Primary use |
|---|---|
| **pr_profiles** | One row per `(employee_name, year)`. Stores `html_report` (TEXT) and `yoy_analysis` (TEXT, JSON). |
| **uploaded_files** | One row per uploaded document. Stores `extracted_text`, `file_type` (upload type), `content_hash` (SHA-256 for dedup), `status`. |
| **users** | Scaffolded user accounts (not enforced in current build). |
| **feedback** | Scaffolded feedback records (data stored in `uploaded_files` instead). |
| **project_activities** | Project detail records. |
| **function_activities** | Company function detail records. |

---

## 🌐 API Surface

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/uploads/doc` | **Primary upload**: upload .docx → generate/update HTML |
| `GET` | `/api/profiles/` | List all profiles |
| `GET` | `/api/profiles/html/{name}/{year}` | Download HTML report |
| `POST` | `/api/profiles/html/{name}/{year}/regenerate` | Force regenerate HTML |
| `POST` | `/api/profiles/html/{name}/{year}/rename` | Rename / merge profile |
| `POST` | `/api/documents/process/{upload_id}` | Re-extract sections from an upload |
| `POST` | `/api/documents/bulk-process` | Bulk section extraction |
| `POST` | `/api/ai/analyze/{upload_id}` | On-demand AI skill/achievement analysis |
| `GET` | `/api/ai/skills/{upload_id}` | Get extracted skills |
| `GET` | `/api/ai/achievements/{upload_id}` | Get extracted achievements |

Full interactive documentation: **http://localhost:8000/docs**

---

## 🚀 Frontend Routes

| Route | Component | Purpose |
|---|---|---|
| `/` | Dashboard | List all profiles; download HTML reports |
| `/submit-feedback` | SubmitFeedback | Upload a `.docx` document |
| `/profile/:name/:year` | ViewProfile | Preview HTML report inline; regenerate; rename |

## 📡 API Endpoints (To Be Implemented)

### Profiles
- `GET /api/profiles` - List all profiles
- `GET /api/profiles/{id}` - Get specific profile
- `POST /api/profiles` - Create profile
- `PUT /api/profiles/{id}` - Update profile

### Feedback
- `POST /api/feedback` - Submit feedback (multipart/form-data)
- `GET /api/feedback/{profile_id}` - Get feedback for profile

### Auth (Optional)
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

## 🔧 Environment Variables

See `.env.example` for full list:
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - For AI analysis features
- `SECRET_KEY` - JWT signing key
- `ALLOWED_ORIGINS` - CORS configuration
- `VITE_API_URL` - Backend API URL (frontend)

## 🐳 Docker Services

### PostgreSQL (db)
- Port: 5432
- User: prprofile_user
- Password: prprofile_password
- Database: prprofile_db
- Volume: postgres_data

### FastAPI Backend (backend)
- Port: 8000
- URL: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### React Frontend (frontend)
- Port: 3000
- URL: http://localhost:3000
- Dev server with hot reload

## 📊 Key Features to Implement

### PDF Processing
- Extract data from three feedback forms
- OCR support for scanned documents
- Structured data extraction

### AI Analysis
- Skills summary generation
- Achievement analysis
- Contribution ranking

### Report Generation
- HTML report with all required sections
- Year-over-year comparison
- Interactive visualizations

### User Experience
- Role-based views (employee, manager, colleague)
- File upload and processing
- Report viewing and sharing

## 🧪 Testing

Run tests with:
```bash
cd backend
pytest
```

Uses in-memory SQLite for test database.

## 📝 Development Workflow

1. **Backend Development**: 
   - Modify files in `backend/app/`
   - Tests auto-reload with pytest
   - API docs at `/docs`

2. **Frontend Development**:
   - Modify files in `frontend/src/`
   - Hot reload with Vite
   - Browser opens automatically

3. **Database**:
   - Models in `backend/app/models/`
   - Migrations with Alembic (to be set up)

## 🚢 Deployment

```bash
# Copy environment template
cp .env.example .env

# Update .env with production values
# Key: SECRET_KEY, OPENAI_API_KEY, DATABASE_URL

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 📚 Next Steps

1. ✅ Project structure setup (DONE)
2. ⏳ Implement API routes for profile management
3. ⏳ Build PDF parsing and data extraction services
4. ⏳ Implement AI analysis engine
5. ⏳ Build HTML report generator
6. ⏳ Create comparison and analytics logic
7. ⏳ Complete frontend UI components
8. ⏳ Add authentication and authorization
9. ⏳ Testing and documentation
10. ⏳ Production deployment

