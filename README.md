# Finance Data Processing and Access Control Backend

A backend API for a finance dashboard system built with **FastAPI**, **SQLAlchemy**, and **MySQL**. Supports role-based access control (RBAC), financial records management, and dashboard analytics.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [API Documentation](#api-documentation)
- [Access Control Matrix](#access-control-matrix)
- [Database Schema](#database-schema)
- [Assumptions & Design Decisions](#assumptions--design-decisions)
- [Running Tests](#running-tests)

---

## Architecture Overview

The application follows a **3-layer architecture** with clean separation of concerns:

```
┌──────────────────────────────────┐
│         API Layer (Routes)       │  ← Thin controllers, request/response handling
├──────────────────────────────────┤
│       Service Layer (Logic)      │  ← Business rules, validation, orchestration
├──────────────────────────────────┤
│       Data Layer (Models/DB)     │  ← SQLAlchemy ORM, database access
└──────────────────────────────────┘
         ↕
┌──────────────────────────────────┐
│      Cross-Cutting Concerns      │  ← Auth, RBAC, error handling, config
│    (core/security, core/deps)    │
└──────────────────────────────────┘
```

**Key design principles:**
- **Routes are thin controllers** — they parse input, call services, and format responses. No business logic in routes.
- **Services own business logic** — validation, aggregation, access rules all live here.
- **Consistent response format** — every endpoint returns `{success, data, message}` or `{success, error}`.
- **Role-based access via dependencies** — reusable `RoleChecker` dependency, declared at the route level.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (synchronous) |
| Database | MySQL 8.0 |
| DB Driver | PyMySQL |
| Authentication | JWT (python-jose + passlib/bcrypt) |
| Validation | Pydantic v2 |
| Rate Limiting | SlowAPI |
| Migrations | Alembic |
| Testing | pytest + FastAPI TestClient |

---

## Project Structure

```
finance-backend/
├── app/
│   ├── main.py              # FastAPI app factory, lifespan, middleware
│   ├── config.py            # Environment-based settings (pydantic-settings)
│   ├── database.py          # Engine, session factory, Base
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py          # User model with UserRole enum
│   │   └── financial_record.py  # FinancialRecord with RecordType enum
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── auth.py          # Register, Login, Token schemas
│   │   ├── user.py          # User response and update schemas
│   │   ├── financial_record.py  # Record CRUD + filter schemas
│   │   ├── dashboard.py     # Summary, breakdown, trends schemas
│   │   └── common.py        # Shared response wrappers
│   ├── api/                 # Route handlers
│   │   ├── router.py        # Aggregated router (/api/v1)
│   │   ├── auth.py          # Register, Login endpoints
│   │   ├── users.py         # User CRUD (admin only)
│   │   ├── financial_records.py  # Record CRUD with filtering
│   │   └── dashboard.py     # Analytics endpoints
│   ├── services/            # Business logic layer
│   │   ├── user_service.py
│   │   ├── financial_service.py
│   │   └── dashboard_service.py
│   └── core/                # Cross-cutting concerns
│       ├── security.py      # JWT + password hashing
│       ├── dependencies.py  # get_db, get_current_user, RoleChecker
│       └── exceptions.py    # Custom exceptions + handlers
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── seed.py                  # Seed script for demo data
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup Instructions

### Prerequisites

- **Python 3.11+**
- **MySQL 8.0+** (running locally or via Docker)

### 1. Clone and Install Dependencies

```bash
cd finance-backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac  
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update the database credentials:

```bash
copy .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/finance_db
JWT_SECRET=your-secure-random-secret-key
```

### 3. Create the Database

```sql
CREATE DATABASE IF NOT EXISTS finance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS finance_db_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Run Migrations (or auto-create tables)

Tables are automatically created on app startup via `Base.metadata.create_all()`. For migrations:

```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 5. Seed Demo Data

```bash
python seed.py
```

This creates:
| User | Email | Password | Role |
|---|---|---|---|
| Admin | admin@example.com | admin123 | admin |
| Analyst | analyst@example.com | analyst123 | analyst |
| Viewer | viewer@example.com | viewer123 | viewer |

Plus **50 sample financial records** spanning the last 6 months.

### 6. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 7. Explore the API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## API Documentation

All endpoints are prefixed with `/api/v1`.

### Authentication

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/auth/register` | Register new user (default: viewer) | No |
| POST | `/auth/login` | Login → returns JWT token | No |

### Users

| Method | Endpoint | Description | Allowed Roles |
|---|---|---|---|
| GET | `/users/me` | Get own profile | All authenticated |
| GET | `/users/` | List all users (paginated) | Admin |
| GET | `/users/{id}` | Get user by ID | Admin |
| PUT | `/users/{id}` | Update user (role, status) | Admin |
| DELETE | `/users/{id}` | Deactivate user | Admin |

### Financial Records

| Method | Endpoint | Description | Allowed Roles |
|---|---|---|---|
| POST | `/records/` | Create record | Admin |
| GET | `/records/` | List records (filtered, paginated) | All authenticated |
| GET | `/records/{id}` | Get single record | All authenticated |
| PUT | `/records/{id}` | Update record | Admin |
| DELETE | `/records/{id}` | Soft-delete record | Admin |

**Filter parameters** for `GET /records/`:
- `type` — `income` or `expense`
- `category` — category name
- `date_from`, `date_to` — date range
- `min_amount`, `max_amount` — amount range
- `page`, `page_size` — pagination
- `sort_by` — `date`, `amount`, `created_at`, `category`
- `sort_order` — `asc` or `desc`

### Dashboard

| Method | Endpoint | Description | Allowed Roles |
|---|---|---|---|
| GET | `/dashboard/summary` | Income, expenses, net balance | Analyst, Admin |
| GET | `/dashboard/category-breakdown` | Totals per category | Analyst, Admin |
| GET | `/dashboard/trends` | Monthly income/expense trends | Analyst, Admin |
| GET | `/dashboard/recent-activity` | Recent N records | All authenticated |

---

## Access Control Matrix

| Action | Viewer | Analyst | Admin |
|---|---|---|---|
| View own profile | ✅ | ✅ | ✅ |
| View financial records | ✅ | ✅ | ✅ |
| View recent activity | ✅ | ✅ | ✅ |
| View summary & trends | ❌ | ✅ | ✅ |
| Create records | ❌ | ❌ | ✅ |
| Update records | ❌ | ❌ | ✅ |
| Delete records | ❌ | ❌ | ✅ |
| Manage users | ❌ | ❌ | ✅ |

**Implementation**: Access control is enforced via FastAPI dependencies using a reusable `RoleChecker` class. Each route declares its required roles explicitly:

```python
allow_admin = RoleChecker([UserRole.ADMIN])

@router.post("/", dependencies=[Depends(allow_admin)])
def create_record(...): ...
```

---

## Database Schema

### users
| Column | Type | Notes |
|---|---|---|
| id | INT (PK) | Auto-increment |
| email | VARCHAR(255) | Unique |
| username | VARCHAR(100) | Unique |
| hashed_password | VARCHAR(255) | bcrypt hash |
| full_name | VARCHAR(200) | |
| role | ENUM(admin, analyst, viewer) | Default: viewer |
| is_active | BOOLEAN | Default: true |
| created_at | DATETIME | Auto-set |
| updated_at | DATETIME | Auto-update |

### financial_records
| Column | Type | Notes |
|---|---|---|
| id | INT (PK) | Auto-increment |
| amount | DECIMAL(15,2) | Positive values |
| type | ENUM(income, expense) | |
| category | VARCHAR(100) | Flexible, user-defined |
| date | DATE | Transaction date |
| description | TEXT | Optional |
| created_by | INT (FK → users.id) | Audit trail |
| is_deleted | BOOLEAN | Soft delete, default: false |
| created_at | DATETIME | Auto-set |
| updated_at | DATETIME | Auto-update |

**Indexes**: `type`, `category`, `date`, `created_by`, composite `(type, date)` for aggregation queries.

---

## Assumptions & Design Decisions

1. **Synchronous SQLAlchemy** — Chosen over async for simplicity. This is an assessment project; async adds complexity without meaningful benefit at this scale.

2. **Soft delete for records over SCD Type 2** — Financial records are never physically deleted. The `is_deleted` flag supports audit trails and potential undo functionality. We chose this over fully versioned row history (SCD Type 2) because historical row bloat is unnecessary for this scale, and strict CRUD overwrites are sufficient.

3. **Category as VARCHAR, not ENUM** — Allows flexible, user-defined categories without schema migrations. The seed script provides suggested defaults.

4. **JWT in Authorization header** — Standard `Bearer <token>` scheme. Token contains `sub` (user ID) and `role` for quick authorization checks without DB lookups.

5. **Positive amounts only** — The `type` field (income/expense) determines the direction. This simplifies aggregation queries and avoids ambiguity.

6. **Admin self-protection** — An admin cannot deactivate their own account, preventing lockout scenarios.

7. **Tables auto-created on startup** — `Base.metadata.create_all()` runs on app startup for ease-of-use. Alembic is also configured for proper migration workflows.

8. **Consistent response envelope** — All responses use `{success, data, message}` for success or `{success, error: {code, message}}` for errors. This makes frontend integration predictable.

9. **Date-range filters on dashboard** — All dashboard endpoints accept optional `date_from` and `date_to` parameters, defaulting to all-time if not specified.

---

## Running Tests

The test suite requires a separate `finance_db_test` MySQL database.

```bash
# Create test database
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS finance_db_test;"

# Run tests
pytest tests/ -v
```

---

## Error Response Format

All errors follow a consistent structure:

```json
{
  "success": false,
  "error": {
    "code": "RECORD_NOT_FOUND",
    "message": "Financial record with ID 42 not found"
  }
}
```

Validation errors include field-level details:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      { "field": "body -> amount", "message": "Input should be greater than 0", "type": "greater_than" }
    ]
  }
}
```

---

## Additional Thoughtfulness

Beyond the core requirements, extra effort was made to ensure this API is production-ready, secure, and developer-friendly:

1. **Intelligent Rate Limiting**: Implemented `slowapi` to protect the backend. Public endpoints like `/auth/login` are strictly capped (e.g., 5 requests/minute) to prevent brute force attacks. Aggregation endpoints like `/dashboard/summary` are moderately capped to prevent malicious database exhaustion (DoS).
2. **Unified Error Handler**: Built a global exception interceptor (`app/core/exceptions.py`) that catches everything from logic failures to Pydantic syntax errors, formatting them into a deeply readable, standardized `{"success": False, "error": {...}}` JSON payload.
3. **Advanced Filtering Engine**: Financial records aren't just paginated; they include robust query parameter filters combining exact matches (`category`, `type`) with ranges (`min_amount`, `date_from`).
4. **Out-of-the-box SeederScript**: Included `seed.py` that not only builds the tables but injects complex historical financial records spanning 6 months, ensuring the dashboard APIs yield rich data out of the box instead of empty arrays.

---


