# PDVM Web Application - Quick Start Guide

## Overview
PDVM_APP_WEB is a modern full-stack web application with:
- **Backend**: FastAPI (Python) with PostgreSQL database
- **Frontend**: React with TypeScript
- **Database**: PostgreSQL 18
- **Authentication**: JWT tokens with bcrypt password hashing

## Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 18
- pgAdmin 4 (optional, for database management)

## Project Structure
```
PDVM_APP_WEB/
├── backend/              # FastAPI backend
│   ├── main.py          # Main application entry point
│   ├── database.py      # Database connection and session management
│   ├── tables.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── auth.py          # Authentication logic
│   ├── security.py      # Password hashing and JWT utilities
│   ├── requirements.txt # Python dependencies
│   └── .env.example     # Environment variables template
├── frontend/            # React frontend
│   ├── src/
│   │   ├── App.tsx      # Main React component with routing
│   │   ├── Login.tsx    # Login page
│   │   ├── Dashboard.tsx # Main dashboard
│   │   ├── TableView.tsx # Data table component
│   │   └── client.ts    # API client
│   ├── package.json     # Node.js dependencies
│   └── vite.config.ts   # Vite configuration
├── database/
│   └── schema.sql       # Database schema and initial data
└── docker-compose.yml   # Docker setup (optional)
```

## Setup Instructions

### 1. Database Setup (pgAdmin)

#### Create Database in pgAdmin:
1. Open pgAdmin 4
2. Connect to your PostgreSQL 18 server (localhost)
3. Right-click on "Databases" → "Create" → "Database..."
4. Database name: `pdvm_db`
5. Owner: `postgres`
6. Click "Save"

#### Run Schema:
1. Right-click on `pdvm_db` → "Query Tool"
2. Open `database/schema.sql`
3. Execute the SQL script (F5)
4. This creates tables and inserts sample data

### 2. Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env

# Edit .env with your database credentials
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/pdvm_db
```

#### Start Backend:
```powershell
# Make sure you're in the backend directory with venv activated
python main.py
```
Backend runs on: http://localhost:8000
API docs: http://localhost:8000/docs

### 3. Frontend Setup

```powershell
# Open new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend runs on: http://localhost:3000

## Default Credentials
- **Username**: `admin`
- **Password**: `admin123`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### PDVM Entries
- `GET /api/entries` - Get all entries for current user
- `GET /api/entries/{id}` - Get specific entry
- `POST /api/entries` - Create new entry
- `PUT /api/entries/{id}` - Update entry
- `DELETE /api/entries/{id}` - Delete entry

## Docker Setup (Alternative)

If you prefer Docker:

```powershell
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Services:
- PostgreSQL: localhost:5432
- pgAdmin: http://localhost:5050 (admin@pdvm.local / admin)
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running
- Verify DATABASE_URL in `.env`
- Ensure database `pdvm_db` exists

### Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check CORS settings in `backend/main.py`
- Verify API_URL in frontend

### Database connection errors
- Confirm PostgreSQL 18 is running
- Check username/password in connection string
- Ensure database `pdvm_db` exists
- Try connecting via pgAdmin first

### pgAdmin won't open
- Check if any pgAdmin processes are running (Task Manager)
- Delete `%APPDATA%\pgAdmin\pgadmin4.db` if corrupted
- Restart pgAdmin

## Development Tips

### Backend Development
- API documentation available at `/docs` (Swagger UI)
- Enable auto-reload by running with `uvicorn main:app --reload`
- Database changes require updating both `tables.py` and `schema.sql`

### Frontend Development
- Vite provides hot module replacement
- Use React DevTools for debugging
- API client handles authentication automatically

## Next Steps
1. Modify database models in `backend/tables.py`
2. Update schemas in `backend/schemas.py`
3. Add new API endpoints in `backend/main.py`
4. Create new React components in `frontend/src/`
5. Customize styling in CSS files

## Support
For issues or questions, check:
- FastAPI docs: https://fastapi.tiangolo.com/
- React docs: https://react.dev/
- PostgreSQL docs: https://www.postgresql.org/docs/18/
