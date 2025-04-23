import os
import sys
import glob
import frontmatter
from datetime import datetime
from slugify import slugify
import shutil
from PIL import Image as PILImage
import json
import uuid
from flask import current_app

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import (
    Post,
    User,
    Category,
    Tag,
    PostSection,
    Image,
    WorkflowStatus,
    WorkflowStage,
)

# Image ID to filename mapping
IMAGE_ID_MAP = {
    # Kilt Evolution
    "IMG00001": "kilt-evolution_header",  # Header
    "IMG00002": "kilt-evolution_early-highland-dress",  # Early Forms
    "IMG00003": "kilt-evolution_great-kilt-origins",  # Origins
    "IMG00004": "kilt-evolution_great-kilt-significance",  # Cultural Significance
    "IMG00005": "kilt-evolution_kilt-adaptations-practicality",  # Adaptations
    "IMG00006": "kilt-evolution_small-kilt-emergence",  # Small Kilt
    "IMG00007": "kilt-evolution_highland-dress-suppression",  # Suppression
    "IMG00008": "kilt-evolution_romantic-revival-renaissance",  # Revival
    "IMG00009": "kilt-evolution_military-adoption-influence",  # Military
    "IMG00010": "kilt-evolution_formal-everyday-attire",  # Formal
    "IMG00011": "kilt-evolution_modern-innovations-fashion",  # Modern
    # Quaich Traditions
    "IMG00012": "quaich-traditions_header-collage",  # Header
    "IMG00013": "quaich-traditions_early-origins-wooden",  # Early Origins
    "IMG00014": "quaich-traditions_clan-unity-hospitality",  # Clan Unity
    "IMG00015": "quaich-traditions_design-evolution",  # Design Evolution
    "IMG00016": "quaich-traditions_royal-gift",  # Royal Connections
    "IMG00017": "quaich-traditions_whisky-pairing",  # Whisky Pairing
    "IMG00018": "quaich-traditions_decline-revival",  # Decline and Revival
    "IMG00019": "quaich-traditions_contemporary-culture",  # Contemporary
    "IMG00020": "quaich-traditions_modern-diplomacy",  # Modern Diplomacy
    "IMG00021": "quaich-traditions_collecting-quaichs",  # Collecting
    "IMG00022": "quaich-traditions_wedding-ceremony",  # Ceremony
}


def get_or_create_user():
    """Get or create the default user for imported posts."""
    user = User.query.filter_by(username="admin").first()
    if not user:
        user = User()
        user.username = "admin"
        user.email = "admin@example.com"
        user.is_admin = True
        user.set_password("changeme123")
        db.session.add(user)
        db.session.commit()
    return user


def find_image_file(base_name, posts_dir):
    """Find an image file by its base name in the posts directory."""
    # Check in the posts directory and its subdirectories
    for root, _, files in os.walk(posts_dir):
        for file in files:
            if file.startswith(base_name) and file.lower().endswith(
                (".jpg", ".jpeg", ".png", ".gif")
            ):
                return os.path.join(root, file)
    return None


def get_or_create_image(image_data):
    """Get or create an image."""
    if not image_data:
        return None

    filename = image_data.get("filename")
    if not filename:
        return None

    image = Image.query.filter_by(filename=filename).first()
    if not image:
        image = Image(
            filename=filename,
            original_filename=image_data.get("original_filename", filename),
            path=image_data.get("path", ""),
            alt_text=image_data.get("alt_text", ""),
            caption=image_data.get("caption", ""),
            image_prompt=image_data.get("image_prompt", ""),
            notes=image_data.get("notes", ""),
            image_metadata=image_data.get("metadata", {}),
            watermarked=image_data.get("watermarked", False),
            watermarked_path=image_data.get("watermarked_path", ""),
        )
        db.session.add(image)
        db.session.commit()
    return image


def get_or_create_category(name):
    """Get or create a category by name."""
    category = Category.query.filter_by(name=name).first()
    if not category:
        category = Category(name=name, slug=slugify(name))
        db.session.add(category)
        db.session.commit()
    return category


def get_or_create_tag(name):
    """Get or create a tag by name."""
    tag = Tag.query.filter_by(name=name).first()
    if not tag:
        tag = Tag(name=name, slug=slugify(name))
        db.session.add(tag)
        db.session.commit()
    return tag


def get_image_filename_by_id(post_slug, image_id):
    """Map image IDs to actual filenames based on post slug and image ID."""
    # Remove the post slug prefix from image_id if it exists
    if image_id.startswith(f"{post_slug}_"):
        image_id = image_id[len(post_slug) + 1 :]

    # Construct the base filename
    base_filename = f"{post_slug}_{image_id}"

    # Define possible extensions and variants
    extensions = [".jpg", ".png", ".webp"]
    variants = ["_raw", ""]

    # Check for existence of files in the images directory
    for ext in extensions:
        for variant in variants:
            filename = f"{base_filename}{variant}{ext}"
            path = os.path.join("images", "posts", post_slug, filename)
            if os.path.exists(path):
                return filename

    return None


def process_image_by_id(image_id, image_info, db_session):
    """Process an image by its ID and create/update the corresponding Image record."""
    if not image_id:
        print(f"Warning: No image ID provided in image_info: {image_info}")
        return None

    if not image_info.get("filename"):
        print(f"Warning: No filename found for image ID {image_id}")
        return None

    try:
        # Create a new Image instance
        image = Image()

        # Set attributes directly
        image.filename = image_info.get("filename")
        image.original_filename = image_info.get(
            "original_filename", image_info.get("filename")
        )
        image.path = image_info.get("path", "")
        image.alt_text = image_info.get("alt_text", "")
        image.caption = image_info.get("caption", "")
        image.image_prompt = image_info.get("image_prompt", "")
        image.notes = image_info.get("notes", "")
        image.image_metadata = image_info.get("image_metadata", {})
        image.watermarked = image_info.get("watermarked", False)
        image.watermarked_path = image_info.get("watermarked_path", "")

        # Add to session and flush to get the ID
        db_session.add(image)
        db_session.flush()

        print(f"Created image record for {image_id}: {image.filename}")
        return image

    except Exception as e:
        print(f"Error processing image {image_id}: {str(e)}")
        return None


def create_or_update_post(frontmatter_data, content, post_slug):
    """Create or update a blog post with the given data."""
    try:
        # Get or create the post
        post = Post.query.filter_by(slug=post_slug).first()
        if not post:
            post = Post()

        # Update basic post information
        post.title = frontmatter_data.get("title", "")
        post.slug = post_slug
        post.content = content
        post.draft = frontmatter_data.get("draft", True)
        post.published_date = frontmatter_data.get("date")
        post.last_modified_date = frontmatter_data.get("last_modified")
        post.seo_metadata = frontmatter_data.get("seo", {})
        post.syndication_status = frontmatter_data.get("syndication_status", {})
        post.llm_metadata = frontmatter_data.get("llm_metadata", {})

        # Clear existing relationships
        post.categories = []
        post.tags = []
        if hasattr(post, "sections"):
            for section in post.sections:
                db.session.delete(section)
            db.session.flush()

        # Process categories
        categories = frontmatter_data.get("categories", [])
        for category_name in categories:
            category = get_or_create_category(category_name)
            if category:
                post.categories.append(category)

        # Process tags
        tags = frontmatter_data.get("tags", [])
        for tag_name in tags:
            tag = get_or_create_tag(tag_name)
            if tag:
                post.tags.append(tag)

        # Process sections
        sections_data = frontmatter_data.get("sections", [])
        for idx, section_data in enumerate(sections_data):
            section = PostSection(
                post=post,
                position=idx,
                title=section_data.get("title", ""),
                content=section_data.get("content", ""),
                metadata=section_data.get("metadata", {}),
            )

            # Process section images
            image_id = section_data.get("image_id")
            if image_id:
                image = process_image_by_id(
                    image_id, section_data.get("image_info", {}), db.session
                )
                if image:
                    section.image = image

            db.session.add(section)

        # Set workflow status if not already set
        if not post.current_status:
            status = WorkflowStatusHistory(
                post=post,
                status="draft",
                user=get_or_create_user(),
                notes="Initial import",
            )
            db.session.add(status)

        db.session.add(post)
        db.session.commit()
        logger.info(f"Successfully processed post: {post_slug}")
        return post

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing post {post_slug}: {str(e)}")
        raise


def import_posts(posts_dir):
    """Import all markdown posts from a directory."""
    app = create_app()
    with app.app_context():
        user = get_or_create_user()

        # Process all markdown files in the directory
        for filename in os.listdir(posts_dir):
            if filename.endswith(".md"):
                md_file = os.path.join(posts_dir, filename)
                try:
                    post = create_or_update_post(md_file, user)
                    print(f"Successfully imported/updated post: {post.title}")
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")


if __name__ == "__main__":
    posts_dir = "__blog_old/posts"
    import_posts(posts_dir)
