import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Post, Image, PostSection


def create_image(filename, post_slug):
    """Create an Image record if it doesn't exist."""
    image = Image.query.filter_by(filename=filename).first()
    if not image:
        # Create new image with all required fields
        image = Image()
        image.filename = filename
        image.original_filename = filename
        image.path = f"images/posts/{post_slug}/{filename}"
        image.alt_text = filename.replace(".jpg", "").replace("_", " ").title()
        image.caption = filename.replace(".jpg", "").replace("_", " ").title()
        image.image_prompt = ""  # Optional AI generation prompt
        image.notes = "Created by check_images.py script"
        image.image_metadata = {
            "created_at": datetime.utcnow().isoformat(),
            "post_slug": post_slug,
            "source": "check_images.py",
        }
        image.watermarked = False
        image.watermarked_path = ""

        db.session.add(image)
        db.session.flush()  # Get the ID without committing
    return image


def main():
    """Process images for the specified blog posts."""
    app = create_app()
    with app.app_context():
        # Process quaich-traditions post
        post = Post.query.filter_by(slug="quaich-traditions").first()
        if post:
            # Set header image
            header_image = create_image(
                "quaich-traditions_header.jpg", "quaich-traditions"
            )
            post.header_image = header_image

            # Process section images
            for section in post.sections:
                if section.title:
                    section_slug = section.title.lower().replace(" ", "-")
                    image_filename = f"quaich-traditions_{section_slug}.jpg"
                    if os.path.exists(
                        os.path.join(
                            "app",
                            "static",
                            "images",
                            "posts",
                            "quaich-traditions",
                            image_filename,
                        )
                    ):
                        section.image = create_image(
                            image_filename, "quaich-traditions"
                        )

        # Process kilt-evolution post
        post = Post.query.filter_by(slug="kilt-evolution").first()
        if post:
            # Set header image
            header_image = create_image("kilt-evolution_header.jpg", "kilt-evolution")
            post.header_image = header_image

            # Process section images
            for section in post.sections:
                if section.title:
                    section_slug = section.title.lower().replace(" ", "-")
                    image_filename = f"kilt-evolution_{section_slug}.jpg"
                    if os.path.exists(
                        os.path.join(
                            "app",
                            "static",
                            "images",
                            "posts",
                            "kilt-evolution",
                            image_filename,
                        )
                    ):
                        section.image = create_image(image_filename, "kilt-evolution")

        # Commit all changes
        try:
            db.session.commit()
            print("Successfully processed all images")
        except Exception as e:
            db.session.rollback()
            print(f"Error processing images: {str(e)}")


if __name__ == "__main__":
    main()
