from flask import Flask, render_template, jsonify, request
from pathlib import Path
import json

app = Flask(__name__, template_folder="app/templates")

# Specimen data for post id=22 (mocked for now)
SECTIONS_DATA = [
    {
        "id": 1,
        "post_id": 22,
        "section_heading": "Introduction",
        "section_description": "Overview of the topic.",
        "ideas_to_include": "Key points, context",
        "status": "draft",
        "section_order": 1
    },
    {
        "id": 2,
        "post_id": 22,
        "section_heading": "Main Argument",
        "section_description": "Detailed argument and evidence.",
        "ideas_to_include": "Supporting facts, examples",
        "status": "draft",
        "section_order": 2
    },
    {
        "id": 3,
        "post_id": 22,
        "section_heading": "Conclusion",
        "section_description": "Summary and closing thoughts.",
        "ideas_to_include": "Restate thesis, implications",
        "status": "draft",
        "section_order": 3
    }
]

def get_sections():
    # In a real app, fetch from DB. Here, just return the specimen data.
    return sorted(SECTIONS_DATA, key=lambda s: s["section_order"])

@app.route("/")
def sections_panel():
    sections = get_sections()
    return render_template("workflow/standalone_sections.html", sections=sections)

@app.route("/api/sections/", methods=["GET", "POST"])
def api_sections():
    global SECTIONS_DATA
    if request.method == "GET":
        return jsonify(get_sections())
    elif request.method == "POST":
        # Save all sections (replace specimen data)
        SECTIONS_DATA = request.json.get("sections", SECTIONS_DATA)
        return jsonify({"success": True, "sections": get_sections()})

if __name__ == "__main__":
    app.run(debug=True, port=5050) 