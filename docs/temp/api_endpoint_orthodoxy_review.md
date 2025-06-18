# API Endpoint Orthodoxy Review and Action Plan

## Summary of Findings

### Canonical Endpoint Schema (from docs)
- **Plan Structure:**  
  `POST /api/v1/structure/plan`  
  Request: `{ "title": ..., "idea": ..., "facts": [...] }`  
  Response: `{ "sections": [ ... ] }`

- **Save Structure:**  
  `POST /api/v1/structure/save/<post_id>`  
  Request: `{ "sections": [ ... ] }`  
  Response: `{ "message": ..., "sections": [ ... ] }`

- **Get Structure:**  
  `GET /api/v1/post/<post_id>/structure`  
  Response: `{ "post": ..., "sections": [ ... ], ... }`

### Current Codebase Endpoint Review

#### Location of Endpoints
- Structure endpoints (`/api/v1/structure/plan`, `/api/v1/structure/plan_and_save`) are defined in `app/blog/routes.py`, which is registered under the `/blog` blueprint (`url_prefix='/blog'`).
- This means the actual URL is `/blog/api/v1/structure/plan`, **not** `/api/v1/structure/plan`.

#### Other Structure-Related Endpoints
- `/api/v1/post/<int:post_id>/structure` (GET) is also in `app/blog/routes.py`.
- There are also endpoints like `/api/v1/post/<int:post_id>/sections` and `/api/v1/posts/<int:post_id>/sections/<int:section_id>/fields/<field>`.

#### Non-Orthodox Patterns
- **Blueprint Mismatch:**  
  Endpoints intended for `/api/v1/...` are defined in the `blog` blueprint, not the `api` blueprint. This is non-orthodox and can cause confusion and routing issues.
- **Inconsistent Naming:**  
  - Both `/api/v1/post/...` and `/api/v1/posts/...` are used (singular vs plural).
  - `/api/v1/post_development/fields` is a one-off pattern, not matching the rest.
- **Save Endpoint Not Implemented as Documented:**  
  - The canonical `/api/v1/structure/save/<post_id>` endpoint is **not present** in the codebase.
  - Instead, you have `/api/v1/structure/plan_and_save` (not documented in `/docs/api/structure_stage.md`).

## Action Plan

### Immediate Fix (Current Issue)
- **Move** the `/api/v1/structure/plan_and_save` endpoint from `app/blog/routes.py` to `app/api/routes.py` to ensure it is available at `/api/v1/structure/plan_and_save`.

### Long-Term Fixes
1. **Move** all structure-related endpoints to `app/api/routes.py`.
2. **Rename** and refactor endpoints to match the canonical schema:
   - `/api/v1/structure/plan`
   - `/api/v1/structure/save/<post_id>`
   - `/api/v1/post/<post_id>/structure`
3. **Remove or deprecate** `/api/v1/structure/plan_and_save` unless you want to document and standardize it.
4. **Update documentation** if you decide to keep any non-canonical endpoints, or (preferably) update code to match docs.
5. **Standardize** on plural resource names for REST endpoints.

## Next Steps
- Proceed with the immediate fix to move the `/api/v1/structure/plan_and_save` endpoint to the `api` blueprint.
- After the immediate fix, review and implement the long-term fixes to ensure API orthodoxy and maintainability. 