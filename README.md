# Setup & Run Instructions

## Prerequisites
- Python 3.8+
- PostgreSQL database running and accessible

## 1. Install dependencies
```sh
pip install fastapi uvicorn sqlalchemy psycopg2-binary passlib[bcrypt] python-jose pydantic
```

## 2. Configure environment variables
Set your database URL and JWT secret key:
```sh
# Recommended database name: 846_final_project
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/846_final_project"
# Generate a secure JWT secret key:
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and set it as your JWT_SECRET_KEY:
export JWT_SECRET_KEY="paste-your-generated-key-here"
```

## 3. Initialize the database
Tables are auto-created on first run. For production, use Alembic for migrations.

## 4. Run the application
From the project root directory:
```sh
uvicorn src.main:app --reload
```

## 5. Access the API
Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive Swagger UI.

---
# 846_final_project
  
---

# Frontend Setup & Run Instructions

## Prerequisites
- Node.js 16+

## 1. Install dependencies
From the `frontend` directory:
```sh
cd frontend
npm install
```

## 2. Configure API URL (if needed)
By default, the frontend expects the backend at `http://127.0.0.1:8000`. If your backend runs elsewhere, update `API_URL` in `frontend/src/api.js`.

## 3. Run the frontend app
```sh
npm start
```

## 4. Access the frontend
Open [http://localhost:3000](http://localhost:3000) in your browser.

---