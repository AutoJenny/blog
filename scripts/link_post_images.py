import os
import sys
from datetime import datetime
from flask import Flask

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Post, Image, PostSection

app = create_app()


def link_images():
    with app.app_context():
        posts = Post.query.all()
        for post in posts:
            # Link header image
            header_image = Image.query.filter_by(
                filename=f"{post.slug}_header.jpg"
            ).first()
            if header_image:
                post.header_image_id = header_image.id
                print(f"Linked header image for post: {post.title}")

            # Link section images
            sections = (
                PostSection.query.filter_by(post_id=post.id)
                .order_by(PostSection.position)
                .all()
            )
            for section in sections:
                # Convert section title to filename format
                section_slug = section.title.lower().replace(" ", "-")
                image = Image.query.filter_by(
                    filename=f"{post.slug}_{section_slug}.jpg"
                ).first()
                if image:
                    section.image_id = image.id
                    print(f"Linked image for section: {section.title}")

        try:
            db.session.commit()
            print("Successfully linked all images")
        except Exception as e:
            db.session.rollback()
            print(f"Error linking images: {str(e)}")


if __name__ == "__main__":
    link_images()
