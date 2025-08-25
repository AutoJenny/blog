# Flask App Working Setup (Reference)

## Directory Structure (Key Parts)

```
/Users/nickfiddes/Code/projects/blog
├── app/
│   ├── __init__.py
│   ├── main/
│   ├── llm/
│   ├── blog/
│   ├── ...
│   └── templates/
│       ├── base.html
│       ├── llm/
│       │   ├── actions.html
│       │   ├── ...
│       ├── main/
│       ├── ...
├── requirements.txt
├── run_server.sh
├── .env or assistant_config.env
├── ...
```

## Flask App Factory (app/__init__.py)
- Uses `Flask(__name__)` (no explicit template_folder needed if using `app/templates`)
- Registers all blueprints before any routes are used
- Loads config from `config.py` and `.env`/`assistant_config.env`
- Initializes all extensions (SQLAlchemy, Celery, etc.)

## Template Discovery
- Templates are stored in `app/templates/` and subfolders (e.g., `llm/`, `main/`)
- No symlinks, hidden files, or `__init__.py` in template folders
- All templates are valid text files

## Environment Variables (.env or assistant_config.env)
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/blog
FLASK_ENV=development
FLASK_DEBUG=1
```

## requirements.txt (Key Packages)
- Flask==3.1.0
- Flask-Caching, Flask-Mail, Flask-Migrate, Flask-WTF
- Celery, SQLAlchemy, psycopg2
- Jinja2==3.1.6
- python-dotenv
- ... (see full requirements.txt)

## Server Startup (run_server.sh)
- Kills any process on port 5000 and any Flask processes
- Activates the virtual environment
- Sets `FLASK_APP=app.py`, `FLASK_DEBUG=1`, `FLASK_RUN_PORT=5000`
- Runs `python run.py` (or `flask run` if using app factory)

## Troubleshooting Lessons
- **Templates must be in `app/templates/`** (or `templates/` if using default)
- **No symlinks, hidden files, or `__init__.py` in template folders**
- **Blueprints must be registered before any routes are used**
- **Always check working directory and template_folder config**
- **If templates are not found, check with a minimal Flask app**
- **Rolling back to a known-good Git commit can resolve deep config issues**

---

_Last updated: 2024-05-22_ 