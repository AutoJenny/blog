# SYSTEM_ARCHITECTURE_v3

Status: Active  
Updated: 2026-03-20  
Scope: BlogForge + AI Hub transition to a multi-domain, schema-agnostic intelligence platform

## 1) Architectural Intent

The platform is now governed as a multi-domain intelligence system, not a single-site blog tool.  
Its primary job is to separate project context, data models, and knowledge vaults so each domain can evolve without cross-domain leakage.

Core invariants:
- Project isolation is mandatory.
- Knowledge retrieval is project-aware and domain-aware.
- Lifecycle orchestration is reusable across domains, while storage schemas remain domain-specific.

## 2) Multi-Domain "Project" Engine

### 2.1 Domain definitions
- `blog`: heritage and publishing workflows (families, calendar ideas, clan KB, post pipeline).
- `scots.law`: legal research and drafting workflows (statutes, cases, citations, briefs).
- `novels`: narrative worldbuilding and manuscript workflows (characters, lore, arcs, chapter plans).

### 2.2 Project registration standard (`config/projects.json`)

The canonical registration contract is a single JSON manifest that defines per-project runtime boundaries.

Required shape:

```json
{
  "projects": [
    {
      "project_id": "blog",
      "display_name": "BlogForge",
      "root_dir": "/Users/autojenny/Documents/projects/blog",
      "database": {
        "engine": "postgresql",
        "dsn_env": "BLOG_DATABASE_URL",
        "schema": "public"
      },
      "knowledge_vaults": [
        "vault.blog.families",
        "vault.blog.kb",
        "vault.blog.calendar"
      ],
      "models": {
        "planner": "openai:gpt-5.2",
        "builder": null,
        "critic": null
      },
      "flags": {
        "auto_task_logging": true,
        "cursor_tool_mode": false
      }
    }
  ]
}
```

Rules:
- `project_id` is the unique identity key across storage, retrieval, threading, and indexing.
- `root_dir` is the repository boundary for code and docs retrieval.
- Each project declares its own database contract and vault set; no implicit cross-project table reuse.
- If a project is unregistered, it is non-routable in UI and orchestration.

## 3) Modular Knowledge Architecture

### 3.1 Dual-Track Sidebar model
- System Knowledge track:
  - Architecture, standards, infra, operations, governance.
  - Sources: `docs/system/`, platform maps, infra maps, standards docs.
- Domain Knowledge track:
  - Project-specific business truth and subject matter.
  - Sources: project vault tables, curated corpora, vault files, indexed project docs.

### 3.2 Vault mapping by project
- Blog vault map:
  - Families (`families`, `family_designs`)
  - Clan KB (`clan_kb_categories`, `clan_kb_articles`)
  - Calendar/ideas (`calendar_ideas`, calendar control layers)
- Scots.law vault map:
  - Statutes
  - Cases and holdings
  - Citation graph and argument snippets
- Novels vault map:
  - Character registry
  - Lore canon
  - Plot arcs and chronology

### 3.3 Retrieval discipline
- Run project-scoped retrieval first.
- Merge system knowledge when the query is architectural, rules-based, or standards-oriented.
- Never write domain facts into system knowledge stores.
- Never infer cross-project truth without explicit project switch.

## 4) The 5-Phase Content Lifecycle

### Phase 1: Research & Synthesis (AI Hub)
- Agnostic discovery, evidence capture, and contradiction checks.
- Output: ranked evidence pack + traceable source map.

#### Phase 1 UI Stabilization: Research Command Center (Deep Green)
The Research Command Center is the project-aware control plane for evidence-backed research visibility:
- Reference Library (stable) renders `postgres_table` vault summaries (record counts + last updated timestamps).
- Intel Laboratory (transient) renders scout health telemetry derived from `ScoutManager`.
- Evidence Layer renders "Zombified" as an actionable diagnostic by comparing the cron target path to the expected runtime filesystem path.

Backend wiring:
- Scout/source telemetry comes from `ai-hub/app/services/scout_manager.py` via `/api/research/sources`.
- Vault handshake + drill-down sampling uses a small helper (`ai-hub/app/services/vault_sampler.py`) invoked by `/api/research/vaults` and the `resource_id` mode of `/api/research/items`.

### Phase 2: Strategic Planning (BlogForge/Calendar)
- Convert evidence into schedule-aware plans.
- Resolve hierarchy: annual cycle -> scheduled events -> idea backlog.
- Output: approved plan objects and calendar placements.

### Phase 3: Generation (The Forge)
- Template-driven drafting using domain templates and governance constraints.
- Output: draft artifacts with explicit source trace references.

### Phase 4: Media & Refinement
- Asset mapping, tone enforcement, section-level polish, metadata completion.
- Output: publish-ready bundle (text + assets + metadata).

### Phase 5: Deployment
- Queueing, publication, and ledger updates.
- Output: immutable deployment event with timestamps and status trail.

## 5) Hierarchical Calendar Specification

Calendar layers:
1. Annual/Cyclical events (recurring strategic anchors)
2. One-off scheduled events (hard-dated priorities)
3. Thematic idea backlog (opportunity pool)

Resolution order:
- Layer 1 establishes baseline cadence.
- Layer 2 can override cadence on exact windows.
- Layer 3 fills remaining capacity with ranking logic.

Override logic (mandatory):
- Manual operator override can replace any scheduled assignment at any layer.
- Override action must leave a trace entry (who/when/what/why) for later audit.

## 6) Post-Renaissance Infrastructure Standards

### 6.1 Database baseline
- PostgreSQL target: `postgresql@17` (local canonical runtime).
- Recovery milestone: Renaissance dataset graft from `backups/RECOVERED_MARCH_RENAISSANCE.sql` (~31 MB).
- Verified core row footprint (2026-03-19 audit):
  - `families=14573`
  - `family_designs=3302`
  - `calendar_ideas=299`
  - `clan_kb_articles=629`
  - `post=42`

### 6.2 Recovery and backup standard
- Standard backup format: `pg_dump -Fc` custom binary dump.
- Rationale: table-level surgical restore support, better resilience than plain SQL-only routines.
- Baseline archive reference: `backups/CANONICAL_RENAISSANCE_RECOVERY_20260319.dump`.

### 6.3 Operational logging note
- `logs/renaissance_graft_import_20260319.log` contains import-time restrictions/errors (`\` command restrictions, syntax interruption) and is treated as incident evidence, not an active runtime configuration source.

## 7) Guardrails (Non-Negotiable)

- No domain may write into another domain's tables.
- No project may bypass registration.
- No retrieval pipeline may skip project identity filtering.
- No production standard may be documented only in code; architecture and standards docs must be kept in sync.
