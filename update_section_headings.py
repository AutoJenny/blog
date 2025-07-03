#!/usr/bin/env python3
import psycopg2
import json

# Section headings data
section_headings = [
    {
        "title": "Uncovering Scotland's Rich Storytelling Heritage",
        "description": "Exploring the ancient Celtic roots of Scottish storytelling and its evolution over time"
    },
    {
        "title": "The Makars and Medieval Courts: Shaping Scotland's Literary Identity",
        "description": "Discovering how medieval poets and writers influenced Scotland's cultural heritage"
    },
    {
        "title": "Folklore, Mythology, and the Power of Place in Scottish Storytelling",
        "description": "Examining the impact of folklore, mythology, and landscape on Scottish storytelling traditions"
    },
    {
        "title": "From Oral Tradition to Written Works: The Evolution of Scottish Storytelling",
        "description": "Tracing the shift from oral storytelling to written works and its effects on Scottish literature"
    },
    {
        "title": "Subversion and Social Commentary in Modern Scottish Storytelling",
        "description": "Investigating how contemporary Scottish storytellers use their craft for social commentary and critique"
    },
    {
        "title": "New Voices, New Forms: The Future of Scottish Storytelling",
        "description": "Exploring the innovative ways in which modern Scottish storytellers are pushing the boundaries of traditional forms"
    }
]

# Convert to JSON string
json_data = json.dumps(section_headings)

# Connect to database and update
conn = psycopg2.connect("dbname=blog")
cur = conn.cursor()

cur.execute("UPDATE post_development SET section_headings = %s WHERE post_id = 22", (json_data,))
conn.commit()

print(f"Updated section_headings for post 22 with {len(section_headings)} sections")
print("JSON data:", json_data)

cur.close()
conn.close() 