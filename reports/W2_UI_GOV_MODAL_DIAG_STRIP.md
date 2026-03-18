# W2 UI — Governance Modal Diagnostics Strip (Instruction Set A)

**Created:** 2026-02-25  
**Purpose:** Prove in-browser what JS is running and why render might fail. Diagnostics strip is always visible at the top of the Governance panel.

---

## 1. Screenshot: Diagnostics strip visible

**Path:** `reports/screenshots/W2_UI_GOV_MODAL_DIAG_STRIP.png`

*(Capture the homepage with the Governance panel open. The Diagnostics line appears at the top of the panel with: Build, Fetched, Payload hash, Rendered slots, Render error, and the "Force refresh" button.)*

If the strip is working, it will show something like:
- **Build:** git short hash and PID (from `/api/diag/runtime-signature`) or "…" until loaded
- **Fetched:** ISO timestamp of last governance-summary fetch
- **Payload hash:** first 8 chars of hash of the JSON response
- **Rendered slots:** count of table rows rendered
- **Render error:** "—" when no error, or truncated exception message
- **Force refresh** button

---

## 2. `curl -i` output for runtime-signature

```http
HTTP/1.1 200 OK
Server: Werkzeug/3.1.3 Python/3.13.2
Date: Wed, 25 Feb 2026 16:19:33 GMT
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
  "home_governance_js_mtime": 1772036344,
  "home_governance_js_sha256": "c2a2ff26e1b474ba28932e749ed2a76dd26d032402c5b0ec253dc18ad334dd16",
  "home_governance_js_sha_short": "c2a2ff26e1b4",
  "index_sha_short": "e869c3670481",
  "index_template_abs_path": "/Users/autojenny/Documents/projects/blog/templates/index.html",
  "index_template_mtime": 1772032374,
  "index_template_sha256": "e869c367048196760af83396699be61f1c53041fc3f4030f558404b8dc6fda5c",
  "jinja_auto_reload": true,
  "pid": 65982,
  "send_file_max_age_default": null,
  "server_time_utc": "2026-02-25T16:19:33Z",
  "templates_auto_reload": true
}
```

---

## 3. Screenshot: “Broken” state (optional)

**Path:** `reports/screenshots/W2_UI_GOV_MODAL_DIAG_STRIP_BROKEN.png`

*(If you observe a broken state, capture it and save here. The Diagnostics strip will show one of:*
- *Render error: &lt;truncated message&gt;*
- *Rendered slots: 0*
- *Fetch error box with status code, URL, and first 300 chars of response*

*If the UI is working and no broken state is observed, this screenshot can be omitted or noted as "N/A — no broken state observed.")*

---

## Implementation summary (Instruction Set A)

| Item | Done |
|------|------|
| **A1** Diagnostics strip at top of modal with Build, Fetched, Payload hash, Rendered slots, Render error | ✓ |
| **A1** `loadGovernancePanel()` and `renderPanel()` wrapped in try/catch; errors shown in strip | ✓ |
| **A2** Non-200 or JSON parse failure → visible error box in modal (status, first 300 chars, URL) | ✓ |
| **A3** "Force refresh" button calls `loadGovernancePanel({ force: true })`, updates Fetched and payload hash | ✓ |

Payload hash uses a simple synchronous hash (first 8 hex chars); Build is filled asynchronously from `/api/diag/runtime-signature`.
