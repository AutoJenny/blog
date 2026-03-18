#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path

# Add the application root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import Image, Post


def ensure_directory(path):
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)


def fix_image_paths():
    """Fix image paths to ensure they point to processed versions instead of raw files."""
    app = create_app()

    with app.app_context():
        # Get all images
        images = Image.query.all()
        posts = Post.query.all()

        # Create the static images directory if it doesn't exist
        static_images_dir = os.path.join(app.root_path, "static", "images", "posts")
        ensure_directory(static_images_dir)

        # Track which images we've processed
        processed_images = set()

        # First, process images attached to posts
        for post in posts:
            if post.header_image:
                image = post.header_image
                if image.id not in processed_images:
                    # Create post-specific directory
                    post_image_dir = os.path.join(static_images_dir, post.slug)
                    ensure_directory(post_image_dir)

                    # Update path to be relative to static directory
                    new_path = f"images/posts/{post.slug}/{post.slug}_header.jpg"

                    # Copy the image file from the source location
                    source_file = os.path.join(
                        "/Users/nickfiddes/Code/projects/blog/images/posts",
                        post.slug,
                        f"{post.slug}_header.jpg",
                    )
                    target_file = os.path.join(app.root_path, "static", new_path)

                    if os.path.exists(source_file):
                        print(f"Copying {source_file} to {target_file}")
                        shutil.copy2(source_file, target_file)
                        image.path = new_path
                        processed_images.add(image.id)
                    else:
                        print(f"Warning: Source file not found at {source_file}")

            # Process section images
            for section in post.sections:
                if section.image and section.image.id not in processed_images:
                    image = section.image
                    post_image_dir = os.path.join(static_images_dir, post.slug)
                    ensure_directory(post_image_dir)

                    # Get the original filename without _raw if present
                    filename = os.path.basename(image.path)
                    if "_raw." in filename:
                        filename = filename.replace("_raw.", ".")

                    new_path = f"images/posts/{post.slug}/{filename}"

                    # Copy the image file from the source location
                    source_file = os.path.join(
                        "/Users/nickfiddes/Code/projects/blog/images/posts",
                        post.slug,
                        filename,
                    )
                    target_file = os.path.join(app.root_path, "static", new_path)

                    if os.path.exists(source_file):
                        print(f"Copying {source_file} to {target_file}")
                        shutil.copy2(source_file, target_file)
                        image.path = new_path
                        processed_images.add(image.id)
                    else:
                        print(f"Warning: Source file not found at {source_file}")

        # Process any remaining images not attached to posts
        for image in images:
            if image.id not in processed_images and image.path:
                # Try to determine the post slug from the path
                path_parts = Path(image.path).parts
                if len(path_parts) >= 2:
                    post_slug = path_parts[-2]
                    filename = path_parts[-1]

                    if "_raw." in filename:
                        filename = filename.replace("_raw.", ".")

                    post_image_dir = os.path.join(static_images_dir, post_slug)
                    ensure_directory(post_image_dir)

                    new_path = f"images/posts/{post_slug}/{filename}"

                    # Copy the image file from the source location
                    source_file = os.path.join(
                        "/Users/nickfiddes/Code/projects/blog/images/posts",
                        post_slug,
                        filename,
                    )
                    target_file = os.path.join(app.root_path, "static", new_path)

                    if os.path.exists(source_file):
                        print(f"Copying {source_file} to {target_file}")
                        shutil.copy2(source_file, target_file)
                        image.path = new_path
                    else:
                        print(f"Warning: Source file not found at {source_file}")

        # Commit all changes
        try:
            db.session.commit()
            print("Successfully updated image paths")
        except Exception as e:
            print(f"Error updating image paths: {str(e)}")
            db.session.rollback()


if __name__ == "__main__":
    fix_image_paths()
