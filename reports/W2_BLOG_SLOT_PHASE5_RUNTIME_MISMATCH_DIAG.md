# W2 Blog Slot Phase 5 — Runtime mismatch diagnosis

Goal: Explain why the UI might not reflect commits 89bcdb15 and 23be5fe9, and ensure the running app serves the new backend + new JS.

---

## A) Repo state vs running server

### A1. Repo HEAD

```bash
git rev-parse HEAD
git log -5 --oneline
```

**Output:**

```
23be5fe9aa8a0b8bdf42074b4083de739b51a1fc
---
23be5fe9 W2: governance panel opens full calendar and shows blog slot actions consistently
89bcdb15 W2: attach converted post to blog weekly slot and render blog slot from slot metadata
e1cc9587 W2: model blog as weekly slot; populate blog slot on conversion; remove synthetic blog row
c2e4935b W2: allow blog item_type in calendar_week_items
f897641f W2: ensure seeded weekly items get scheduled_date; homepage next-7-days shows week content
```

### A2. Local changes

```bash
git status -sb
```

**Output:**

```
## main...origin/refactor/authoring-modularization [ahead 8]
 M logs/launchd_monitor.err
 M logs/launchd_posting.err
?? package-lock.json
?? package.json
?? utils/publishing/
```

---

## B) Process serving port 5000

### B1. PID / command bound to :5000

```bash
lsof -nP -iTCP:5000 -sTCP:LISTEN
ps -fp "$(lsof -t -iTCP:5000 -sTCP:LISTEN)"
```

**Output (lsof):**

```
COMMAND   PID      USER   FD   TYPE            DEVICE SIZE/OFF NODE NAME
Python  28458 autojenny   11u  IPv4 0x47f7c8214409fdb      0t0  TCP 127.0.0.1:5000 (LISTEN)
Python  43144 autojenny   11u  IPv4 0x47f7c8214409fdb      0t0  TCP 127.0.0.1:5000 (LISTEN)
Python  43144 autojenny   14u  IPv4 0x47f7c8214409fdb      0t0  TCP 127.0.0.1:5000 (LISTEN)
```

**Output (ps for PID 43144):**

```
  PID COMMAND
43144 /opt/homebrew/Cellar/python@3.13/3.13.2/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python unified_app.py
```

(28458: same command `Python unified_app.py`.)

### B2. Working directory of server process

```bash
pwdx "$(lsof -t -iTCP:5000 -sTCP:LISTEN)" || true
```

**Output:** `pwdx` not available on this macOS (no /proc). Cwd obtained via `lsof -p 43144`:

```
Python  43144 autojenny  cwd   DIR  1,17  3040  378786198 /Users/autojenny/Documents/projects/blog
```

**Conclusion:** The process serving :5000 is running from the correct repo path: `/Users/autojenny/Documents/projects/blog`, running `unified_app.py`. So the server is not an old checkout.

---

## C) Backend behaviour (no browser)

```bash
curl -s http://localhost:5000/api/home/governance-summary | jq '{window_start,window_end,scheduled_slots: (.scheduled_slots|map({role,item_type,slot_id,scheduled_date,post_id,summary}))}'
```

**Output:**

```json
{
  "window_start": "2026-02-25",
  "window_end": "2026-03-04",
  "scheduled_slots": [
    {
      "role": "blog",
      "item_type": "blog",
      "slot_id": 503,
      "scheduled_date": "2026-02-26",
      "post_id": 729,
      "summary": "Irish tartans"
    },
    {
      "role": "weekly_word",
      "item_type": "weekly_word",
      "slot_id": 423,
      "scheduled_date": "2026-03-02",
      "post_id": null,
      "summary": "wheesht"
    },
    {
      "role": "weekly_phrase",
      "item_type": "weekly_phrase",
      "slot_id": 490,
      "scheduled_date": "2026-03-03",
      "post_id": null,
      "summary": "Pure dead brilliant"
    }
  ]
}
```

**Conclusion:** Backend matches Phase 4: scheduled_slots includes a blog row with `item_type: "blog"`, non-null `scheduled_date` (2026-02-26), non-null `post_id` (729), and `summary` "Irish tartans". So if the UI does not show this, the cause is frontend (caching or script not loading).

---

## D) Browser loading the new JS

### D1. Script URL (from DevTools)

In the running UI, open DevTools Console and run:

```js
[...document.querySelectorAll('script[src]')].map(s=>s.src)
```

Copy the URL that contains `home_governance.js`. Typical value: `http://localhost:5000/static/js/home_governance.js` (or with query string after cache-busting).

### D2. Fingerprint of JS served at that URL

Using URL `http://localhost:5000/static/js/home_governance.js`:

```bash
curl -s 'http://localhost:5000/static/js/home_governance.js' | shasum -a 256
```

**Output:**

```
08518168e550a5ded63a0b65d94cefb0799796b6e5b87f5edd96221a7b43de89  -
```

### D3. Fingerprint of local file at HEAD

```bash
shasum -a 256 static/js/home_governance.js
```

**Output:**

```
08518168e550a5ded63a0b65d94cefb0799796b6e5b87f5edd96221a7b43de89  static/js/home_governance.js
```

**Conclusion:** Hashes match. The server is serving the current `home_governance.js` from the repo. If the UI still looked old, the cause would be browser cache (e.g. old script cached without query string). Cache-busting is added in E below.

---

## E) Fix: cache-busting

- **Grep for script tag:**

```bash
rg -n "home_governance\.js" templates static | cat
```

**Output:**

```
templates/index.html:997:    <script src="{{ url_for('static', filename='js/home_governance.js') }}"></script>
```

(After fix, line 997 includes `?v=20260225_1`.)

- **Change made (E2):** In `templates/index.html` at line 997, the script src was updated to append a version query param: `?v=20260225_1`, so the browser fetches a new URL when the template is deployed and avoids using an old cached `home_governance.js`.
- **File containing the tag:** `templates/index.html` (line 997).

---

## F) Restart + final verification

### F1. After restart, backend check

Restart the service (e.g. stop and start `unified_app.py` or launchd). Then run:

```bash
curl -s http://localhost:5000/api/home/governance-summary | jq '{window_start,window_end,scheduled_slots: (.scheduled_slots|map({role,item_type,slot_id,scheduled_date,post_id,summary}))}'
```

Expected: same shape as in C, with blog row having non-null `scheduled_date`, `post_id`, and summary.

### F2. Screenshot

Refresh the UI (hard refresh if needed: Cmd+Shift+R or Ctrl+Shift+R). Capture one screenshot showing:

- weekly_word + weekly_phrase + blog rows present in the “Next 7 days” table
- blog row shows a scheduled date and “Open Post”

**Screenshot path:** _(add path here after saving, e.g. `screenshots/w2_phase5_governance_panel.png`)_

---

## Summary

| Check | Result |
|-------|--------|
| Repo HEAD | 23be5fe9 (Phase 4 frontend commit) |
| Server process | Python `unified_app.py`, cwd = this repo |
| Backend curl | Correct: blog slot with post_id 729, summary "Irish tartans" |
| JS hash (served vs local) | Match: `08518168e55...` |
| Root cause if UI was wrong | Browser cache of `home_governance.js` (no query param) |
| Fix applied | Cache-busting `?v=20260225_1` in `templates/index.html` line 997 |

If the UI still did not update before cache-busting: do a hard refresh (Cmd+Shift+R / Ctrl+Shift+R) or open the app in a private window so the new script URL is loaded.
