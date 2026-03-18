# Infrastructure Map (Unified Cockpit Baseline)

**Generated:** 2026-03-18  
**Scope:** Local services on the Mac Studio, plus Cloudflare Tunnel routing for `13edinburgh.com`.

## 1. The Current Port Registry

| Service Name | Port | Working Directory | Public URL(s) | Status |
|---|---:|---|---|---|
| Next.js (no13edinburgh UI) | `3001` | `/Users/autojenny/Documents/projects/no13edinburgh` | `https://13edinburgh.com`, `https://staging.13edinburgh.com` | Active (listening) |
| LawTutor civil-law API (FastAPI/uvicorn) | `8000` | `/Users/autojenny/Documents/projects/lawtutor/api` | `https://civil-law-api.13edinburgh.com` | Active (listening) |
| AI Hub / AI Governance Hub (FastAPI/uvicorn) | `9000` | `/Users/autojenny/Documents/ai-hub` | `http://127.0.0.1:9000` (local only; not currently tunneled to public) | Active (listening; bound to `127.0.0.1`) |
| PostgreSQL | `5432` | n/a | n/a | Active (listening on `127.0.0.1`) |
| Cloudflare Tunnel local listeners | `20241`, `20242` | n/a (cloudflared) | n/a | Active (tunnel endpoints; not public) |
| BlogForge unified_app.py (Flask) | `5000` | `/Users/autojenny/Documents/projects/blog` | n/a (not currently tunneled) | **Expected but currently not listening** |
| Nginx | `80/443` | `/opt/homebrew/etc/nginx` | n/a | No listener detected (not currently serving) |
| Ollama | `11434` | n/a | n/a | Active (local) |

### 1.1 Process notes (for port 9000)
- `uvicorn app.main:create_app --reload --host 127.0.0.1 --port 9000` is running with a reload worker + a forked child process.
- Both processes are expected under `--reload` and should be treated as an intentional multi-process footprint (not necessarily “ghosts”).

## 2. The Routing Path

### 2.1 Public domain routing (Cloudflare Tunnel)
Cloudflare Tunnel is routing requests for these hostnames back into local ports:

| Hostname | Tunnel Config | Local Service Target |
|---|---|---|
| `13edinburgh.com` | `/Users/autojenny/Documents/projects/no13edinburgh/.cloudflared/config.yml` | `http://localhost:3001` |
| `civil-law-api.13edinburgh.com` | `/Users/autojenny/Documents/projects/no13edinburgh/.cloudflared/config.yml` | `http://localhost:8000` |
| `staging.13edinburgh.com` | `/Users/autojenny/Documents/projects/no13edinburgh/.cloudflared/config-staging.yml` | `http://localhost:3001` |

### 2.2 Request flow diagram

```text
Browser
  |
  v
Public DNS (Cloudflare)
  |
  v
Cloudflare edge -> cloudflared tunnel
  |
  v
Local tunnel listener (127.0.0.1:20241 or 127.0.0.1:20242)
  |
  v
Local Python/Node process:
  - localhost:3001 (Next.js UI) for 13edinburgh.com (+ staging)
  - localhost:8000 (LawTutor API) for civil-law-api.13edinburgh.com
```

### 2.3 BlogForge / unified_app.py exposure
- `unified_app.py` is configured to run on port `5000` (see Section 4), but there is **no active listener on `:5000` right now**.
- The current Cloudflare Tunnel ingress rules do **not** route `13edinburgh.com` traffic to `:5000`.

## 3. The “Ghost” List (Orphans / Redundant UIs)

1. **BlogForge unified_app expected server is not currently running**
   - Expected by `start_blog.sh` / `start-production.sh`: `http://localhost:5000/health`
   - Observed: no process listening on `:5000`
2. **Multiple uvicorn processes on `:9000`**
   - Expected under `--reload` (PID footprint is redundant but functional)
3. **Two cloudflared tunnels active simultaneously**
   - One tunnel for production hostname rules, one for staging rules
   - Not inherently wrong; treat as deliberate environment separation

### 3.1 Commands to terminate (only if you want to decommission)
The audit did not find true orphaned services (everything listening is intentionally serving a project), so the commands below are for decommissioning on purpose:
1. Stop AI Hub (port `9000`):
   - `pkill -f "uvicorn app.main:create_app"`
2. Stop LawTutor civil-law API (port `8000`):
   - `pkill -f "uvicorn app:app --port 8000"`
3. Stop Next.js UI (port `3001`):
   - `pkill -f "next dev -p 3001"`
4. Stop both cloudflared tunnels:
   - `pkill -f "cloudflared tunnel --config /Users/autojenny/Documents/projects/no13edinburgh/.cloudflared/"`

## 4. Application Entry-Point Audit

### 4.1 BlogForge unified_app.py
- Entry point: `/Users/autojenny/Documents/projects/blog/unified_app.py`
- Runtime config (hard-coded):
  - `app.run(debug=True, port=5000)`
- Current state:
  - Port `5000` is not listening, so unified_app is not reachable locally right now.

### 4.2 AI Hub
- Entry point (uvicorn): `app.main:create_app`
- Runtime config (from process args):
  - `--host 127.0.0.1 --port 9000 --reload`

### 4.3 Next.js UI
- Entry point: `next dev -p 3001`

### 4.4 Civil-law API (LawTutor)
- Entry point: `python -m uvicorn app:app --host 0.0.0.0 --port 8000`

## 5. Domain & Redirection Audit (13edinburgh.com)

- There is **no nginx proxy listener detected** for `80/443` on this host right now.
- `13edinburgh.com` traffic is being handled by **Cloudflare Tunnel**, which forwards to:
  - `localhost:3001` for UI
  - `localhost:8000` for the civil-law API subdomain

## 6. Security & Remote Access Readiness

### 6.1 unified_app.py
- No basic-auth or password middleware detected in `unified_app.py`.
- `create_app()` config includes CSRF/WTF toggles and CORS, but nothing that provides request authentication for remote Cockpit access.

### 6.2 AI Hub
- `ai-hub/app/main.py` shows only timing middleware in the file reviewed.
- `ai-hub/app/authority.py` indicates “work mode is informational only” and does not enforce remote authentication.

## 7. Cockpit Readiness Implications (for your next step)
- The fastest safe path to a “Unified Cockpit” is:
  1. Re-introduce BlogForge at the expected `localhost:5000` (or route it explicitly)
  2. Add Cockpit-level password/auth in the Cockpit layer (reverse proxy or in-app middleware)
  3. Keep Cloudflare Tunnel ingress as the single public entry point

## 8. Unified Cockpit (AI Hub) — Single Point of Entry Proposal

### 8.1 Recommended “single point of entry”
- AI Hub already exposes a cockpit-like control surface:
  - `GET /` redirects to `GET /dashboard`
  - Port: `9000`
  - Local URL: `http://127.0.0.1:9000/` (then `/dashboard`)

### 8.2 Public cockpit target hostname
- Proposed: `hub.13edinburgh.com`
- Current status: no `hub.*` tunnel ingress rule exists yet (only `13edinburgh.com`, `civil-law-api.13edinburgh.com`, and `staging.13edinburgh.com`).

### 8.3 Cloudflare Tunnel guide (hub.13edinburgh.com -> AI Hub)
1. Update the Cloudflare Tunnel ingress configuration:
   - Edit: `/Users/autojenny/Documents/projects/no13edinburgh/.cloudflared/config.yml`
   - Add an ingress rule (keep it above the catch-all):
     - `hostname: hub.13edinburgh.com`
     - `service: http://localhost:9000`
2. Restart the tunnel process if needed:
   - The tunnel currently runs via:
     - `/Users/autojenny/Documents/projects/no13edinburgh/.cloudflared/config.yml`
3. Verify locally:
   - `curl -I http://127.0.0.1:9000/dashboard`
   - Then verify via public hostname after Cloudflare DNS propagation.

### 8.4 Zero Trust password protection (recommended approach)
Cloudflare “Zero Trust” protection is implemented via **Cloudflare Access policies**, not via a password prompt inside the tunnel.

Recommended policy shape:
1. In Cloudflare Dashboard -> Zero Trust:
   - Create an **Access application** for `hub.13edinburgh.com`
2. Add an **Access policy** requiring authentication:
   - Option A (human login): allow specific emails/groups; requires Cloudflare user login.
   - Option B (service token): require a Cloudflare service token (acts like a password for automation).
3. Ensure the policy is applied to the application and that it blocks unauthenticated requests.

