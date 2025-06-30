import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db


def create_image(filename, post_slug):
    """Create an Image record if it doesn't exist."""
    image = db.session.execute(
        "SELECT * FROM images WHERE filename = :filename",
        {"filename": filename}
    ).fetchone()
    if not image:
        # Create new image with all required fields
        image = db.session.execute(
            "INSERT INTO images (filename, original_filename, path, alt_text, caption, image_prompt, notes, image_metadata, watermarked, watermarked_path) "
            "VALUES (:filename, :filename, :path, :alt_text, :caption, :image_prompt, :notes, :image_metadata, :watermarked, :watermarked_path) RETURNING *",
            {
                "filename": filename,
                "path": f"images/posts/{post_slug}/{filename}",
                "alt_text": filename.replace(".jpg", "").replace("_", " ").title(),
                "caption": filename.replace(".jpg", "").replace("_", " ").title(),
                "image_prompt": "",  # Optional AI generation prompt
                "notes": "Created by check_images.py script",
                "image_metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "post_slug": post_slug,
                    "source": "check_images.py",
                },
                "watermarked": False,
                "watermarked_path": ""
            }
        ).fetchone()

    return image


def main():
    """Process images for the specified blog posts."""
    app = create_app()
    with app.app_context():
        # Process quaich-traditions post
        post = db.session.execute(
            "SELECT * FROM post WHERE slug = :slug",
            {"slug": "quaich-traditions"}
        ).fetchone()
        if post:
            # Set header image by adding it first to the images relationship
            header_image = create_image(
                "quaich-traditions_header-collage.jpg", "quaich-traditions"
            )
            if not db.session.execute(
                "SELECT * FROM post_images WHERE post_id = :post_id AND image_id = :image_id",
                {"post_id": post[0], "image_id": header_image[0]}
            ).fetchone():
                db.session.execute(
                    "INSERT INTO post_images (post_id, image_id) VALUES (:post_id, :image_id)",
                    {"post_id": post[0], "image_id": header_image[0]}
                )

            # Process section images
            for section in db.session.execute(
                "SELECT * FROM sections WHERE post_id = :post_id",
                {"post_id": post[0]}
            ).fetchall():
                if section[2]:
                    # Convert section title to filename format
                    section_slug = (
                        section[2].lower()
                        .replace(":", "")
                        .replace(" and ", "-")
                        .replace(" ", "-")
                    )
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
                        section_image = create_image(image_filename, "quaich-traditions")
                        if not db.session.execute(
                            "SELECT * FROM section_images WHERE section_id = :section_id AND image_id = :image_id",
                            {"section_id": section[0], "image_id": section_image[0]}
                        ).fetchone():
                            db.session.execute(
                                "INSERT INTO section_images (section_id, image_id) VALUES (:section_id, :image_id)",
                                {"section_id": section[0], "image_id": section_image[0]}
                            )

        # Process kilt-evolution post
        post = db.session.execute(
            "SELECT * FROM post WHERE slug = :slug",
            {"slug": "kilt-evolution"}
        ).fetchone()
        if post:
            # Set header image by adding it first to the images relationship
            header_image = create_image("kilt-evolution_header.jpg", "kilt-evolution")
            if not db.session.execute(
                "SELECT * FROM post_images WHERE post_id = :post_id AND image_id = :image_id",
                {"post_id": post[0], "image_id": header_image[0]}
            ).fetchone():
                db.session.execute(
                    "INSERT INTO post_images (post_id, image_id) VALUES (:post_id, :image_id)",
                    {"post_id": post[0], "image_id": header_image[0]}
                )

            # Process section images
            for section in db.session.execute(
                "SELECT * FROM sections WHERE post_id = :post_id",
                {"post_id": post[0]}
            ).fetchall():
                if section[2]:
                    # Convert section title to filename format
                    section_slug = (
                        section[2].lower()
                        .replace(":", "")
                        .replace(" and ", "-")
                        .replace(" ", "-")
                    )
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
                        section_image = create_image(image_filename, "kilt-evolution")
                        if not db.session.execute(
                            "SELECT * FROM section_images WHERE section_id = :section_id AND image_id = :image_id",
                            {"section_id": section[0], "image_id": section_image[0]}
                        ).fetchone():
                            db.session.execute(
                                "INSERT INTO section_images (section_id, image_id) VALUES (:section_id, :image_id)",
                                {"section_id": section[0], "image_id": section_image[0]}
                            )

        # Commit all changes
        try:
            db.session.commit()
            print("Successfully processed all images")
        except Exception as e:
            db.session.rollback()
            print(f"Error processing images: {str(e)}")


if __name__ == "__main__":
    main()
