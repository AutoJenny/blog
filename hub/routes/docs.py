from flask import render_template, abort
from datetime import datetime
import os
import markdown
from . import bp
import re

@bp.route('/docs/', defaults={'req_path': ''})
@bp.route('/docs/<path:req_path>')
def docs(req_path):
    docs_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs')
    abs_path = os.path.join(docs_root, req_path)

    # If path is a file and ends with .md, render it
    if os.path.isfile(abs_path) and abs_path.endswith('.md'):
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        html = markdown.markdown(content, extensions=['fenced_code', 'tables'])
        # For navigation, show the tree from root
        tree = build_docs_tree(docs_root)
        rel_file = os.path.relpath(abs_path, docs_root)
        return render_template('main/docs_browser.html', tree=tree, file_html=html, file_path=rel_file)

    # If path is a directory, list its contents
    if os.path.isdir(abs_path):
        tree = build_docs_tree(docs_root)
        return render_template('main/docs_browser.html', tree=tree, file_html=None, file_path=None)

    # Not found
    return "Not found", 404

def build_docs_tree(root):
    """Recursively build a tree of .md files and directories for navigation."""
    tree = []
    for entry in sorted(os.listdir(root)):
        path = os.path.join(root, entry)
        if os.path.isdir(path):
            subtree = build_docs_tree(path)
            if subtree:
                tree.append({'type': 'dir', 'name': entry, 'children': subtree})
        elif entry.endswith('.md'):
            tree.append({'type': 'file', 'name': entry, 'path': os.path.relpath(path, root)})
    return tree

@bp.route('/docs/nav/')
def docs_nav():
    docs_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs')
    tree = build_docs_tree(docs_root)
    file_path = None
    return render_template('main/docs_nav.html', tree=tree, file_path=file_path)

@bp.route('/docs/view/<path:file_path>')
def docs_content(file_path):
    docs_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs')
    abs_path = os.path.join(docs_root, file_path)
    if not os.path.isfile(abs_path) or not abs_path.endswith('.md'):
        return "Not found", 404
    with open(abs_path, 'r', encoding='utf-8') as f:
        content = f.read()
    html = markdown.markdown(content, extensions=['fenced_code', 'tables'])
    # Post-process Mermaid code blocks
    def mermaid_replacer(match):
        code = match.group(1)
        return f'<div class="mermaid">{code}</div>'
    html = re.sub(r'<pre><code class="language-mermaid">([\s\S]*?)</code></pre>', mermaid_replacer, html)
    return render_template('main/docs_content.html', file_html=html, file_path=file_path) 