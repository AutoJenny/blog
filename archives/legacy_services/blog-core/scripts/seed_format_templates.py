#!/usr/bin/env python3
"""
Seed script to populate the database with proper format template examples.
This creates usable formats for testing the format system.
"""

import os
import sys
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def seed_format_templates():
    """Seed the database with proper format template examples."""
    app = create_app()
    
    with app.app_context():
        from app.db import get_db_conn
        
        # Connect to database
        conn = get_db_conn()
        cursor = conn.cursor()
        
        print("Seeding format templates...")
        
        # First, clear existing templates (except the integration test one)
        cursor.execute("DELETE FROM workflow_format_template WHERE id != 11")
        print("Cleared existing templates (kept integration test format)")
        
        # 1. Plain Text Format (UK English)
        plain_text_format = {
            "name": "Plain Text Response (UK English)",
            "description": "Format for plain text responses using British English spellings and conventions",
            "fields": [
                {
                    "name": "title",
                    "type": "string",
                    "required": True,
                    "description": "The main title or heading"
                },
                {
                    "name": "content",
                    "type": "string", 
                    "required": True,
                    "description": "The main content text using British English spellings (e.g., colour, centre, organisation)"
                },
                {
                    "name": "summary",
                    "type": "string",
                    "required": False,
                    "description": "A brief summary of the content"
                },
                {
                    "name": "key_points",
                    "type": "array",
                    "required": False,
                    "description": "List of key points or takeaways"
                },
                {
                    "name": "author_notes",
                    "type": "string",
                    "required": False,
                    "description": "Additional notes or comments from the author"
                }
            ]
        }
        
        # 2. JSON Structure Format
        json_format = {
            "name": "Structured JSON Response",
            "description": "Format for structured data responses in JSON format with defined schema",
            "fields": [
                {
                    "name": "status",
                    "type": "string",
                    "required": True,
                    "description": "Response status (success, error, pending)"
                },
                {
                    "name": "data",
                    "type": "object",
                    "required": True,
                    "description": "Main data object containing the response content"
                },
                {
                    "name": "metadata",
                    "type": "object",
                    "required": False,
                    "description": "Additional metadata about the response"
                },
                {
                    "name": "timestamp",
                    "type": "string",
                    "required": True,
                    "description": "ISO 8601 timestamp of when the response was generated"
                },
                {
                    "name": "version",
                    "type": "string",
                    "required": False,
                    "description": "Version identifier for the response format"
                },
                {
                    "name": "errors",
                    "type": "array",
                    "required": False,
                    "description": "Array of error messages if any occurred"
                }
            ]
        }
        
        # 3. Blog Post Format
        blog_post_format = {
            "name": "Blog Post Structure",
            "description": "Format for structured blog post content with sections and metadata",
            "fields": [
                {
                    "name": "title",
                    "type": "string",
                    "required": True,
                    "description": "The blog post title"
                },
                {
                    "name": "subtitle",
                    "type": "string",
                    "required": False,
                    "description": "Optional subtitle or tagline"
                },
                {
                    "name": "introduction",
                    "type": "string",
                    "required": True,
                    "description": "Opening paragraph that introduces the topic"
                },
                {
                    "name": "sections",
                    "type": "array",
                    "required": True,
                    "description": "Array of content sections, each with title and content"
                },
                {
                    "name": "conclusion",
                    "type": "string",
                    "required": True,
                    "description": "Closing paragraph that summarises the main points"
                },
                {
                    "name": "tags",
                    "type": "array",
                    "required": False,
                    "description": "Array of relevant tags for categorisation"
                },
                {
                    "name": "estimated_read_time",
                    "type": "string",
                    "required": False,
                    "description": "Estimated reading time (e.g., '5 minutes')"
                }
            ]
        }
        
        # Insert the new formats
        formats_to_insert = [plain_text_format, json_format, blog_post_format]
        
        for format_data in formats_to_insert:
            cursor.execute("""
                INSERT INTO workflow_format_template (name, description, fields)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (
                format_data["name"],
                format_data["description"],
                json.dumps(format_data["fields"])
            ))
            
            format_id = cursor.fetchone()["id"]
            print(f"✓ Created format: {format_data['name']} (ID: {format_id})")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✅ Format templates seeded successfully!")
        print("Created formats:")
        print("  - Plain Text Response (UK English)")
        print("  - Structured JSON Response") 
        print("  - Blog Post Structure")
        print("  - Integration Test Format (preserved)")

if __name__ == '__main__':
    seed_format_templates() 