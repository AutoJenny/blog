# Code Mapping: Old to New Modular Framework

This document maps all existing files, endpoints, and their new locations in the modular framework. Use this as a reference and checklist during migration.

---

## Column Legend
| Old File/Path | Old Endpoint/Route | New Module | New File/Path | New Endpoint/Route | Notes/Dependencies |
|--------------|--------------------|------------|---------------|--------------------|--------------------|

---

## Main / HUB (Site Shell, Docs, Settings, etc.)
| Old File/Path                | Old Endpoint/Route      | New Module | New File/Path                      | New Endpoint/Route         | Notes/Dependencies                |
|------------------------------|------------------------|------------|------------------------------------|----------------------------|-----------------------------------|
| app/templates/base.html      | /                      | main/hub   | hub/templates/base.html            | /                          | Uses nav, docs, settings includes |
| app/routes.py                | /posts, /settings      | main/hub   | hub/routes.py                      | /posts, /settings          |                                   |
| app/templates/main/modern_index.html | /          | main/hub   | hub/templates/index.html           | /                          | Main landing page                 |
| app/templates/main/settings.html | /settings      | main/hub   | hub/templates/settings.html        | /settings                  | Settings page                     |
| app/templates/docs/live_field_mapping.html | /docs/fields | main/hub | hub/templates/docs/fields.html     | /docs/fields              | Field mapping documentation       |
| app/templates/errors/404.html | (error handler)    | main/hub   | hub/templates/errors/404.html      | (error handler)            | 404 error page                    |
| app/templates/errors/500.html | (error handler)    | main/hub   | hub/templates/errors/500.html      | (error handler)            | 500 error page                    |
| app/errors/__init__.py       | (error handlers)   | main/hub   | hub/errors/__init__.py             | (error handlers)           | Error handling setup              |

---

## workflow_nav (Navigation UI, Stage/Substage Logic)
| Old File/Path                | Old Endpoint/Route      | New Module         | New File/Path                      | New Endpoint/Route         | Notes/Dependencies                |
|------------------------------|------------------------|--------------------|------------------------------------|----------------------------|-----------------------------------|
| app/templates/nav.html       | (included in base)     | workflow_nav       | modules/nav/templates/nav.html     | (included in hub)          | Needs stage/substage data         |
| app/static/js/nav.js         |                        | workflow_nav       | modules/nav/static/js/nav.js       |                            | Navigation logic                  |
| app/static/css/src/nav.css   |                        | workflow_nav       | modules/nav/static/css/nav.css     |                            | Navigation styles                 |

---

## workflow_llm_actions (LLM Input/Prompt/Output)
| Old File/Path                | Old Endpoint/Route      | New Module             | New File/Path                          | New Endpoint/Route         | Notes/Dependencies                |
|------------------------------|------------------------|------------------------|----------------------------------------|----------------------------|-----------------------------------|
| app/templates/llm/actions.html| /llm/                  | workflow_llm_actions   | modules/llm_action/templates/actions.html | /llm/                  | LLM action interface              |
| app/templates/llm/config.html | /llm/config           | workflow_llm_actions   | modules/llm_action/templates/config.html | /llm/config           | LLM configuration interface       |
| app/static/js/llm.js         |                        | workflow_llm_actions   | modules/llm_action/static/js/llm.js    |                            | LLM interaction logic             |
| app/static/css/src/llm.css   |                        | workflow_llm_actions   | modules/llm_action/static/css/llm.css  |                            | LLM interface styles              |
| app/llm/actions/idea.py      | /llm/idea             | workflow_llm_actions   | modules/llm_action/actions/idea.py     | /llm/idea                 | Idea generation action            |
| app/workflow/scripts/llm_processor.py | (internal)    | workflow_llm_actions   | modules/llm_action/scripts/processor.py | (internal)            | LLM processing logic              |

---

## workflow_sections (Section List, Drag & Drop)
| Old File/Path                | Old Endpoint/Route      | New Module         | New File/Path                          | New Endpoint/Route         | Notes/Dependencies                |
|------------------------------|------------------------|--------------------|----------------------------------------|----------------------------|-----------------------------------|
| app/templates/workflow/writing/content/sections.html | /writing/sections | workflow_sections | modules/sections/templates/sections.html | /writing/sections     | Section management interface      |
| app/static/js/sections.js    |                        | workflow_sections  | modules/sections/static/js/sections.js |                            | Section drag & drop logic         |
| app/workflow/config/prompts/writing/content/sections.json | (config) | workflow_sections | modules/sections/config/sections.json | (config)                    | Section prompt configuration      |

---

## workflow_outline (Outline Management)
| Old File/Path                | Old Endpoint/Route      | New Module         | New File/Path                          | New Endpoint/Route         | Notes/Dependencies                |
|------------------------------|------------------------|--------------------|----------------------------------------|----------------------------|-----------------------------------|
| app/templates/workflow/steps/outline.html | /workflow/outline | workflow_outline | modules/outline/templates/outline.html | /workflow/outline          | Outline management interface      |
| app/workflow/handlers/outline_handler.py | (internal) | workflow_outline | modules/outline/handlers/outline.py | (internal)                  | Outline processing logic          |

---

## workflow_planning (Planning Stages)
| Old File/Path                | Old Endpoint/Route      | New Module         | New File/Path                          | New Endpoint/Route         | Notes/Dependencies                |
|------------------------------|------------------------|--------------------|----------------------------------------|----------------------------|-----------------------------------|
| app/templates/workflow/steps/planning.html | /workflow/planning | workflow_planning | modules/planning/templates/planning.html | /workflow/planning    | Planning interface                |
| app/data/prompts/planning_idea_basic_idea.json | (config) | workflow_planning | modules/planning/config/idea.json | (config)                    | Planning prompt configuration     |

---

## workflow_writing (Writing Stages)
| Old File/Path                | Old Endpoint/Route      | New Module         | New File/Path                          | New Endpoint/Route         | Notes/Dependencies                |
|------------------------------|------------------------|--------------------|----------------------------------------|----------------------------|-----------------------------------|
| app/templates/workflow/writing/index.html | /workflow/writing | workflow_writing | modules/writing/templates/index.html | /workflow/writing          | Writing stage interface           |
| app/workflow/config/writing_steps.json | (config) | workflow_writing | modules/writing/config/steps.json | (config)                    | Writing stage configuration       |

---

## workflow_preview (Preview Functionality)
| Old File/Path                | Old Endpoint/Route      | New Module         | New File/Path                          | New Endpoint/Route         | Notes/Dependencies                |
|------------------------------|------------------------|--------------------|----------------------------------------|----------------------------|-----------------------------------|
| app/preview/__init__.py      | /preview              | workflow_preview   | modules/preview/__init__.py            | /preview                   | Preview functionality setup       |
| app/preview/routes.py        | /preview/*           | workflow_preview   | modules/preview/routes.py              | /preview/*                 | Preview routes                    |

---

## workflow_blog (Blog Display)
| Old File/Path                | Old Endpoint/Route      | New Module         | New File/Path                          | New Endpoint/Route         | Notes/Dependencies                |
|------------------------------|------------------------|--------------------|----------------------------------------|----------------------------|-----------------------------------|
| app/blog/routes.py           | /blog/*              | workflow_blog      | modules/blog/routes.py                 | /blog/*                    | Blog display routes               |
| app/templates/blog/_post_header.html | (template) | workflow_blog | modules/blog/templates/post_header.html | (template)             | Blog post header template         |

---

## Static Assets
| Old File/Path                | Type                   | New Module         | New File/Path                          | Notes/Dependencies         |
|------------------------------|------------------------|--------------------|----------------------------------------|----------------------------|
| app/static/css/dist/main.css | Compiled CSS          | main/hub           | hub/static/css/main.css                | Main stylesheet            |
| app/static/css/src/main.css  | Source CSS            | main/hub           | hub/static/css/src/main.css            | Main stylesheet source     |
| app/static/css/admin.css     | CSS                   | main/hub           | hub/static/css/admin.css               | Admin interface styles     |
| app/static/images/site/header.jpg | Image          | main/hub           | hub/static/images/header.jpg           | Site header image          |
| app/static/images/site/quaich-logo.png | Image      | main/hub           | hub/static/images/logo.png             | Site logo                  |

---

## Database
| Old File/Path                | Type                   | New Module         | New File/Path                          | Notes/Dependencies         |
|------------------------------|------------------------|--------------------|----------------------------------------|----------------------------|
| app/database/__init__.py     | Database setup        | main/hub           | hub/database/__init__.py               | Database connection setup  |
| app/templates/db/index.html  | /db                   | main/hub           | hub/templates/db/index.html            | Database interface         |
| app/templates/db/raw.html    | /db/raw              | main/hub           | hub/templates/db/raw.html              | Raw database view          |

---

## Services
| Old File/Path                | Type                   | New Module         | New File/Path                          | Notes/Dependencies         |
|------------------------------|------------------------|--------------------|----------------------------------------|----------------------------|
| app/services/structure.py    | Structure service     | workflow_structure | modules/structure/services/structure.py | Structure processing      |
| app/services/llm_service.py  | LLM service          | workflow_llm_actions | modules/llm_action/services/llm.py   | LLM API interaction        | 