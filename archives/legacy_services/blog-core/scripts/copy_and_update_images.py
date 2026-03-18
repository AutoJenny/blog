import os
import sys
import shutil
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Image


def ensure_directory_exists(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")


def copy_and_update_images():
    """Copy images to static directory and update database records."""
    app = create_app()
    with app.app_context():
        # Ensure static image directories exist
        static_base = os.path.join("app", "static", "images", "posts")
        ensure_directory_exists(os.path.join(static_base, "kilt-evolution"))
        ensure_directory_exists(os.path.join(static_base, "quaich-traditions"))

        # Process kilt evolution images
        source_dir = os.path.join("__blog_old", "images", "posts", "kilt-evolution")
        for filename in os.listdir(source_dir):
            if not filename.endswith("_raw.jpg") and filename.endswith(".jpg"):
                source_path = os.path.join(source_dir, filename)
                dest_path = os.path.join(static_base, "kilt-evolution", filename)

                # Copy file
                shutil.copy2(source_path, dest_path)
                print(f"Copied: {filename}")

                # Update database
                image = Image.query.filter_by(filename=filename).first()
                if not image:
                    image = Image()
                    db.session.add(image)

                base_name = filename.rsplit(".", 1)[0]
                image.filename = filename
                image.original_filename = filename
                image.path = os.path.join("images", "posts", "kilt-evolution", filename)
                image.alt_text = base_name.replace("_", " ").title()
                image.caption = base_name.replace("_", " ").title()
                image.notes = "Migrated from old blog"
                image.image_metadata = {
                    "import_date": datetime.utcnow().isoformat(),
                    "source": source_path,
                }

        # Process quaich traditions images
        source_dir = os.path.join("__blog_old", "images", "posts", "quaich-traditions")
        for filename in os.listdir(source_dir):
            if not filename.endswith(
                ("_raw.jpg", "_raw.png", ".webp")
            ) and filename.endswith(".jpg"):
                source_path = os.path.join(source_dir, filename)
                dest_path = os.path.join(static_base, "quaich-traditions", filename)

                # Copy file
                shutil.copy2(source_path, dest_path)
                print(f"Copied: {filename}")

                # Update database
                image = Image.query.filter_by(filename=filename).first()
                if not image:
                    image = Image()
                    db.session.add(image)

                base_name = filename.rsplit(".", 1)[0]
                image.filename = filename
                image.original_filename = filename
                image.path = os.path.join(
                    "images", "posts", "quaich-traditions", filename
                )
                image.alt_text = base_name.replace("_", " ").title()
                image.caption = base_name.replace("_", " ").title()
                image.notes = "Migrated from old blog"
                image.image_metadata = {
                    "import_date": datetime.utcnow().isoformat(),
                    "source": source_path,
                }

        # Commit all changes
        try:
            db.session.commit()
            print("Successfully updated all images")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating images: {str(e)}")


if __name__ == "__main__":
    copy_and_update_images()
