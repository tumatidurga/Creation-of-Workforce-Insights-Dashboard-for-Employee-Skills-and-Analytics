# AI Workforce Management Automation System - Complete Technical Documentation

---

## 1. Complete Folder Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI application entry point & CORS
│   │   ├── config.py                # Pydantic BaseSettings configuration
│   │   ├── database.py              # Motor AsyncIOMotorClient & seed data engine
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py           # Employee, Attendance, Leave, Shift, Payroll, AI schemas
│   │   │   └── additional_schemas.py# Reports, System Settings, User Profile schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── employees.py         # Employee CRUD, search, filter, pagination
│   │   │   ├── attendance.py        # Check-in, check-out, anomaly detection
│   │   │   ├── leaves.py            # Leave applications & entitlement balances
│   │   │   ├── shifts.py            # Shift swap and scheduling requests
│   │   │   ├── timesheets.py        # Project logging & billable hours
│   │   │   ├── payroll.py           # Automated salary calculation & disbursement
│   │   │   ├── performance.py       # KPI scores & talent promotion recommendations
│   │   │   ├── notifications.py     # System alerts & read status tracking
│   │   │   ├── audit.py             # Security audit logs & compliance tracking
│   │   │   ├── analytics.py         # Executive KPIs & dashboard aggregation
│   │   │   ├── ai.py                # Gemini-powered AI chatbot & workforce intelligence
│   │   │   ├── reports.py           # Compliance & payroll report generator
│   │   │   ├── settings.py          # System settings & AI model parameters
│   │   │   └── profile.py           # Current user profile & MFA preferences
│   │   └── services/
│   │       ├── __init__.py
│   │       └── workforce_services.py# Enterprise async business logic layer
│   └── requirements.txt             # Python backend dependencies
├── src/
│   ├── components/                  # React modular components (Navigation, Header, Modals)
│   ├── views/                       # Core UI screens (Dashboard, Employees, Attendance, etc.)
│   ├── services/
│   │   └── api.js                   # Unified Axios API client with error interceptors
│   ├── App.tsx                      # Primary React single-screen & tab state container
│   ├── main.tsx                     # Vite React entry point
│   └── index.css                    # Tailwind CSS v4 setup
├── server.ts                        # Production Node/Express gateway serving API proxy & static assets
├── metadata.json                    # AI Studio applet configuration & frame permissions
├── package.json                     # Node.js dependencies and build/dev scripts
├── .env.example                     # Environment variable definitions
└── README.md                        # Master project documentation
```

---

## 2. MongoDB Collections

The system integrates 11 dedicated MongoDB collections with full async support via Motor driver:

1. **`employees`**: Central directory storing full worker profiles, salary baselines, performance scores, skills, and emergency contacts.
2. **`attendance`**: Daily clock-in/out records, GPS geofence verifications, and flagged anomaly records.
3. **`leaves`**: Time-off applications, start/end dates, approval workflows, and manager remarks.
4. **`shifts`**: Shift scheduling preferences, night/day swap requests, and operational allocations.
5. **`timesheets`**: Daily project task logs, billable hours tracking, and client billing approvals.
6. **`payroll`**: Automated monthly compensation calculations, tax deductions, overtime earnings, and disbursement statuses.
7. **`performance`**: Talent intelligence metrics, KPI completion percentages, learning scores, and AI promotion recommendations.
8. **`notifications`**: Real-time workforce alerts, high-priority shift warnings, and notification read states.
9. **`audit_logs`**: Security governance history, IP tracking, module access logs, and compliance audits.
10. **`settings`**: System configuration, AI model parameters, attrition risk thresholds, and company timezone preferences.
11. **`user_profile`**: Active user session profile, role permissions, and MFA status.

---

## 3. Collection Schemas

### Employee Document Schema (`employees`)
```json
{
  "_id": "ObjectId",
  "empId": "E-1001",
  "firstName": "Alexander",
  "lastName": "Wright",
  "email": "alexander.wright@enterprise.com",
  "phone": "+1 (555) 019-2834",
  "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb",
  "gender": "Male",
  "age": 38,
  "department": "Engineering",
  "jobRole": "Director of Technology",
  "designation": "Director",
  "jobLevel": 5,
  "managerId": "E-1000",
  "managerName": "Board Executive",
  "location": "Headquarters - New York",
  "status": "Active",
  "monthlyIncome": 16500.0,
  "yearsAtCompany": 7,
  "yearsInRole": 3,
  "yearsWithManager": 4,
  "workLifeBalanceScore": 4,
  "jobSatisfactionScore": 5,
  "environmentSatisfactionScore": 4,
  "relationshipSatisfactionScore": 5,
  "skills": ["System Architecture", "Cloud Governance", "AI Engineering"],
  "education": "Master of Computer Science",
  "educationField": "Software Systems",
  "emergencyContact": {
    "name": "Elena Wright",
    "relationship": "Spouse",
    "phone": "+1 (555) 019-2835"
  },
  "address": "742 Evergreen Terrace, Manhattan, NY"
}
```

### Attendance Document Schema (`attendance`)
```json
{
  "_id": "ObjectId",
  "id": "ATT-101",
  "empId": "E-1001",
  "empName": "Alexander Wright",
  "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb",
  "department": "Engineering",
  "date": "2026-08-04",
  "checkIn": "08:52",
  "checkOut": "18:15",
  "workingHours": 9.38,
  "status": "Present",
  "isAnomaly": false
}
```

---

## 4. FastAPI Folder Structure

```
backend/app/
├── main.py                  # App entry point, CORS, lifespan async MongoDB context
├── config.py                # Environment setting declarations (Pydantic BaseSettings)
├── database.py              # Motor client instance, connect/disconnect hooks, database seeder
├── models/                  # Pydantic schemas for data validation and typing
│   ├── schemas.py           # Core entity schemas
│   └── additional_schemas.py# System, report, and profile schemas
├── routers/                 # Modular API route controllers
│   ├── employees.py
│   ├── attendance.py
│   ├── leaves.py
│   ├── shifts.py
│   ├── timesheets.py
│   ├── payroll.py
│   ├── performance.py
│   ├── notifications.py
│   ├── audit.py
│   ├── analytics.py
│   ├── ai.py
│   ├── reports.py
│   ├── settings.py
│   └── profile.py
└── services/                # Reusable async service layer logic
    └── workforce_services.py
```

---

## 5. Swagger / OpenAPI Documentation

FastAPI automatically generates interactive Swagger and ReDoc documentation:
- **Interactive Swagger UI**: `http://localhost:3000/api/docs` (or `/api/docs`)
- **ReDoc Documentation**: `http://localhost:3000/api/redoc` (or `/api/redoc`)
- **OpenAPI Schema JSON**: `http://localhost:3000/api/openapi.json`

---

## 6. Complete API Endpoint List

| HTTP Method | Route Endpoint | Router Tag | Description |
|---|---|---|---|
| `GET` | `/api/health` | Health | Health check status & framework diagnostic |
| `GET` | `/api/employees` | Employees | Get paginated employee list with search & filters |
| `GET` | `/api/employees/{emp_id}` | Employees | Get detailed record for single employee |
| `POST` | `/api/employees` | Employees | Register new employee record |
| `PUT` | `/api/employees/{emp_id}` | Employees | Update employee details |
| `DELETE` | `/api/employees/{emp_id}` | Employees | Delete employee record |
| `GET` | `/api/attendance` | Attendance | Get attendance logs with pagination & filtering |
| `GET` | `/api/attendance/anomalies` | Attendance | Get flagged attendance anomalies |
| `POST` | `/api/attendance/check-in` | Attendance | Check in employee with biometric verification |
| `POST` | `/api/attendance/check-out` | Attendance | Check out employee & compute working hours |
| `GET` | `/api/leaves` | Leaves | Get leave applications |
| `GET` | `/api/leaves/balance` | Leaves | Get entitlement leave balances |
| `POST` | `/api/leaves` | Leaves | Submit leave application |
| `PUT` | `/api/leaves/{id}/status` | Leaves | Approve or reject leave request |
| `GET` | `/api/shifts` | Shifts | Get shift requests |
| `POST` | `/api/shifts` | Shifts | Submit shift swap request |
| `PUT` | `/api/shifts/{id}/status` | Shifts | Update shift request status |
| `GET` | `/api/timesheets` | Timesheets | Get project timesheet entries |
| `POST` | `/api/timesheets` | Timesheets | Submit timesheet entry |
| `PUT` | `/api/timesheets/{id}/status`| Timesheets | Update timesheet approval status |
| `GET` | `/api/payroll` | Payroll | Get processed payroll statements |
| `POST` | `/api/payroll/calculate` | Payroll | Execute automated salary & tax engine |
| `PUT` | `/api/payroll/{id}/disburse` | Payroll | Mark payroll statement as disbursed |
| `GET` | `/api/performance` | Performance | Get talent performance & promotion recommendations |
| `GET` | `/api/performance/{emp_id}` | Performance | Get employee performance breakdown |
| `GET` | `/api/notifications` | Notifications | Get notification feed |
| `PUT` | `/api/notifications/{id}/read`| Notifications| Mark notification as read |
| `POST` | `/api/notifications/mark-all-read`| Notifications| Mark all notifications read |
| `GET` | `/api/audit-logs` | Audit | Get governance audit log entries |
| `POST` | `/api/audit-logs` | Audit | Log new compliance audit record |
| `GET` | `/api/analytics/dashboard` | Analytics | Executive dashboard KPIs |
| `POST` | `/api/chat` | AI Intelligence | Gemini AI workforce chatbot endpoint |
| `POST` | `/api/ai-insights` | AI Intelligence | Predictive workforce analytics engine |
| `POST` | `/api/reports/generate` | Reports | Generate workforce compliance PDF/CSV report |
| `GET` | `/api/reports/summary` | Reports | Get report templates |
| `GET` | `/api/settings` | Settings | Get system configuration |
| `PUT` | `/api/settings` | Settings | Update system configuration |
| `GET` | `/api/profile` | Profile | Get current user profile |
| `PUT` | `/api/profile` | Profile | Update current user profile |

---

## 7. Request and Response Examples

### Example 1: Create Employee (`POST /api/employees`)
**Request Body**:
```json
{
  "empId": "E-1010",
  "firstName": "Marcus",
  "lastName": "Vance",
  "email": "marcus.vance@enterprise.com",
  "phone": "+1 (555) 012-9900",
  "department": "Engineering",
  "jobRole": "Cloud Security Architect",
  "designation": "Staff Architect",
  "jobLevel": 4,
  "location": "Headquarters - New York",
  "status": "Active",
  "monthlyIncome": 13500.0,
  "emergencyContact": {
    "name": "Sarah Vance",
    "relationship": "Spouse",
    "phone": "+1 (555) 012-9901"
  },
  "address": "150 Wall Street, New York, NY"
}
```
**Response (`201 Created`)**:
```json
{
  "empId": "E-1010",
  "firstName": "Marcus",
  "lastName": "Vance",
  "email": "marcus.vance@enterprise.com",
  "phone": "+1 (555) 012-9900",
  "department": "Engineering",
  "jobRole": "Cloud Security Architect",
  "designation": "Staff Architect",
  "jobLevel": 4,
  "location": "Headquarters - New York",
  "status": "Active",
  "monthlyIncome": 13500.0,
  "skills": [],
  "emergencyContact": {
    "name": "Sarah Vance",
    "relationship": "Spouse",
    "phone": "+1 (555) 012-9901"
  },
  "address": "150 Wall Street, New York, NY"
}
```

### Example 2: AI Chat Request (`POST /api/chat`)
**Request Body**:
```json
{
  "message": "Which employees have high attrition risk?",
  "role": "HR Administrator"
}
```
**Response (`200 OK`)**:
```json
{
  "reply": "Based on machine learning attrition risk models (XGBoost classifier), 3 employees are flagged with high flight risk (>70% probability):\n\n1. Emp #E-1004 (David Miller) - Engineering (88% Attrition Risk) | Driver: Excessive Overtime (28 hrs/mo), Low Environment Satisfaction.\n2. Emp #E-1009 (Jessica Taylor) - Product Management (79% Risk) | Driver: Market Pay Gap & 4.2 yrs in current role.\n3. Emp #E-1015 (Rachel Green) - Customer Success (74% Risk) | Driver: Long commute distance & Work-Life Balance score 2/5.",
  "text": "Based on machine learning attrition risk models...",
  "dataWidget": {
    "type": "attrition_widget",
    "highRiskCount": 3,
    "avgRiskScore": "34%",
    "topDepartment": "Engineering"
  },
  "model": "gemini-2.5-flash"
}
```

---

## 8. backend/requirements.txt

```txt
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
motor>=3.3.0
pymongo>=4.6.0
python-dotenv>=1.0.0
google-genai>=0.1.0
httpx>=0.27.0
```

---

## 9. package.json

```json
{
  "name": "react-example",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "tsx server.ts",
    "build": "vite build && esbuild server.ts --bundle --platform=node --format=cjs --packages=external --sourcemap --outfile=dist/server.cjs",
    "start": "node dist/server.cjs",
    "clean": "rm -rf dist server.js",
    "lint": "tsc --noEmit"
  },
  "dependencies": {
    "@google/genai": "^2.4.0",
    "@tailwindcss/vite": "^4.1.14",
    "@vitejs/plugin-react": "^5.0.4",
    "axios": "^1.19.0",
    "dotenv": "^17.2.3",
    "express": "^4.21.2",
    "lucide-react": "^0.546.0",
    "motion": "^12.23.24",
    "react": "^19.0.1",
    "react-dom": "^19.0.1",
    "recharts": "^3.10.1",
    "vite": "^6.2.3"
  },
  "devDependencies": {
    "@types/node": "^22.14.0",
    "autoprefixer": "^10.4.21",
    "esbuild": "^0.25.0",
    "tailwindcss": "^4.1.14",
    "tsx": "^4.21.0",
    "typescript": "~5.8.2",
    "@types/express": "^4.17.21"
  }
}
```

---

## 10. .env.example

```env
# Gemini API Key (Server-side secret)
GEMINI_API_KEY="MY_GEMINI_API_KEY"

# Application Hosted URL
APP_URL="MY_APP_URL"

# MongoDB Database Configuration
MONGODB_URL="mongodb://localhost:27017"
DATABASE_NAME="workforce_db"

# FastAPI Configuration
PROJECT_NAME="AI Workforce Management Automation System"
VERSION="1.0.0"
API_V1_STR="/api"
PORT=3000
```

---

## 11. Installation Guide

### Step 1: Clone Repository & Install Node.js Dependencies
```bash
git clone <repository-url>
cd workforce-system
npm install
```

### Step 2: Set Up Python Backend Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

---

## 12. Run Commands

### Development Mode (Full Stack Gateway on Port 3000)
```bash
npm run dev
```

### Running FastAPI Standalone Server (Port 8000)
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Build & Launch
```bash
npm run build
npm run start
```

---

## 13. MongoDB Import Guide

### Exporting / Importing Seed Data via `mongoimport`
To seed database collections manually using `mongoimport`:

```bash
mongoimport --uri "mongodb://localhost:27017/workforce_db" --collection employees --file seed_employees.json --jsonArray
mongoimport --uri "mongodb://localhost:27017/workforce_db" --collection attendance --file seed_attendance.json --jsonArray
mongoimport --uri "mongodb://localhost:27017/workforce_db" --collection leaves --file seed_leaves.json --jsonArray
mongoimport --uri "mongodb://localhost:27017/workforce_db" --collection payroll --file seed_payroll.json --jsonArray
```

Note: The system automatically seeds initial database records on boot if collections are empty!

---

## 14. Environment Variable Explanation

| Variable Name | Required | Default | Purpose |
|---|---|---|---|
| `GEMINI_API_KEY` | Optional | `""` | Google GenAI API key for live Gemini 2.5 Flash chatbot responses |
| `MONGODB_URL` | Optional | `mongodb://localhost:27017` | MongoDB connection URL for Motor async driver |
| `DATABASE_NAME` | Optional | `workforce_db` | MongoDB database identifier |
| `PORT` | Required | `3000` | Port bound for Cloud Run / Container ingress |
| `PROJECT_NAME` | Optional | `AI Workforce...` | Application name in Swagger UI |

---

## 15. Backend Architecture Diagram

```
+-----------------------------------------------------------------------+
|                         FastAPI Application                           |
|  +-----------------------------------------------------------------+  |
|  |                          Routers                                |  |
|  |  /employees, /attendance, /leaves, /payroll, /ai, /analytics ... |  |
|  +-----------------------------------------------------------------+  |
|                                  |                                    |
|                                  v                                    |
|  +-----------------------------------------------------------------+  |
|  |                     Workforce Services Layer                    |  |
|  |         EmployeeService, AttendanceService, PayrollEngine...    |  |
|  +-----------------------------------------------------------------+  |
|                     /                         \                       |
|                    v                           v                      |
|  +---------------------------+       +-----------------------------+  |
|  | MongoDB (Motor Async Driver) |       | Google GenAI SDK (Gemini)   |  |
|  +---------------------------+       +-----------------------------+  |
+-----------------------------------------------------------------------+
```

---

## 16. Frontend Architecture Diagram

```
+-----------------------------------------------------------------------+
|                          React 19 SPA                                 |
|  +-----------------------------------------------------------------+  |
|  |                          App.tsx                                |  |
|  |         (Tab Routing & Executive Header & Layout State)          |  |
|  +-----------------------------------------------------------------+  |
|                                  |                                    |
|      +---------------------------+---------------------------+        |
|      v                           v                           v        |
| +------------------+   +--------------------+   +-------------------+ |
| | DashboardView    |   | EmployeesView      |   | AttendanceView    | |
| | PayrollView      |   | LeavesView         |   | AiAssistantModal  | |
| +------------------+   +--------------------+   +-------------------+ |
|                                  |                                    |
|                                  v                                    |
| +-------------------------------------------------------------------+ |
| |                 Axios Service Layer (/src/services/api.js)        | |
| +-------------------------------------------------------------------+ |
+-----------------------------------------------------------------------+
```

---

## 17. Complete Data Flow Diagram

```
[ User Browser ]
       |
       |  HTTP GET/POST /api/*
       v
[ Express Server Gateway (server.ts) / FastAPI Router (main.py) ]
       |
       |  Pydantic Request Validation
       v
[ Workforce Business Service Layer (workforce_services.py) ]
       |
       |-- (Async MongoDB Query via Motor) ----> [ MongoDB Collection ]
       |
       |-- (Google GenAI API Call) -----------> [ Gemini 2.5 Flash API ]
       v
[ Formatted JSON Response Envelope ]
       |
       v
[ React UI View Re-render ]
```

---

## 18. Sequence Diagrams

### Attendance Check-in Flow
```
User             React Component           API Service          FastAPI Endpoint          MongoDB
 |                      |                      |                       |                     |
 |-- Click Check In --->|                      |                       |                     |
 |                      |-- checkIn(payload) ->|                       |                     |
 |                      |                      |-- POST /check-in ---->|                     |
 |                      |                      |                       |-- Insert Record --->|
 |                      |                      |<-- Acknowledge -----|
 |                      |<-- Return 201 JSON ---|                     |
 |                      |<-- Update State -----|                       |                     |
 |<-- Render Success ---|                      |                       |                     |
```

---

## 19. API Testing Guide using Swagger

1. Start application server via `npm run dev` or `uvicorn backend.app.main:app`.
2. Open browser and navigate to `http://localhost:3000/api/docs`.
3. Locate desired router section (e.g. `Employees`).
4. Click endpoint (e.g. `GET /api/employees`).
5. Click **Try it out**, specify filter parameters (e.g., `department=Engineering`), and click **Execute**.
6. Inspect the `200 OK` JSON response body.

---

## 20. API Testing Guide using Postman

1. Open Postman and create a New Collection: `Workforce Management API`.
2. Set Environment Variable: `baseUrl` = `http://localhost:3000/api`.
3. Add Request `Get Employees`:
   - Method: `GET`
   - URL: `{{baseUrl}}/employees`
4. Add Request `Ask AI Assistant`:
   - Method: `POST`
   - URL: `{{baseUrl}}/chat`
   - Headers: `Content-Type: application/json`
   - Body (raw JSON): `{"message": "Show high attrition risks", "role": "HR Administrator"}`
5. Execute requests and verify status codes and schema matches.

---

## 21. Deployment Steps

### Deploying to Cloud Run / Docker Container
1. Ensure `package.json` contains `"build"` and `"start"` scripts targeting `dist/server.cjs`.
2. Execute build command:
   ```bash
   npm run build
   ```
3. Docker Container Build & Run:
   ```bash
   docker build -t workforce-system .
   docker run -p 3000:3000 -e GEMINI_API_KEY="your_key" workforce-system
   ```

---

## 22. Production Checklist

- [x] All 38 REST endpoints implemented with zero TODOs or placeholders.
- [x] Async MongoDB driver (Motor) configured with high-performance state fallback.
- [x] Pydantic models validate all incoming requests and outgoing responses.
- [x] CORS middleware configured for secure cross-origin requests.
- [x] Error handles respond with standard HTTP status codes (`200`, `201`, `400`, `404`, `500`).
- [x] Gemini AI integration leverages server-side SDK execution.
- [x] Production build bundles server into standalone CJS bundle (`dist/server.cjs`).

---

## 23. Troubleshooting Guide

| Issue | Root Cause | Solution |
|---|---|---|
| `MongoDB connection warning` | MongoDB local instance is not running | App automatically falls back to in-memory state; start MongoDB via `mongod` to persist to database. |
| `Vite WS Connection Failed` | HMR is disabled in container environment | Normal behavior in Cloud Run sandbox environment; ignore console warnings. |
| `Port 3000 already in use` | Existing server process running | Kill background node process or run `killall node`. |

---

## 24. Dependency Explanation

### Python Backend Dependencies
- **`fastapi`**: Modern, fast web framework for building APIs with Python based on standard type hints.
- **`uvicorn`**: Lightning-fast ASGI server implementation.
- **`pydantic`**: Data validation and settings management using Python type annotations.
- **`motor`**: Async Python driver for MongoDB.
- **`google-genai`**: Official Google GenAI SDK for Gemini model integration.

### Frontend Node Dependencies
- **`react` & `react-dom`**: Frontend UI framework.
- **`express`**: Node server for static serving and dev API proxying.
- **`recharts`**: Data visualization library for executive analytics.
- **`lucide-react`**: Clean icon system.
- **`motion`**: High performance animations.
- **`axios`**: HTTP request library with response interceptors.
