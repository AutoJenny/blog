from app import create_app, db
from app.models import Post, Image, PostSection

app = create_app()

with app.app_context():
    # Quaich Traditions mappings
    mappings = {
        "Early Origins: Ancient Beginnings and Symbolic Meaning": "quaich-traditions_early-origins-wooden.jpg",
        "Symbol of Clan Unity and Hospitality": "quaich-traditions_clan-unity-hospitality.jpg",
        "Evolution of Design: Materials and Craftsmanship": "quaich-traditions_design-evolution.jpg",
        "Quaich and Royal Connections": "quaich-traditions_royal-gift.jpg",
        "Quaich Traditions and Whisky: A Timeless Pairing": "quaich-traditions_whisky-pairing.jpg",
        "Cultural Decline and Revival": "quaich-traditions_decline-revival.jpg",
        "The Quaich in Contemporary Scottish Culture": "quaich-traditions_contemporary-culture.jpg",
        "Quaich as a Modern Symbol of Friendship and Diplomacy": "quaich-traditions_modern-diplomacy.jpg",
        "Collecting Quaichs: Preservation and Modern Appeal": "quaich-traditions_collecting-quaichs.jpg",
        "The Quaich in Ceremony and Celebration": "quaich-traditions_wedding-ceremony.jpg",
    }

    post = Post.query.filter_by(slug="quaich-traditions").first()
    if post:
        for section in post.sections:
            if section.title in mappings:
                image = Image.query.filter_by(filename=mappings[section.title]).first()
                if image:
                    section.image = image
                    print(
                        f'Matched section "{section.title}" with image {image.filename}'
                    )

    # Kilt Evolution mappings
    mappings = {
        "Early Origins: The Great Kilt": "kilt-evolution_great-kilt-origins.jpg",
        "The Birth of the Modern Kilt": "kilt-evolution_small-kilt-emergence.jpg",
        "Proscription and Revival": "kilt-evolution_highland-dress-suppression.jpg",
        "Victorian Influence and Romanticization": "kilt-evolution_romantic-revival-renaissance.jpg",
        "Military Adoption and Influence": "kilt-evolution_military-adoption-influence.jpg",
        "Modern Innovations and Adaptations": "kilt-evolution_kilt-adaptations-practicality.jpg",
        "Cultural Significance Today": "kilt-evolution_formal-everyday-attire.jpg",
    }

    post = Post.query.filter_by(slug="kilt-evolution").first()
    if post:
        for section in post.sections:
            if section.title in mappings:
                image = Image.query.filter_by(filename=mappings[section.title]).first()
                if image:
                    section.image = image
                    print(
                        f'Matched section "{section.title}" with image {image.filename}'
                    )

    db.session.commit()
    print("Successfully updated all section-image associations")
