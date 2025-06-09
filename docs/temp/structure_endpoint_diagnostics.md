# 🚨 CRITICAL RULE: PREVENT ASSISTANT HANGS 🚨

**DO NOT RUN FOREGROUND SERVER COMMANDS FROM THE ASSISTANT**
- Always use background execution (`nohup`, `&`), log output, and store PID.
- Never run `flask run`, `python -m flask run`, or any server process in the foreground.
- Always redirect output to a log file and store the process ID for later management.
- Before running any long-running or server process, check and document the command here.
- If a command could hang, do not run it—document the risk and suggest a safe alternative.

---

# Structure Endpoint Diagnostics

## Issue Summary
- Frontend is making requests to `/structure/plan` but getting 404 errors
- According to API endpoint orthodoxy review, correct endpoint should be `/api/v1/structure/plan`

## Server Management Issue
### Problem
- Server keeps hanging when started with `flask run`
- This is likely due to the server waiting for input or being in an interactive mode
- The hanging occurs because the server process is not properly detached from the terminal

### Workaround
1. Use `nohup` to detach the process from the terminal
2. Redirect output to a log file
3. Use `&` to run in background
4. Store PID for later cleanup

### Updated Server Start Command
```bash
nohup python3 -m flask run --no-reload > flask.log 2>&1 &
echo $! > flask.pid
```

### Server Stop Command
```bash
if [ -f flask.pid ]; then
    kill $(cat flask.pid)
    rm flask.pid
fi
```

## Current State (as of last check)
1. Frontend Code (`app/static/js/workflow/structure_stage.js`):
   - Making requests to `/api/v1/structure/plan`
   - Button click handler properly configured
   - Response handling logic in place

2. Backend Routes:
   - API Blueprint registered with `/api/v1` prefix in `app/__init__.py`
   - Endpoints correctly defined in `app/api/routes.py`:
     - `/structure/plan` (POST)
     - `/structure/save/<post_id>` (POST)
     - `/posts/<post_id>/structure` (GET)
   - No duplicate endpoints in `app/blog/routes.py`

3. Blueprint Registration:
   - `app/api/__init__.py`: Creates APIBlueprint instance
   - `app/api/base.py`: Defines APIBlueprint class with enhanced functionality
   - `app/__init__.py`: Registers blueprint with `/api/v1` prefix

## Diagnostic Steps Taken

### 1. Frontend Request Verification
- [x] Confirmed frontend is making requests to correct endpoint
- [x] Verified request payload format
- [x] Checked error handling

### 2. Backend Route Verification
- [x] Confirmed endpoint exists in `app/api/routes.py`
- [x] Verified route registration
- [x] Checked for duplicate route definitions
- [x] Confirmed no endpoints in `app/blog/routes.py`

### 3. Blueprint Registration Check
- [x] Verified API blueprint registration
- [x] Checked URL prefix configuration
- [x] Confirmed no conflicting route registrations

## Current Issues
1. Route Prefix:
   - API blueprint registered with `/api/v1` prefix
   - Routes in `app/api/routes.py` also include `/api/v1`
   - This creates double-prefixed URLs (e.g., `/api/v1/api/v1/structure/plan`)

2. Server Management:
   - Server restart process needs improvement
   - Need reliable way to check server status
   - Need automated cleanup of stale processes

## Next Steps
1. [ ] Remove duplicate `/api/v1` prefix from routes in `app/api/routes.py`:
   - [x] Update `/structure/plan` route
   - [x] Update `/structure/save/<post_id>` route
   - [x] Update `/posts/<post_id>/structure` route

2. [ ] Update server management script with new workaround
3. [ ] Test server start/stop with new approach
4. [ ] Test endpoints with curl:
   - [ ] Test `/api/v1/structure/plan` with curl
   - [ ] Test `/api/v1/structure/save/<post_id>` with curl
   - [ ] Test `/api/v1/post/<post_id>/structure` with curl

5. [ ] Update frontend if necessary:
   - [ ] Verify frontend requests match new endpoint structure
   - [ ] Update any hardcoded URLs if needed

## Test Results
(To be filled as we progress)

## Notes
- Keep track of all changes made
- Document any new issues discovered
- Record successful fixes
- Maintain list of remaining tasks
- Always use documented server management procedures
- Never use `flask run` directly - always use the management script 