#!/usr/bin/env python3
"""
Refactor tool: splits monolithic planning.py into small modules by responsibility.
- Reads exact function/class blocks via AST + line ranges (no content guessing)
- Writes new package under ./app/
- You can re-run safely; it overwrites generated files.

Usage:
  python3 refactor_planning.py
"""

import ast, os, re, shutil, sys, textwrap

SRC = "blueprints/planning.py"
OUTDIR = "app"

# ---------- helpers ----------
def read(src):
    with open(src, "r", encoding="utf-8") as f:
        return f.read()

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def write_file(path, content):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def extract_blocks(code, names):
    """Return list of (name, src_text) for defs/classes with exact names."""
    tree = ast.parse(code)
    lines = code.splitlines(True)
    found = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in names:
                start = node.lineno - 1
                end = getattr(node, "end_lineno", None)
                if end is None:
                    # fallback: walk node to find max lineno
                    end = max(getattr(n, "lineno", node.lineno) for n in ast.walk(node))
                block = "".join(lines[start:end])
                found[node.name] = block
    return [(n, found[n]) for n in names if n in found]

def list_defs(code):
    tree = ast.parse(code)
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            out.append((node.name, start, end, type(node).__name__))
    return out

# ---------- load + analyze ----------
if not os.path.exists(SRC):
    print(f"ERROR: {SRC} not found.", file=sys.stderr)
    sys.exit(1)

code = read(SRC)
defs = list_defs(code)

# Buckets by prefix/responsibility
def names_starting(pref):
    return [n for (n,_,_,_) in defs if n.startswith(pref)]

API_CAL = names_starting("api_calendar_")
API_UPD = names_starting("api_update_")
API_SAV = names_starting("api_save_")

api_all = names_starting("api_")
api_covered = set(API_CAL + API_UPD + API_SAV)
API_MISC = [n for n in api_all if n not in api_covered]

PLANNING = names_starting("planning_")
ALLOCATE = names_starting("allocate_") + ["allocate_global"]
VALIDATE = names_starting("validate_") + ["canonicalize_sections", "auto_correct_sections"]
PARSING  = names_starting("parse_")
PROMPTS  = names_starting("build_") + names_starting("generate_")
SAVE_FUNCS = names_starting("save_")
GET_POSTS  = ["get_post_data"] + SAVE_FUNCS
GET_CONF   = ["get_step_config", "get_system_prompts", "get_providers", "get_actions", "get_section_keywords"]

SERV_LLM = ["LLMService", "run_llm"]

def uniq(seq):
    seen = set(); out=[]
    for x in seq:
        if x not in seen:
            out.append(x); seen.add(x)
    return out

plan = [
    ("routes/calendar.py", API_CAL, "# Flask endpoints: calendar"),
    ("routes/update.py",   API_UPD, "# Flask endpoints: update"),
    ("routes/save.py",     API_SAV, "# Flask endpoints: save"),
    ("routes/misc.py",     API_MISC,"# Flask endpoints: miscellaneous"),
    ("planning/views.py",  PLANNING,"# Planning UI/data helpers"),
    ("services/allocation.py", ALLOCATE, "# Allocation/assignment"),
    ("services/validation.py", VALIDATE, "# Validation & canonicalization"),
    ("services/parsing.py",    PARSING,  "# Parsing/normalization"),
    ("services/prompting.py",  PROMPTS,  "# Prompt builders & titling"),
    ("services/llm.py",        SERV_LLM, "# LLM client + runner"),
    ("repositories/posts.py",  GET_POSTS,"# Post + save operations"),
    ("repositories/config.py", GET_CONF, "# Config, providers, actions"),
]

if os.path.exists(OUTDIR):
    shutil.rmtree(OUTDIR)
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(os.path.join(OUTDIR, "routes"), exist_ok=True)
os.makedirs(os.path.join(OUTDIR, "planning"), exist_ok=True)
os.makedirs(os.path.join(OUTDIR, "services"), exist_ok=True)
os.makedirs(os.path.join(OUTDIR, "repositories"), exist_ok=True)

def header(comment):
    return textwrap.dedent(f"""\
    # Auto-generated from {SRC}
    # {comment}
    # NOTE: Code blocks are copied verbatim; import dependencies remain the same.
    from __future__ import annotations

    """)

for relpath, names, comment in plan:
    names = uniq(names)
    blocks = extract_blocks(code, names)
    content = header(comment)
    if not blocks:
        content += "# (no blocks matched by current file)\n"
    else:
        for name, src_block in blocks:
            content += f"{src_block}\n\n"
    write_file(os.path.join(OUTDIR, relpath), content)

# Init stubs
for sub in ["routes","planning","services","repositories"]:
    write_file(os.path.join(OUTDIR, sub, "__init__.py"), "")

print("Refactor complete.")
for relpath, names, _ in plan:
    print(f"- app/{relpath}: {len(names)} items")
