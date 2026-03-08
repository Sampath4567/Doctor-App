# DoctorBook - Version v1.0.0-rag

DoctorBook is a full-stack doctor appointment platform with role-based access, slot management, email notifications, and an AI chat assistant with booking intent support.

This README is written for the repository snapshot `doctor-appV2.0-RAG` (March 2026).

## Tech Stack

- Backend: FastAPI, SQLAlchemy, MySQL, JWT auth
- Frontend: React (Vite), React Router, Axios
- AI: Ollama local LLM integration for chat and booking intent extraction
- Notifications: SMTP email (Gmail app password supported)

## Version Scope

- Repository release: `v2.0.0-rag`
- Backend API title/version: `DoctorBook API` / `1.0.0` (from FastAPI app metadata)
- Includes: AI chat endpoints (`/chat`, `/chat/stream`) and appointment booking flow

## Project Structure

```text
doctor-app/
|-- backend/
|   |-- main.py
|   |-- rag.py
|   |-- auth.py
|   |-- config.py
|   |-- database.py
|   |-- email_utils.py
|   |-- models.py
|   |-- schemas.py
|   |-- requirements.txt
|   `-- .env.example
|-- frontend/
|   |-- src/
|   |-- package.json
|   `-- vite.config.js
`-- README.md
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8+
- Optional for AI chat: Ollama running locally at `http://localhost:11434`

## Setup

### 1. Create database

```sql
CREATE DATABASE doctor_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Backend setup

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend default URL: `http://localhost:8000`
Swagger docs: `http://localhost:8000/docs`

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL: `http://localhost:5173`

## Environment Variables

Use `backend/.env.example` as the template. Never commit real secrets.

Required keys:

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
- `EMAIL_FROM`, `EMAIL_FROM_NAME`
- `FRONTEND_URL`
- `LLM_PROVIDER` (default currently set to `ollama`)

Optional keys:

- `GOOGLE_API_KEY`
- `OPENAI_API_KEY`

## API Overview

Main endpoint groups:

- Auth: `/auth/register`, `/auth/login`, `/auth/me`
- Specializations: CRUD endpoints for admin/public listing
- Doctors: list, details, admin create/update
- Slots: single and bulk slot management
- Appointments: create, list, cancel, complete
- Users: admin user listing
- Chat: `/chat`, `/chat/stream`

## Security and Git Hygiene

This repo now includes a root `.gitignore` to keep sensitive and local-only files out of commits:

- `.env` and secret variants
- Python virtual environments and caches
- `node_modules`
- build outputs and logs
- IDE local settings

Before first push, verify what will be committed:

```bash
git init
git add .
git status
```

If any secret file still appears in staged files, unstage it and extend `.gitignore`.

## Notes

- Gmail SMTP should use an App Password, not the account login password.
- AI chat features require a running local Ollama instance and available model.
