# W2-OPS: UI not updating — runtime proof (ground truth)

Goal: prove which exact template + JS + commit the browser is executing, and whether Flask/Jinja template caching (server-side) is the real cause.

---

## 1. git rev-parse HEAD

```
23be5fe9aa8a0b8bdf42074b4083de739b51a1fc
```

---

## 2. lsof -i :5000 -n -P

```
COMMAND   PID      USER   FD   TYPE            DEVICE SIZE/OFF NODE NAME
Python  28458 autojenny   11u  IPv4 0x47f7c8214409fdb      0t0  TCP 127.0.0.1:5000 (LISTEN)
Python  65982 autojenny   11u  IPv4 0x47f7c8214409fdb      0t0  TCP 127.0.0.1:5000 (LISTEN)
Python  65982 autojenny   14u  IPv4 0x47f7c8214409fdb      0t0  TCP 127.0.0.1:5000 (LISTEN)
```

---

## 3. ps -p <PID> -o pid,ppid,command for each PID listening on 5000

```
  PID  PPID COMMAND
28458 28452 /opt/homebrew/Cellar/python@3.13/3.13.2/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python unified_app.py
  PID  PPID COMMAND
65982 28458 /opt/homebrew/Cellar/python@3.13/3.13.2/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python unified_app.py
```

---

## 4. curl -i http://localhost:5000/api/diag/runtime-signature

```
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.13.2
Date: Wed, 25 Feb 2026 15:23:27 GMT
Content-Type: application/json
Content-Length: 893
Cache-Control: no-store, max-age=0
Pragma: no-cache
Access-Control-Allow-Origin: http://127.0.0.1:3000
Access-Control-Allow-Credentials: true
Vary: Origin
Connection: close

{
  "cwd": "/Users/autojenny/Documents/projects/blog",
  "debug": true,
  "env": null,
  "git_head": "23be5fe9aa8a0b8bdf42074b4083de739b51a1fc",
  "git_short": "23be5fe",
  "home_governance_js_abs_path": "/Users/autojenny/Documents/projects/blog/static/js/home_governance.js",
  "home_governance_js_mtime": 1772032482,
  "home_governance_js_sha256": "8de9295763b7a1a4156859afe9ea50472902db59970e49de02fb545645996876",
  "home_governance_js_sha_short": "8de9295763b7",
  "index_sha_short": "e869c3670481",
  "index_template_abs_path": "/Users/autojenny/Documents/projects/blog/templates/index.html",
  "index_template_mtime": 1772032374,
  "index_template_sha256": "e869c367048196760af83396699be61f1c53041fc3f4030f558404b8dc6fda5c",
  "jinja_auto_reload": true,
  "pid": 65982,
  "send_file_max_age_default": null,
  "server_time_utc": "2026-02-25T15:23:27Z",
  "templates_auto_reload": true
}
```

---

## 5. curl -s http://localhost:5000/api/diag/runtime-signature | jq

```json
{
  "cwd": "/Users/autojenny/Documents/projects/blog",
  "debug": true,
  "env": null,
  "git_head": "23be5fe9aa8a0b8bdf42074b4083de739b51a1fc",
  "git_short": "23be5fe",
  "home_governance_js_abs_path": "/Users/autojenny/Documents/projects/blog/static/js/home_governance.js",
  "home_governance_js_mtime": 1772032482,
  "home_governance_js_sha256": "8de9295763b7a1a4156859afe9ea50472902db59970e49de02fb545645996876",
  "home_governance_js_sha_short": "8de9295763b7",
  "index_sha_short": "e869c3670481",
  "index_template_abs_path": "/Users/autojenny/Documents/projects/blog/templates/index.html",
  "index_template_mtime": 1772032374,
  "index_template_sha256": "e869c367048196760af83396699be61f1c53041fc3f4030f558404b8dc6fda5c",
  "jinja_auto_reload": true,
  "pid": 65982,
  "send_file_max_age_default": null,
  "server_time_utc": "2026-02-25T15:23:27Z",
  "templates_auto_reload": true
}
```

---

## 6. curl -i http://localhost:5000/ | head -n 40 (prove the HTML comment exists)

```
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.13.2
Date: Wed, 25 Feb 2026 15:23:28 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 79143
Cache-Control: no-store, no-cache, must-revalidate, max-age=0
Pragma: no-cache
Expires: 0
Access-Control-Allow-Origin: http://127.0.0.1:3000
Access-Control-Allow-Credentials: true
Vary: Origin
Connection: close

<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BlogForge - Unified CMS</title>
    
    <!-- Static Assets -->
    
    
    <!-- CDN Assets -->
    
    <!-- External CDN assets -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>

    
    <!-- CSS Assets -->
    
        <link rel="stylesheet" href="/static/css/shared/dark-theme.css">
        <link rel="stylesheet" href="/static/css/shared.css">
        
    
        <!-- Blueprint-specific CSS -->
        
            <link rel="stylesheet" href="/static/css/dist/main.css">
```

---

## 7. curl -s http://localhost:5000/ | grep -n "RUNTIME_STAMP"

```
1892:    <!-- RUNTIME_STAMP git=23be5fe pid=65982 index_sha=e869c3670481 js_sha=8de9295763b7 time=2026-02-25T15:23:29Z -->
```

---

## 8. Screenshot path (local)

Screenshot showing the Governance modal header with the Build stamp line visible:

**Screenshot path:** _(add path after capturing, e.g. `screenshots/w2_ops_governance_build_stamp.png`)_

---

## Decision rule

- **If the Build stamp line shows the new git SHA + new index/js sha, but the UI still appears “old”** → the issue is **render logic / DOM** (not caching).
- **If the Build stamp shows an old SHA or debug=false with jinja_auto_reload=false** → the issue is **server-side template caching / not restarted** (clean browser is irrelevant).

**Current proof:** Server is running from this repo (cwd, pid 65982), commit 23be5fe, debug=true, templates_auto_reload=true, jinja_auto_reload=true; homepage HTML contains RUNTIME_STAMP at line 1892. So the **server is serving the current commit and template**; any “UI not changing” is either browser cache (old JS) or front-end render logic, not server-side template caching.
