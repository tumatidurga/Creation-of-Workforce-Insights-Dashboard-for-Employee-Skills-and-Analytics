# Deployment Guide — AI Workforce Management Automation System

Free, no-payment deployment where **every** feature works, including the APScheduler
automation engine. No code changes are required to follow this guide.

---

## Why not Vercel / Netlify Functions for the backend

The automation engine is `AsyncIOScheduler` (APScheduler) started inside the FastAPI
lifespan. It needs a **process that stays alive between requests**. Serverless platforms
freeze the process after each response, so:

- `notification_maintenance` has **no HTTP trigger endpoint at all** — it exists only as a
  scheduled job. On serverless it would simply never run.
- The other four jobs do have trigger endpoints, but they require an HR JWT that expires in
  60 minutes and nothing in the system can refresh it unattended.

So the backend must go on a platform that runs a **long-lived process**. The frontend is a
static bundle and can go anywhere.

Also no longer free (checked before writing this): Hugging Face Docker Spaces (now needs a
paid tier for always-on) and Koyeb (free web services removed).

---

## Target architecture

| Piece | Platform | Free tier |
|---|---|---|
| FastAPI backend + APScheduler | Render **Web Service** | 750 instance-hours/mo, 0.1 CPU, 512 MB |
| React build output | Render **Static Site** | unlimited, no spin-down |
| Database | MongoDB Atlas (existing) | M0 512 MB |
| Keep-alive pinger | cron-job.org | free, every 10 min |

---

## Step 0 — Fix two blockers before you deploy

**Blocker 1: the cluster hostname.** The connection string you first pasted used
`workforcecluster.znvqva8.mongodb.net`. The working host is
`workforcecluster.c9wibir.mongodb.net`. Use the `c9wibir` one — verified against the live
cluster. Copy it from Atlas → Connect → Drivers if in doubt.

**Blocker 2: `JWT_SECRET_KEY` must be set explicitly.** If it is unset the app generates a
random key at boot, which means every restart invalidates every issued token — users get
logged out on each cold start. Generate one once and keep it fixed:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

The value already in your local `.env` is fine to reuse.

---

## Step 1 — MongoDB Atlas network access

Render free tier has **no static outbound IP**, so IP allow-listing individual addresses
will not work.

1. Atlas → **Network Access** → **Add IP Address**
2. Enter `0.0.0.0/0`, comment `Render free tier (dynamic egress)`
3. Confirm

This is the standard trade-off on free hosting. Your protection is the database user
credential, which is why rotating it matters (see Security below).

Also confirm under **Database Access** that `saikavyakalyanig_db_user` has
`readWrite` on `workforce_db`.

---

## Step 2 — Backend as a Render Web Service

Push the repo to GitHub, then Render → **New** → **Web Service** → connect the repo.

| Field | Value |
|---|---|
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT` |
| Instance type | **Free** |
| Health check path | `/api/health` |

**Do not add `--workers N`.** Multiple workers means multiple APScheduler instances, and
every job would fire N times — duplicate notifications, duplicate payroll rows. Single
worker is both correct and all that 0.1 CPU can drive.

Environment variables (Render → Environment):

```
MONGODB_URL=mongodb+srv://saikavyakalyanig_db_user:<password>@workforcecluster.c9wibir.mongodb.net/
DATABASE_NAME=workforce_db
JWT_SECRET_KEY=<the hex string from Step 0>
AUTH_BOOTSTRAP_PASSWORD=HR@Demo2026!
HR_ADMIN_TEST_PASSWORD=HR@Demo2026!
EMPLOYEE_TEST_PASSWORD=EMP000001
AUTOMATION_ENABLED=True
API_V1_STR=/api
PROJECT_NAME=AI Workforce Management Automation System
```

Do **not** set `PORT` — Render injects it. Leave `GEMINI_API_KEY` unset unless you have a
key; the code degrades gracefully without it.

### Verifying the backend is actually up

Visiting the service root URL returns:

```json
{"detail":"Not Found"}
```

**That is expected and is not an error.** The app registers no `GET /` route — that JSON is
FastAPI's own 404 body, which only a *running* FastAPI process can produce. A dead service
returns a Render error page instead. The real check is:

```bash
curl https://<your-service>.onrender.com/api/health
```

Expect `status: connected`, `database: workforce_db`, `AUTOMATION_ENABLED: true`.
Then check the Render log stream for `Automation Engine: ENABLED`.

---

## Step 3 — Frontend as a Render Static Site

Render → **New** → **Static Site** → same repo.

| Field | Value |
|---|---|
| Build command | `npm --prefix frontend install && npm --prefix frontend run build` |
| Publish directory | `frontend/dist` |

Environment variable:

```
VITE_API_URL=https://<your-backend-service>.onrender.com/api
```

`VITE_*` values are **baked into the bundle at build time**, not read at runtime. If you
change this you must trigger a rebuild — a restart does nothing.

Add a rewrite so client-side routing works on refresh:

Render → Redirects/Rewrites → Source `/*` → Destination `/index.html` → Action **Rewrite**
(not Redirect).

---

## Step 4 — CORS

Back on the **backend** service, add:

```
CORS_ALLOWED_ORIGINS=https://<your-static-site>.onrender.com
```

No trailing slash. Save and let it redeploy. Without this the browser blocks every API
call and the UI looks empty even though the backend is healthy.

---

## Step 5 — Keep the backend awake (this is what makes automation reliable)

A free Render web service **spins down after 15 minutes with no inbound traffic**. While
spun down the process is gone, so APScheduler is gone — any job scheduled during that
window never fires and is not replayed on wake.

Fix: ping it continuously.

1. Go to <https://cron-job.org> and create a free account
2. New cronjob → URL `https://<your-service>.onrender.com/api/health`
3. Schedule: **every 10 minutes** (safely under the 15-min idle timeout)
4. Enable, save

### Does 24/7 fit in 750 instance-hours?

| | Hours |
|---|---|
| Free monthly allowance | 750 |
| A 31-day month, always on | 744 |
| Spare | **6** |

It fits, but with only ~6 hours of headroom — and that is for **one** service. Keep the
frontend as a *Static Site* (static sites do not consume instance-hours) and do not add a
second web service on the same account, or you will blow the quota mid-month and the
backend will be suspended until it resets.

---

## Step 6 — Verify every feature

Open the static site URL and check, in order:

1. **Login** as HR — confirms Atlas connectivity + JWT signing
2. **Employees** list loads — confirms read path and pagination
3. **Apply for leave** as an employee, then **Leave Management** as HR — the new request
   must appear **at the top of the list** (this is what the `.sort("_id", -1)` fix in
   `LeaveService.get_all` guarantees), with a working Approve/Reject button
4. **Shift swap** request → HR **Shift Management** — same newest-first behaviour
5. **Attendance** check-in/check-out
6. **Notifications** bell populates
7. Leave the tab for ~20 minutes with the cron pinger active, come back, reload — you
   should **not** be logged out (proves `JWT_SECRET_KEY` is pinned) and there should be no
   cold-start delay (proves the pinger works)

Credentials:

| Role | Username | Password |
|---|---|---|
| HR admin | as seeded in your `employees` collection | `HR@Demo2026!` |
| Employee | their Employee ID | their own Employee ID (e.g. `EMP000001`) |

---

## Step 7 — The one honest compromise

Free Render gives you **0.1 CPU**. That is roughly a tenth of a core. Consequences:

- First request after a deploy takes ~30–60 s while Python imports and Mongo connects
- Large report generation and the heavier automation jobs are slow but do complete
- Concurrent users will queue

Nothing fails, but nothing is fast. There is no free tier anywhere that gives a full core
plus an always-on process — this is the actual floor for "free and everything works".

### If 0.1 CPU is too slow: Oracle Cloud Always Free

Genuinely free forever (not a trial), and far more capable: 4 ARM cores / 24 GB RAM.
Trade-off — it is a bare VM, so you do it yourself: provision Ubuntu, open port 80/443,
`pip install -r requirements.txt`, run uvicorn under `systemd`, put nginx in front, and get
TLS from certbot. No spin-down, so **no keep-alive pinger needed** and automation is
strictly more reliable than on Render. Signup requires a card for identity verification
(not charged on Always Free shapes).

Use Render if you want it live today. Use Oracle if you want it fast and permanent.

---

## Failure modes and what they mean

| Symptom | Cause | Fix |
|---|---|---|
| `{"detail":"Not Found"}` at root URL | Normal — no `GET /` route | Use `/api/health` |
| Render error page (not JSON) at root | Service is actually down | Read the log stream |
| `/api/health` says `disconnected` | Atlas IP rules or bad `MONGODB_URL` | Step 1; check `c9wibir` host |
| UI loads but all lists empty | CORS | Step 4 |
| Network tab shows calls to `localhost:8000` | `VITE_API_URL` missing at build | Set it, then **rebuild** |
| Logged out after every cold start | `JWT_SECRET_KEY` unset | Step 0 |
| 404 on refresh of a sub-route | No SPA rewrite | Step 3 rewrite rule |
| Automation jobs silently skipped | Service spun down | Step 5 pinger |
| Each notification arrives twice | `--workers` > 1 | Remove the flag |
| Backend suspended mid-month | 750 instance-hours exhausted | Only one web service per account |

---

## Security — do these before sharing the URL

1. **Rotate the Atlas password.** `Infosys123` has been shared in plaintext (in chat and in
   this repo's local `.env`). Change it in Atlas → Database Access, then update
   `MONGODB_URL` on Render.
2. **Every employee's password equals their own Employee ID**, and Employee IDs are visible
   in the UI. Any logged-in user can therefore log in as any other employee. Acceptable for
   a demo; do not put real data behind it.
3. **`scripts/token.txt` is a committed JWT.** It is expired and signed with a different
   key, so it is not currently exploitable, but it should not be in version control.
4. `.env` is gitignored (`.gitignore:5`) and has never been committed — verified against the
   full git history. Keep it that way; put production values in Render's env panel only.

---

## Condensed checklist

- [ ] `JWT_SECRET_KEY` generated and pinned
- [ ] `MONGODB_URL` uses `c9wibir`
- [ ] Atlas Network Access allows `0.0.0.0/0`
- [ ] Render Web Service: build/start commands set, health check `/api/health`, no `--workers`
- [ ] All backend env vars set
- [ ] `/api/health` returns `connected`
- [ ] Log shows `Automation Engine: ENABLED`
- [ ] Render Static Site built from `frontend/dist`
- [ ] `VITE_API_URL` set, then rebuilt
- [ ] SPA rewrite `/*` → `/index.html`
- [ ] `CORS_ALLOWED_ORIGINS` set on the backend
- [ ] cron-job.org pinging `/api/health` every 10 min
- [ ] Only one web service on the account (quota)
- [ ] New leave request appears at top of HR's Leave Management
- [ ] Atlas password rotated
