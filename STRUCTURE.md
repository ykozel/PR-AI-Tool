# PR Profile - Complete Project Structure

## 📁 Directory Tree

```
pr-profile/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application factory
│   │   ├── api/                    # API routes (to be implemented)
│   │   │   └── __init__.py
│   │   ├── core/                   # Configuration & utilities
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Settings from environment
│   │   │   ├── database.py         # SQLAlchemy engine & session
│   │   │   └── security.py         # JWT & password utilities
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User (Employee, Manager, Colleague)
│   │   │   ├── pr_profile.py       # Annual PR Profile record
│   │   │   ├── feedback.py         # Feedback from all sources
│   │   │   ├── project_activity.py # Project details
│   │   │   └── function_activity.py# Company function details
│   │   ├── schemas/                # Pydantic request/response models
│   │   │   └── __init__.py
│   │   ├── services/               # Business logic services
│   │   │   └── __init__.py
│   │   └── utils/                  # Utilities
│   │       └── __init__.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py            # Pytest configuration
│   │   └── test_main.py           # Sample tests
│   ├── main.py                    # Application entry point
│   └── requirements.txt           # Python dependencies
│
├── frontend/
│   ├── public/
│   │   └── index.html             # HTML template
│   ├── src/
│   │   ├── components/
│   │   │   └── Navigation.jsx      # App navigation
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx       # Main dashboard
│   │   │   ├── SubmitFeedback.jsx  # Feedback submission
│   │   │   └── ViewProfile.jsx     # Profile view
│   │   ├── services/
│   │   │   └── api.js             # Axios client + API methods
│   │   ├── hooks/
│   │   │   ├── useAuth.js         # Auth state management
│   │   │   └── useApi.js          # API call hook
│   │   ├── styles/                # CSS/SCSS files
│   │   ├── main.jsx               # React entry point
│   │   ├── App.jsx                # App wrapper with routing
│   │   ├── App.css                # Main styles
│   │   └── index.css              # Global styles
│   ├── .env.development           # Dev environment variables
│   ├── .env.production            # Prod environment variables
│   ├── package.json               # Node dependencies & scripts
│   └── vite.config.js             # Vite configuration
│
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── .dockerignore                  # Docker ignore rules
├── Dockerfile                     # Backend container image
├── docker-compose.yml             # Service orchestration
├── README.md                      # Project documentation
└── STRUCTURE.md                   # This file

```

## 🗄️ Database Schema

### Tables
- **users**: Employee, Manager, Colleague accounts
  - Roles: employee, manager, colleague
  
- **pr_profiles**: Annual performance review records
  - Links to users (employee_id)
  - Year-based records
  
- **feedback**: Feedback from all three sources
  - Sources: project, self, function
  - Contains all obligatory sections
  - Submitted by different users
  
- **project_activities**: Project-specific data
  - Project name, responsibilities, contributions
  
- **function_activities**: Company function data
  - Function name, activities, contributions

## 🚀 Frontend Routes

| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | Dashboard | Main page, list profiles |
| `/submit-feedback` | SubmitFeedback | Upload PDF feedback forms |
| `/profile/:year` | ViewProfile | View annual PR profile |

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

