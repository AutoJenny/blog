# Code Mapping: Monolithic to Modular Branch Architecture

This document maps all existing files, endpoints, and fields to their new locations and responsibilities in the modular branch architecture. Use this as a reference and checklist during the transition. All changes must be explicit, reviewable, and in line with the orientation document.

---

## Column Legend
| Old File/Path | Old Endpoint/Route | Old Field | New Module/Branch | New File/Path | New Endpoint/Route | New Field | Notes/Dependencies |
|--------------|--------------------|-----------|-------------------|---------------|--------------------|-----------|--------------------|

---

## Base Framework (base-framework branch)
| Old File/Path                | Old Endpoint/Route      | Old Field | New Module/Branch | New File/Path                      | New Endpoint/Route         | New Field | Notes/Dependencies                |
|------------------------------|------------------------|-----------|-------------------|------------------------------------|----------------------------|-----------|-----------------------------------|
| app/templates/base.html      | /                      |           | base-framework    | templates/base.html                | /                          |           | Site shell, header, footer        |
| app/routes.py                | /posts, /settings      |           | base-framework    | routes.py                          | /posts, /settings          |           |                                   |
| app/templates/main/docs_browser.html | /docs/browser |           | base-framework    | templates/main/docs_browser.html   | /docs/browser              |           | Docs browser                      |
| app/static/css/style.css     |                        |           | base-framework    | static/css/style.css               |                            |           | Site-wide CSS                     |
| app/static/css/admin.css     |                        |           | base-framework    | static/css/admin.css               |                            |           | Admin CSS                         |
| app/static/images/site/*     |                        |           | base-framework    | static/images/site/*               |                            |           | Site images                       |

---

## Workflow Navigation (workflow-navigation branch)
| Old File/Path                | Old Endpoint/Route      | Old Field | New Module/Branch | New File/Path                      | New Endpoint/Route         | New Field | Notes/Dependencies                |
|------------------------------|------------------------|-----------|-------------------|------------------------------------|----------------------------|-----------|-----------------------------------|
| app/templates/workflow/_workflow_nav.html | (included) |           | workflow-navigation | templates/_workflow_nav.html      | (included)                 |           | Navigation bar, breadcrumbs       |
| app/static/js/workflow.js    |                        |           | workflow-navigation | static/js/workflow_nav.js         |                            |           | Navigation JS                     |
| app/static/css/src/nav.css   |                        |           | workflow-navigation | static/css/nav.css                |                            |           | Navigation styles                  |

---

## LLM-Actions (workflow-llm-actions branch)
| Old File/Path                | Old Endpoint/Route      | Old Field | New Module/Branch | New File/Path                      | New Endpoint/Route         | New Field | Notes/Dependencies                |
|------------------------------|------------------------|-----------|-------------------|------------------------------------|----------------------------|-----------|-----------------------------------|
| app/templates/llm/actions.html| /llm/                  |           | workflow-llm-actions | templates/llm/actions.html        | /llm/                      |           | LLM action interface              |
| app/static/js/llm.js         |                        |           | workflow-llm-actions | static/js/llm.js                  |                            |           | LLM interaction logic             |
| app/llm/actions/idea.py      | /llm/idea              |           | workflow-llm-actions | llm/actions/idea.py               | /llm/idea                  |           | LLM action backend                |
| app/workflow/scripts/llm_processor.py | (internal)    |           | workflow-llm-actions | scripts/llm_processor.py          | (internal)                 |           | LLM processing logic              |
| app/data/prompts/planning_idea_basic_idea.json | (config) | | workflow-llm-actions | data/prompts/planning_idea_basic_idea.json | (config) | | LLM prompt config |

---

## Sections (workflow-sections branch)
| Old File/Path                | Old Endpoint/Route      | Old Field | New Module/Branch | New File/Path                      | New Endpoint/Route         | New Field | Notes/Dependencies                |
|------------------------------|------------------------|-----------|-------------------|------------------------------------|----------------------------|-----------|-----------------------------------|
| app/templates/workflow/steps/sections.html | /workflow/sections | | workflow-sections | templates/sections.html            | /workflow/sections         |           | Section management UI             |
| app/static/js/sections.js    |                        |           | workflow-sections | static/js/sections.js              |                            |           | Section drag & drop logic         |
| app/workflow/config/prompts/writing/content/sections.json | (config) | | workflow-sections | config/sections.json               | (config)                   |           | Section prompt config             |

---

## Shared Data/API Layer (all branches, via base-framework)
| Old File/Path                | Old Endpoint/Route      | Old Field | New Module/Branch | New File/Path                      | New Endpoint/Route         | New Field | Notes/Dependencies                |
|------------------------------|------------------------|-----------|-------------------|------------------------------------|----------------------------|-----------|-----------------------------------|
| app/db.py                    | (DB connection)        |           | base-framework    | db.py                              | (DB connection)            |           | Shared DB connection              |
| app/database/routes.py       | /api/db/*              |           | base-framework    | database/routes.py                 | /api/db/*                  |           | DB API endpoints                  |
| app/models.py                | (models)               |           | base-framework    | models.py                          | (models)                   |           | Shared models                     |

---

## Database Fields (reference)
| Old Table/Field              | New Table/Field         | Notes/Dependencies                |
|------------------------------|-------------------------|-----------------------------------|
| post.id                      | post.id                 | Unchanged                         |
| post.title                   | post.title              | Unchanged                         |
| post_section.id              | post_section.id         | Unchanged                         |
| post_section.title           | post_section.title      | Unchanged                         |
| workflow_step_entity.*       | workflow_step_entity.*  | Canonical for workflow steps      |

---

## Notes
- All modules must interact only via the data/API layer or explicit shared config.
- No direct imports or code dependencies between module branches.
- Only site-wide CSS and minimal config may be shared, and only via the base-framework branch.
- This mapping must be updated with every migration or refactor. 