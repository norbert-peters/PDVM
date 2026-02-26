# PDVM_APP_WEB - AI Coding Agent Instructions

## Project Overview
PDVM_APP_WEB is a full-stack web application for data management with user authentication, CRUD operations, and a modern UI. Built with FastAPI backend, React TypeScript frontend, and PostgreSQL database.

**Status**: ✅ Frontend dependencies installed, all TypeScript errors resolved

## Architecture
**Stack**: FastAPI + React + PostgreSQL + JWT Authentication

### Backend (FastAPI)
- **database.py**: SQLAlchemy engine, session management, database initialization
- **tables.py**: ORM models (User, PDVMEntry, AuditLog)
- **schemas.py**: Pydantic models for request/response validation
- **auth.py**: Authentication logic, user retrieval, JWT validation
- **security.py**: Password hashing (bcrypt), JWT token creation/verification
- **main.py**: FastAPI app, routes, CORS middleware

### Frontend (React + TypeScript)
- **client.ts**: Axios API client with auth interceptors
- **Login.tsx**: Login page component
- **Dashboard.tsx**: Main dashboard with system monitoring
- **TableView.tsx**: Sortable, filterable data table
- **App.tsx**: React Router setup with protected routes
- **tsconfig.node.json**: Vite configuration types

### Database
- **schema.sql**: PostgreSQL schema, triggers, sample data
- Uses PostgreSQL 18 with SQLAlchemy ORM

### Key Directories
- `/backend` - FastAPI Python backend
- `/frontend` - React TypeScript frontend (Vite) ✅
- `/database` - SQL schemas and migrations

## Development Workflow

### Setup
Backend:
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env  # Edit with your DB credentials
```

Frontend:
```powershell
cd frontend
npm install
```

Database:
- Create `pdvm_db` in pgAdmin 4
- Execute `database/schema.sql` in Query Tool

### Backend Language**: Python 3.11+
- **Backend Framework**: FastAPI 0.104+
- **Frontend Language**: TypeScript 5.2+
- **Frontend Framework**: React 18.2+ with Vite
- **Database**: PostgreSQL 18
- **ORM**: SQLAlchemy 2.0+

### Code Style
**Python (Backend)**:
- Follow PEP 8
- Use type hints for all function signatures
- Async/await for async operations
- Pydantic models for all API schemas
- SQLAlchemy ORM for database operations
- JWT tokens for authentication
- Bcrypt for password hashing

**TypeScript (Frontend)**:
- Strict TypeScript mode enabled
- Functional components with hooks
- React Router for navigation
- Axios for API calls with interceptors
- CSS modules or separate CSS files per component
- Interface definitions for all props and data models

**File Organization**:
- Backend: One concern per file (auth.py, security.py, etc.)
- Frontend: Component per file with matching CSS
- Database: Centralized in database.py
- Environment variables in .env (never commit)
```powershell
cd frontend
npm run dev  # Runs on http://localhost:3000
```

Docker (Alternative):
```powershell
docker-compose up -d
```

### Testing
- Manual testing via Frontend UI (http://localhost:3000)
- API testing via Swagger UI (http://localhost:8000/docs)
- Database inspection via pgAdmin 4
- Default login: admin / admin123

## Coding Conventions

### Language & Framework
- **Language**: [Specify: Python, JavaScript/TypeScript, etc.]
- **Framework**: [Specify: React, Django, Flask, etc.]
- **Version**: [Specify versions]

### Code Style
[To be completed: Document project-specific patterns]
- Naming conventions
- File organization patterns
- Import/dependency management

### Configuration
- Python environment managed via: **venv** (virtual environment)
- Settings: `.vscode/settings.json` - VS Code workspace configuration
- Backend config: `.env` file (DATABASE_URL, SECRET_KEY)
- Frontend config: `vite.config.ts` (proxy, port)

## Dependencies & Integration

### Backend Dependencies
- fastapi - Web framework
- uvicorn - ASGI server
- sqlalchemy - ORM
- psycopg2-binary - PostgreSQL adapter
- python-jose - JWT handling
- passlib - Password hashing
- pydantic - Data validation
- python-dotenv - Environment variables

### Frontend Dependencies
- react & react-dom - UI library
- react-router-dom - Routing
- axios - HTTP client
- vite - Build tool
- typescript - Type safety

### External Services
- PostgreSQL 18 database (localhost:5432)
- pgAdmin 4 for database management

## Common Patterns

### Authentication Flow
1. User submits credentials to `/api/auth/login`
2. Backend validates and returns JWT token
3. Frontend stores token in localStorage
4. Axios interceptor adds token to all requests
5. Backend validates token via `get_current_user` dependency
6. 401 responses redirect to login page

### API Design
- All API routes prefixed with `/api/`
- Use Pydantic schemas for validation
- Depend on `get_current_active_user` for protected routes
- Return appropriate HTTP status codes
- Use SQLAlchemy sessions via `get_db()` dependency

### Frontend Patterns
- Protected routes check localStorage for token
- API client handles auth automatically
- Components use React hooks (useState, useEffect)
- CSS files match component names
- Error handling with try/catch and user feedback

## Important Notes

### Security
- NEVER commit .env files with real credentials
- SECRET_KEY must be changed in production
- CORS is configured for localhost development
- Passwords are hashed with bcrypt (never stored plain text)
- JWT tokens expire after 30 minutes

### Database
- Schema changes require updating both `tables.py` and `schema.sql`
- Use Alembic for migrations (not yet implemented)
- Foreign keys have CASCADE deletes where appropriate
- Timestamps use timezone-aware TIMESTAMP

### Development
- Backend auto-reloads with uvicorn --reload
- Frontend has HMR via Vite
- API docs auto-generated at /docs
- Default admin user: admin / admin123

### Common Issues
- pgAdmin database corruption → delete pgadmin4.db
- CORS errors → check backend CORS middleware
- Auth errors → verify JWT token and SECRET_KEY
- Database connection → ensure PostgreSQL is running
