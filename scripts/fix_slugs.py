#!/usr/bin/env python3
import os
import sys

# Add the application root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import Post


def fix_slugs():
    """Fix empty slugs in the database."""
    app = create_app()

    with app.app_context():
        # Get all posts
        posts = Post.query.all()

        for post in posts:
            if not post.slug:
                # Generate slug from title
                slug = post.title.lower().replace(" ", "-")
                # Remove any non-alphanumeric characters except hyphens
                slug = "".join(c for c in slug if c.isalnum() or c == "-")
                # Replace multiple hyphens with single hyphen
                slug = "-".join(filter(None, slug.split("-")))

                print(f"Setting slug for post '{post.title}' to '{slug}'")
                post.slug = slug

        # Commit all changes
        try:
            db.session.commit()
            print("Successfully updated post slugs")
        except Exception as e:
            print(f"Error updating post slugs: {str(e)}")
            db.session.rollback()


if __name__ == "__main__":
    fix_slugs()
