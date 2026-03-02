# 🏥 DoctorBook — Full-Stack Appointment System

A production-ready doctor appointment booking system built with **FastAPI** + **React** + **MySQL**, featuring role-based access, slot management, conflict prevention, and email notifications.

---

## 📁 Project Structure

```
doctor-app/
├── backend/
│   ├── main.py            # All API routes
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── database.py        # MySQL connection
│   ├── auth.py            # JWT authentication
│   ├── email_utils.py     # SMTP email notifications
│   ├── config.py          # Settings from .env
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx              # Router + Auth shell
    │   ├── index.css            # Design system
    │   ├── context/
    │   │   └── AuthContext.jsx  # Global auth state
    │   ├── services/
    │   │   └── api.js           # Axios API client
    │   ├── components/
    │   │   └── Navbar.jsx
    │   └── pages/
    │       ├── LoginPage.jsx
    │       ├── RegisterPage.jsx
    │       ├── DoctorsPage.jsx       # Browse + book
    │       ├── AppointmentsPage.jsx  # View + cancel
    │       ├── MySlotsPage.jsx       # Doctor slot mgmt
    │       └── AdminPage.jsx         # Admin dashboard
    ├── package.json
    ├── vite.config.js
    └── index.html
```

---

## 🚀 Setup & Run

### 1. MySQL Database

```sql
CREATE DATABASE doctor_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Backend

```bash
cd backend

# Copy and edit environment variables
cp .env.example .env
# Edit .env with your MySQL credentials and SMTP settings

# Install dependencies
pip install -r requirements.txt

# Start server (tables are auto-created on first run)
uvicorn main:app --reload
```

Backend runs at: http://localhost:8000  
Interactive API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

---

## ⚙️ Environment Variables

```env
# MySQL
DB_HOST=localhost
DB_PORT=3306
DB_NAME=doctor_app
DB_USER=root
DB_PASSWORD=your_password

# JWT (change in production!)
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Gmail SMTP (use App Password, not your real password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # Google App Password
EMAIL_FROM=your_email@gmail.com
EMAIL_FROM_NAME=DoctorBook

FRONTEND_URL=http://localhost:5173
```

> **Gmail setup**: Enable 2FA → Google Account → Security → App Passwords → Generate password

---

## 👥 User Roles

| Role    | Capabilities |
|---------|-------------|
| **Patient** | Register, browse doctors by specialization, book/cancel appointments |
| **Doctor**  | Register, add/delete their own slots (30 min), view their appointments |
| **Admin**   | Add specializations, create doctor profiles, view all users/appointments |

---

## 🔑 First-Time Admin Setup

1. Register a user normally
2. Manually update their role in MySQL:
```sql
UPDATE users SET role = 'admin' WHERE username = 'your_username';
```

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register user |
| POST | `/auth/login` | Login, returns JWT |
| GET | `/doctors` | List doctors (filter by `?specialization_id=`) |
| GET | `/doctors/{id}/slots` | Get slots (`?available_only=true`) |
| POST | `/doctors/{id}/slots` | Add slot (doctor/admin) |
| DELETE | `/doctors/{id}/slots/{sid}` | Delete unbooked slot |
| POST | `/appointments` | Book an appointment |
| GET | `/appointments/my` | My appointments (role-aware) |
| PUT | `/appointments/{id}/cancel` | Cancel appointment |
| GET | `/specializations` | List all specializations |
| POST | `/specializations` | Create specialization (admin) |

---

## ✉️ Email Notifications

Emails are sent in the **background** (non-blocking) for:
- **Patient**: Booking confirmation with full appointment details
- **Doctor**: New patient booking notification  
- **Both**: Cancellation notification

---

## 🛡️ Key Features

- ✅ **JWT Auth** with role-based route protection
- ✅ **Slot conflict prevention** — 409 Conflict if slot already booked
- ✅ **30-minute slots** auto-calculated from start time
- ✅ **Background email tasks** — booking never delayed by email
- ✅ **Password hashing** with bcrypt
- ✅ **Eager loading** for related models (no N+1 queries)
- ✅ **CORS** configured for local dev and production

---

## 🎨 Frontend Pages

| URL | Page | Role |
|-----|------|------|
| `/login` | Sign in | All |
| `/register` | Create account | All |
| `/doctors` | Browse & book | Patient, Admin |
| `/appointments` | View & cancel | All |
| `/my-slots` | Manage slots | Doctor |
| `/admin` | Full dashboard | Admin |
