# Snack Overflow

> A production-minded, concurrency-safe office pantry inventory and management system built with **FastAPI**, **React 18 (TypeScript)**, and **Supabase PostgreSQL**.

---

## 1. Project Overview

In busy shared office spaces, pantry snack inventory rarely reflects reality:
- Employees grab treats throughout the day without updating spreadsheets or physical clipboards.
- Multiple colleagues often rush to claim the final packets of a popular snack simultaneously.
- Traditional web applications using naive "read-then-write" sequences suffer from race conditions, causing inventory counts to drop below zero, over-allocating snacks, or recording corrupted transaction logs.

**Snack Overflow** solves these problems with database-level concurrency control, relational data integrity, robust role-based authentication, and a clean, responsive user experience.

### Core Capabilities
- **Real-Time Inventory Tracking**: Accurately tracks pantry snacks partitioned dynamically into `stocked`, `running_low`, and `gone`.
- **Atomic Stock Consumption**: Uses database-level conditional updates (`UPDATE ... WHERE quantity >= :amount RETURNING ...`) executed in a single atomic transaction with activity audit logging. Prevents negative stock under race conditions and returns an immediate HTTP 409 Conflict alert (`"Someone beat you to the last packet!"`).
- **Snack Voting & Democracy**: Allows employees to vote for their favorite snacks with database-enforced unique constraints (`uq_user_snack_vote`), crowning a deterministic **Snack of the Week**.
- **Pantry Administration**: Empowers administrators to create, edit, restock, and delete snacks with automatic cascade cleanup of historical records.
- **Role-Based Security**: Cryptographically signed JWT tokens with backend authorization enforcement protecting sensitive operations.

---

## 2. Architecture & Design Principles

### System Architecture Diagram

```
+-------------------------------------------------------------+
|                      React 18 Frontend                      |
|          (TypeScript, Vite, Tailwind CSS, Axios)            |
|  - AuthContext (JWT Storage & Persistent Session Guard)     |
|  - Pantry Dashboard & Metric Cards                          |
|  - Server-Side Filtered & Paginated Snack Catalog           |
|  - Member Consumption & Voting Controls                     |
|  - Administrator Management Portal & Modal Forms            |
+-------------------------------------------------------------+
                              |
                              | HTTP / JSON (Bearer JWT)
                              v
+-------------------------------------------------------------+
|                       FastAPI Backend                       |
|         (Python 3.12, Pydantic v2, SQLAlchemy 2.0)          |
|  - JWT Authentication & Bcrypt Password Hashing             |
|  - Role-Based Authorization Dependencies (Admin vs Member)  |
|  - Server-Side Search, Category & Status Query Engines       |
|  - Atomic Concurrency Consumption & Restocking Handlers     |
|  - Consistent API Error Contract Envelope                   |
+-------------------------------------------------------------+
                              |
                              | SQLAlchemy ORM / Psycopg2
                              v
+-------------------------------------------------------------+
|                   Supabase PostgreSQL 15                   |
|  - Relational Schema (users, snacks, votes, activities)     |
|  - CHECK Constraints (quantity >= 0, positive amount)       |
|  - UNIQUE Constraints (uq_user_snack_vote, snack name)      |
|  - Row-Level Locks & Conditional SQL Updates                |
|  - ON DELETE CASCADE Foreign Key Referential Integrity      |
+-------------------------------------------------------------+
```

### Why FastAPI is the Sole Gatekeeper (Bypassing Supabase Client-Side Access)
Supabase provides client libraries (such as `@supabase/supabase-js`) that allow frontends to query tables directly over PostgREST. In **Snack Overflow**, client-side direct database access is **strictly rejected in favor of FastAPI**:

1. **Centralized Business Logic**: Operations like snack consumption require an atomic conditional update and an activity record insert within a single database transaction. Exposing tables directly to the frontend forces business logic into client bundles or disparate Postgres RPC scripts.
2. **True Concurrency & Data Integrity**: FastAPI coordinates transactions with SQLAlchemy, catching row-level concurrency conflicts and returning structured, user-friendly HTTP 409 responses.
3. **Backend-Enforced Authorization**: Frontend role toggling is purely cosmetic. FastAPI verifies cryptographically signed JWT tokens on every protected endpoint, ensuring members cannot execute administrator mutations regardless of what client they use.
4. **Security & Data Sanitization**: Passwords, hashes, and internal database details are never exposed to browser clients.

---

## 3. Database Schema & Data Integrity

The application utilizes four relational tables in PostgreSQL managed via **Alembic** migrations:

```
  +------------------+         +------------------+
  |      users       |         |      snacks      |
  +------------------+         +------------------+
  | id (PK)          |         | id (PK)          |
  | name             |         | name (UNIQUE)    |
  | email (UNIQUE)   |         | category         |
  | password_hash    |         | quantity (>= 0)  |
  | role             |         | low_stock_thresh |
  | created_at       |         | created_at       |
  +------------------+         | updated_at       |
         |      |              +------------------+
         |      |                      |      |
         |      +-----------+  +-------+      |
         |                  |  |              |
         v                  v  v              v
+------------------+   +------------------+
|    activities    |   |      votes       |
+------------------+   +------------------+
| id (PK)          |   | id (PK)          |
| user_id (FK)     |   | user_id (FK)     |
| snack_id (FK)    |   | snack_id (FK)    |
| action           |   | created_at       |
| amount (> 0)     |   | UNIQUE(uid, sid) |
| created_at       |   +------------------+
+------------------+
```

### 1. `users` Table
Stores authenticated pantry users and their role assignments.
- `id`: Integer primary key (autoincrement).
- `name`: Full name string (non-empty).
- `email`: Unique, indexed email string.
- `password_hash`: Bcrypt hashed password string. Never stored in plain text.
- `role`: Role string constrained by `ck_users_role_valid` to either `'admin'` or `'member'`.
- `created_at`: Timestamp with timezone defaulting to `NOW()`.

### 2. `snacks` Table
Maintains snack catalog details and current inventory levels.
- `id`: Integer primary key (autoincrement).
- `name`: Unique, indexed name string.
- `category`: Category string constrained by `ck_snacks_category_valid` to one of: `'sweet'`, `'savoury'`, `'drink'`, `'healthy-ish'`.
- `quantity`: Integer stock level protected by database check constraint `ck_snacks_quantity_non_negative`:
  $$\text{quantity} \ge 0$$
  Stock can never become negative at the database level.
- `low_stock_threshold`: Non-negative integer (default `5`) used to calculate stock alerts.
- `created_at` / `updated_at`: Timestamps with automatic timezone tracking.

### 3. `votes` Table
Records member votes for pantry snacks.
- `id`: Integer primary key (autoincrement).
- `user_id`: Foreign key referencing `users.id` with `ON DELETE CASCADE`.
- `snack_id`: Foreign key referencing `snacks.id` with `ON DELETE CASCADE`.
- `created_at`: Timestamp of vote creation.
- **Unique Constraint (`uq_user_snack_vote`)**: Composite unique constraint on `(user_id, snack_id)`. Guarantees at the database level that an employee can vote for a given snack only once, even under concurrent requests.

### 4. `activities` Table
Maintains an immutable audit ledger of all consumption and restocking events.
- `id`: Integer primary key (autoincrement).
- `user_id`: Foreign key referencing the user performing the action (`ON DELETE CASCADE`).
- `snack_id`: Foreign key referencing the affected snack (`ON DELETE CASCADE`).
- `action`: String constrained by `ck_activities_action_valid` to `'consumed'` or `'restocked'`.
- `amount`: Positive integer constrained by `ck_activities_amount_positive` (`amount > 0`).
- `created_at`: Timestamp of the transaction.

### Derived Snack Status (Why Status is NOT a Column)
Snack status is **calculated dynamically** from `quantity` and `low_stock_threshold` rather than stored as a separate column:
- `stocked`: $\text{quantity} > \text{low\_stock\_threshold}$
- `running_low`: $0 < \text{quantity} \le \text{low\_stock\_threshold}$
- `gone`: $\text{quantity} = 0$

#### Why Not Store It?
Storing derived status in a database column violates normalization principles and introduces **cache invalidation bugs**:
- If `quantity` drops to 0, an update that changes quantity without setting status would leave the record inconsistent (e.g. `quantity: 0`, `status: "stocked"`).
- By computing status as a Python `@property` and SQL expression, the status is mathematically guaranteed to always accurately reflect inventory.

---

## 4. Concurrency & Race Condition Strategy

### The Simultaneous Consumption Problem
Consider a pantry with only **1 packet** of *Artisan Pretzels* remaining. Two employees, Alice and Bob, click "Grab 1 Packet" at the exact same moment.

#### The Naive Read-Then-Write Flaw
In a naive application:
1. Thread Alice reads: `SELECT quantity FROM snacks WHERE id = 1` $\rightarrow$ returns `1`.
2. Thread Bob reads: `SELECT quantity FROM snacks WHERE id = 1` $\rightarrow$ returns `1`.
3. Thread Alice evaluates in Python: `if quantity >= 1: quantity -= 1` $\rightarrow$ writes `quantity = 0`.
4. Thread Bob evaluates in Python: `if quantity >= 1: quantity -= 1` $\rightarrow$ writes `quantity = 0` (or `-1` if decremented directly).

Both Alice and Bob believe they obtained the snack. Two people walk to the shelf, but only one physical packet exists!

### The Atomic SQL Conditional Solution
Snack Overflow solves this by executing a **single atomic conditional update statement** at the PostgreSQL engine level:

```sql
UPDATE snacks
SET quantity = quantity - :amount,
    updated_at = NOW()
WHERE id = :snack_id
  AND quantity >= :amount
RETURNING id, name, category, quantity, low_stock_threshold, created_at, updated_at;
```

#### How It Works:
1. **Row-Level Write Lock**: When the first request reaches PostgreSQL, the database engine acquires a row-level write lock on the target snack row.
2. **Conditional Evaluation**: The clause `WHERE quantity >= :amount` is evaluated atomically inside the database engine.
3. **Outcome for Alice**: The row matches `quantity >= 1`. PostgreSQL decrements quantity to `0`, commits, and returns the updated row via `RETURNING`.
4. **Outcome for Bob**: The lock is released. When Bob's query evaluates the row, `quantity` is now `0`. The condition `quantity >= 1` is false! PostgreSQL updates **0 rows** and returns nothing.
5. **Conflict Response (HTTP 409)**: FastAPI detects that 0 rows were affected. It checks if the snack exists, determines stock was exhausted, and raises:
   ```json
   {
     "error": {
       "code": "INSUFFICIENT_STOCK",
       "message": "Someone beat you to the last packet!"
     }
   }
   ```
6. **Transactional Activity Record**: The stock decrement and `Activity(action='consumed')` insertion occur within the **same database transaction**. If either fails, both roll back.

---

## 5. Snack of the Week & Deterministic Tie-Breaking

The **Snack of the Week** is calculated on demand in `GET /snacks/summary` using a strict, documented 3-tier deterministic tie-breaking algorithm:

```sql
SELECT snacks.*, COUNT(votes.id) AS vote_count
FROM snacks
LEFT OUTER JOIN votes ON votes.snack_id = snacks.id
GROUP BY snacks.id
ORDER BY
    vote_count DESC,        -- Tier 1: Most popular vote tally
    snacks.quantity DESC,   -- Tier 2: Higher available inventory
    snacks.name ASC         -- Tier 3: Alphabetical order by name
LIMIT 1;
```

### Tie-Breaking Rules:
1. **Primary (Total Votes)**: The snack with the highest number of votes wins.
2. **Secondary (Available Inventory)**: If two or more snacks have the exact same vote count, the snack with **greater available stock** wins. This ensures employees are directed toward a popular snack they can actually enjoy.
3. **Tertiary (Alphabetical)**: If votes and stock are identical, the tie is broken alphabetically by snack name (`ASC`), guaranteeing a deterministic, repeatable selection without random flips.

---

## 6. Complete API Reference

All protected endpoints require the HTTP header:
`Authorization: Bearer <access_token>`

### Consistent Error Format
All errors conform strictly to the structured envelope:
```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human-readable description."
  }
}
```

### Endpoints Table

| Method | Endpoint | Access | Description | Success Code |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public | Live database connectivity & health check | `200 OK` |
| `POST` | `/auth/login` | Public | Authenticate user credentials & issue JWT | `200 OK` |
| `GET` | `/auth/me` | Authenticated | Retrieve current user profile | `200 OK` |
| `GET` | `/auth/admin-check`| Admin | Verify administrative privileges | `200 OK` |
| `GET` | `/snacks/summary` | Authenticated | Stock status counts & Snack of the Week | `200 OK` |
| `GET` | `/snacks` | Authenticated | Server-side filtered & paginated snack catalog | `200 OK` |
| `GET` | `/snacks/{id}` | Authenticated | Retrieve single snack details | `200 OK` |
| `POST` | `/snacks` | Admin | Create a new pantry snack | `201 Created` |
| `PATCH`| `/snacks/{id}` | Admin | Update snack metadata | `200 OK` |
| `DELETE`| `/snacks/{id}` | Admin | Delete snack (cascades votes & activities) | `200 OK` |
| `POST` | `/snacks/{id}/consume` | Authenticated | Atomically consume 1 or more packets | `200 OK` |
| `POST` | `/snacks/{id}/restock` | Admin | Restock quantity & log restock audit | `200 OK` |
| `POST` | `/snacks/{id}/vote` | Authenticated | Cast a vote (enforces 1 vote per user) | `200 OK` |
| `DELETE`| `/snacks/{id}/vote` | Authenticated | Retract authenticated user's vote | `200 OK` |

---

## 7. Local Setup & Installation Guide

### Prerequisites
- **Python**: 3.12 or newer
- **Node.js**: 18.x or newer (with npm)
- **Supabase PostgreSQL Database**: A Supabase project (or any local PostgreSQL 14+ instance)

---

### Step 1: Clone the Repository
```powershell
git clone https://github.com/niteshkumar1710/Snack-overflow.git
cd Snack-overflow
```

---

### Step 2: Backend Setup

1. **Navigate to the backend directory**:
   ```powershell
   cd backend
   ```

2. **Create and activate a Python virtual environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```powershell
   cp .env.example .env
   ```
   Open `.env` and configure your database connection string and JWT secret:
   ```env
   # Use Supabase Session Pooler (port 5432) or Transaction Pooler (port 6543)
   DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   JWT_SECRET_KEY=super_secure_random_jwt_secret_key_minimum_32_characters
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ENVIRONMENT=development
   CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
   ```

5. **Run Database Migrations**:
   Apply Alembic schema migrations to create all tables and constraints:
   ```powershell
   alembic upgrade head
   ```

6. **Seed Initial Demo Accounts & Snacks**:
   ```powershell
   python seed.py
   ```

7. **Start the FastAPI Backend Server**:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```
   *The backend will be running at `http://localhost:8000`. Interactive Swagger API docs are available at `http://localhost:8000/docs`.*

---

### Step 3: Frontend Setup

1. **Open a new terminal and navigate to the frontend directory**:
   ```powershell
   cd Snack-overflow/frontend
   ```

2. **Install Node dependencies**:
   ```powershell
   npm install
   ```

3. **Configure Environment Variables**:
   Create `.env`:
   ```powershell
   cp .env.example .env
   ```
   Ensure it points to the backend:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

4. **Start the Vite Development Server**:
   ```powershell
   npm run dev
   ```
   *The frontend application will be running at `http://localhost:5173`.*

---

## 8. Seeded Demo Accounts for Testing

The database seeding script (`python seed.py`) pre-configures two accounts:

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@example.com` | `Admin@123` | Full access: Add, Edit, Delete, Restock, Vote, Consume, Dashboard |
| **Member** | `member@example.com` | `Member@123` | Member access: View Dashboard, Browse Snacks, Vote, Consume |

> **Pro Tip**: The login page (`http://localhost:5173/login`) features **1-Click Demo Buttons** (`Admin Demo` and `Member Demo`) that instantly populate these credentials for convenient evaluation!

---

## 9. Running Automated Tests

Snack Overflow includes an automated test suite covering authentication, database constraints, models, CRUD operations, atomic consumption, voting, summaries, and live PostgreSQL concurrency.

### Execute the Complete Pytest Suite
```powershell
cd backend
.\.venv\Scripts\pytest -v
```

### Live PostgreSQL Concurrency Test
The test suite includes a dedicated multi-threaded PostgreSQL test (`tests/test_concurrency.py`):
```powershell
pytest tests/test_concurrency.py -v
```
**Test Specification**:
- Creates a snack with initial stock = `3`.
- Fires **10 concurrent threads** simultaneously attempting to consume 1 packet each.
- Asserts that **exactly 3 requests succeed** (`200 OK`).
- Asserts that **exactly 7 requests fail with HTTP 409 Conflict** (`"Someone beat you to the last packet!"`).
- Verifies that final database stock is **strictly 0** (never negative).
- Verifies that **exactly 3 activity records** were inserted.

---

## 10. Verifying the Application in the Browser

1. Navigate to `http://localhost:5173/login`.
2. Click **"Member Demo"** and sign in.
3. Review the **Pantry Dashboard**: observe real-time stat cards (Stocked, Running Low, Out of Stock) and the top-voted **Snack of the Week** spotlight.
4. Click **"Snacks Catalog"** in the navigation header:
   - Test the search bar: type `"Almonds"` or `"Chips"` to see live server-side search.
   - Filter by Category or Status.
   - Click **"Vote"** on any snack: observe the vote count increase and button change to `"Voted"`. Click again to unvote.
   - Click **"Grab 1 Packet"**: observe stock decrement in place with success feedback.
5. Log out and sign in using **"Admin Demo"**:
   - Notice the purple **"Admin Portal"** link in the navigation header.
   - Click **"Admin Portal"**: create a new snack, restock existing inventory using quick buttons (`+10`), edit metadata, or test deletion.

---

## 11. Security Checklist

- [x] **No Plaintext Passwords**: Passwords hashed using industry-standard `bcrypt` with salt.
- [x] **Secure Token Authorization**: Stateless JSON Web Tokens (JWT) signed with `HS256`.
- [x] **Backend RBAC Perimeter**: Administrator operations rejected with HTTP 403 at the FastAPI dependency level (`require_admin`).
- [x] **Strict Input Validation**: Request schemas validated via Pydantic v2 (regex sanitization, length boundaries, enum constraints).
- [x] **No Leaked Secrets**: Password hashes, JWT secrets, and database credentials excluded from responses and committed code.
- [x] **CORS Configuration**: Restricts browser requests to authorized frontend origins.

---

## 12. Advanced Production Features

### A. Idempotency-Key Support (Network Retry Safety)
Distributed pantry systems often encounter transient network timeouts where a client is unsure if a request succeeded. Resending the request could accidentally consume multiple snacks or double-restock inventory.

- **Header**: `Idempotency-Key: <UUID>` on `POST /snacks/{id}/consume` and `POST /snacks/{id}/restock`.
- **Database Schema**: `idempotency_keys` table with unique constraint `uq_user_idempotency_key (user_id, key)`.
- **Request Fingerprinting**: Computes a SHA-256 hash of `METHOD:PATH:PAYLOAD`. Reusing the same key with a different payload returns `HTTP 409 Conflict (IDEMPOTENCY_KEY_PAYLOAD_MISMATCH)`.
- **Atomic Caching**: Successful responses are stored in PostgreSQL. Subsequent identical retries return the cached JSON response and HTTP status immediately without re-executing stock decrement logic or inserting duplicate activity logs.
- **Expiration Policy**: Idempotency records expire after 24 hours.

### B. Real-Time Stock Updates (WebSockets)
Pantry inventory updates instantly on all connected devices without manual page refreshes:

- **Endpoint**: `GET /ws/pantry?token=<JWT>` (upgrades to WebSocket).
- **Authentication**: JWT token validated on handshake; unauthenticated connections are closed with code `1008 (Policy Violation)`.
- **Transaction Safety**: Stock events are broadcast **only after** the database transaction successfully commits. If consumption fails (e.g. 409 Insufficient Stock), no broadcast is emitted.
- **Payload Event Structure**:
  ```json
  {
    "type": "STOCK_UPDATED",
    "event": "consumed",
    "snack_id": 4,
    "snack_name": "Lays",
    "quantity": 8,
    "low_stock_threshold": 3,
    "status": "stocked",
    "amount": 1,
    "user_id": 2
  }
  ```
- **Connection Management & Horizontal Scaling**:
  - The current single-instance deployment uses an in-memory `ConnectionManager` with periodic keepalive pings (`25s`) to prevent proxy timeouts.
  - For horizontal scaling across multiple Render instances, a shared pub/sub broker (e.g., Redis via Upstash or Render Redis) can be plugged into `ConnectionManager.broadcast` to fan out events across all nodes.

### C. Optimistic UI with Authoritative Rollback
- **Instant Response**: Clicking **"Take Snack"** decrements displayed quantity and recalculates status badges (`stocked`, `running_low`, `gone`) immediately in React state.
- **Multi-Click Prevention**: The button is locked during transit for that specific snack ID.
- **Authoritative Reconciliation**: Replaces optimistic values with server-verified data upon response.
- **Rollback Guarantee**: If the backend rejects the request (network disconnect or 409 Insufficient Stock), the UI rolls back to the exact previous snapshot and resynchronizes.

---

## 13. Production Deployment Guide (Vercel + Render + Supabase)

### Backend Deployment (Render)
1. **Root Directory**: `backend`
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables**:
   - `DATABASE_URL`: Supabase Transaction Pooler URL (`postgresql://postgres.<REF>:<PASSWORD>@aws-1-ap-south-1.pooler.supabase.com:6543/postgres`)
   - `ENVIRONMENT`: `production`
   - `JWT_SECRET_KEY`: High-entropy 32+ character secret
   - `CORS_ORIGINS`: `http://localhost:5173,https://<your-vercel-domain>.vercel.app`

### Frontend Deployment (Vercel)
1. **Root Directory**: `frontend`
2. **Framework Preset**: `Vite`
3. **Build Command**: `npm run build`
4. **Output Directory**: `dist`
5. **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://<your-render-backend>.onrender.com`
6. **SPA Routing**: Handled via `frontend/vercel.json` rewrites to prevent 404s on direct URL navigation.
