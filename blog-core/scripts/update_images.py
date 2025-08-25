import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Image

# Image ID to filename mapping
IMAGE_MAP = {
    # Kilt Evolution
    "kilt-evolution_header": "Header image for kilt evolution article",
    "kilt-evolution_early-highland-dress": "Early forms of Highland dress",
    "kilt-evolution_great-kilt-origins": "Origins of the Great Kilt",
    "kilt-evolution_great-kilt-significance": "Cultural significance of the Great Kilt",
    "kilt-evolution_kilt-adaptations-practicality": "Practical adaptations of the kilt",
    "kilt-evolution_small-kilt-emergence": "Emergence of the Small Kilt",
    "kilt-evolution_highland-dress-suppression": "Suppression of Highland dress",
    "kilt-evolution_romantic-revival-renaissance": "Romantic revival of Highland dress",
    "kilt-evolution_military-adoption-influence": "Military influence on kilt adoption",
    "kilt-evolution_formal-everyday-attire": "Kilt as formal attire",
    "kilt-evolution_modern-innovations-fashion": "Modern kilt innovations",
    # Quaich Traditions
    "quaich-traditions_header-collage": "Header collage for quaich traditions",
    "quaich-traditions_early-origins-wooden": "Early wooden quaich origins",
    "quaich-traditions_clan-unity-hospitality": "Quaich in clan unity and hospitality",
    "quaich-traditions_design-evolution": "Evolution of quaich design",
    "quaich-traditions_royal-gift": "Quaich as royal gifts",
    "quaich-traditions_whisky-pairing": "Quaich in whisky traditions",
    "quaich-traditions_decline-revival": "Decline and revival of quaich use",
    "quaich-traditions_contemporary-culture": "Quaich in contemporary culture",
    "quaich-traditions_modern-diplomacy": "Quaich in modern diplomacy",
    "quaich-traditions_collecting-quaichs": "Collecting historic quaichs",
    "quaich-traditions_wedding-ceremony": "Quaich in wedding ceremonies",
}


def update_images():
    """Update image records in the database with correct paths and metadata."""
    app = create_app()
    with app.app_context():
        for base_name, description in IMAGE_MAP.items():
            folder = base_name.split("_")[
                0
            ]  # e.g., "kilt-evolution" or "quaich-traditions"

            # Try common image extensions
            for ext in [".jpg", ".jpeg", ".png", ".gif"]:
                filename = base_name + ext
                path = os.path.join("images", "posts", folder, filename)

                # Check if image exists in static folder
                if os.path.exists(os.path.join("app", "static", path)):
                    # Create or update image record
                    image = Image.query.filter_by(filename=filename).first()
                    if not image:
                        image = Image()
                        db.session.add(image)

                    # Update image attributes
                    image.filename = filename
                    image.original_filename = filename
                    image.path = path
                    image.alt_text = description
                    image.caption = description
                    image.notes = f"Updated via direct import script"
                    image.image_metadata = {
                        "import_date": datetime.utcnow().isoformat(),
                        "base_name": base_name,
                    }

                    print(f"Updated image: {filename}")
                    break  # Found the image, no need to try other extensions

        # Commit all changes
        try:
            db.session.commit()
            print("Successfully updated all images")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating images: {str(e)}")


if __name__ == "__main__":
    update_images()
