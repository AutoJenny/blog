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
    WorkflowStatusHistory,
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
        # Create new image instance and set attributes directly
        image = Image()
        image.filename = filename
        image.original_filename = image_data.get("original_filename", filename)
        image.path = image_data.get("path", "")
        image.alt_text = image_data.get("alt_text", "")
        image.caption = image_data.get("caption", "")
        image.image_prompt = image_data.get("image_prompt", "")
        image.notes = image_data.get("notes", "")
        image.image_metadata = image_data.get("metadata", {})
        image.watermarked = image_data.get("watermarked", False)
        image.watermarked_path = image_data.get("watermarked_path", "")

        db.session.add(image)
        db.session.commit()
    return image


def get_or_create_category(name):
    """Get or create a category by name."""
    category = Category.query.filter_by(name=name).first()
    if not category:
        category = Category()
        category.name = name
        category.slug = slugify(name)
        db.session.add(category)
        db.session.commit()
    return category


def get_or_create_tag(name):
    """Get or create a tag by name."""
    tag = Tag.query.filter_by(name=name).first()
    if not tag:
        tag = Tag()
        tag.name = name
        tag.slug = slugify(name)
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

        # Set attributes directly on the instance
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


def create_or_update_post(metadata, content, post_slug):
    """Create or update a blog post with the given metadata and content."""
    try:
        # Find existing post or create new one
        post = Post.query.filter_by(slug=post_slug).first()
        if not post:
            post = Post()
            post.slug = post_slug
            db.session.add(post)

        # Update post attributes from metadata
        post.title = metadata.get("title", "")
        post.content = content
        post.seo_metadata = metadata.get("seo_metadata", {})
        post.syndication_status = metadata.get("syndication_status", {})
        post.llm_metadata = metadata.get("llm_metadata", {})
        post.published = metadata.get("published", False)
        post.published_at = metadata.get("publish_date")

        # Process categories
        if "categories" in metadata:
            # Clear existing categories
            post.categories = []  # This uses the backref defined in Category model
            for cat_name in metadata["categories"]:
                category = get_or_create_category(cat_name)
                post.categories.append(category)

        # Process tags
        if "tags" in metadata:
            # Clear existing tags
            post.tags = []  # This uses the relationship defined in Post model
            for tag_name in metadata["tags"]:
                tag = get_or_create_tag(tag_name)
                post.tags.append(tag)

        # Process images
        if "images" in metadata:
            # Clear existing images
            post.header_image = None  # Reset header image
            for image_id in metadata["images"]:
                # Get the mapped filename from IMAGE_ID_MAP
                base_filename = IMAGE_ID_MAP.get(image_id)
                if base_filename:
                    # Prepare image info
                    image_info = {
                        "filename": f"{base_filename}.jpg",  # Assuming jpg for now
                        "original_filename": f"{base_filename}.jpg",
                        "path": f"images/posts/{post_slug}/{base_filename}.jpg",
                        "alt_text": base_filename.replace("_", " ").title(),
                        "caption": "",
                        "image_prompt": "",
                        "notes": f"Imported from old blog - ID: {image_id}",
                        "image_metadata": {},
                        "watermarked": False,
                        "watermarked_path": "",
                    }
                    image = process_image_by_id(image_id, image_info, db.session)
                    if image and not post.header_image:
                        post.header_image = image  # Set first image as header image
                else:
                    print(f"Warning: No mapping found for image ID {image_id}")

        # Clear existing sections and commit to avoid constraint errors
        if post.sections:
            for section in post.sections:
                db.session.delete(section)
            db.session.commit()

        # Create new sections from content
        sections = process_content_sections(content)
        for position, section_data in enumerate(sections):
            section_content = section_data.get("content", "")
            section_title = section_data.get("title", "")

            post_section = PostSection()
            post_section.post = post
            post_section.content = section_content
            post_section.title = section_title
            post_section.position = position
            post_section.content_type = "text"
            db.session.add(post_section)

        # Set workflow status if not already set
        if not post.workflow_status:
            # Create workflow status
            workflow_status = WorkflowStatus(
                post=post, current_stage=WorkflowStage.IDEA
            )
            db.session.add(workflow_status)

            # Add initial workflow history entry
            history = WorkflowStatusHistory(
                workflow_status=workflow_status,
                from_stage=WorkflowStage.IDEA,
                to_stage=WorkflowStage.IDEA,
                user=user,
                notes="Post imported from old blog",
            )
            db.session.add(history)

        db.session.commit()
        return post

    except Exception as e:
        db.session.rollback()
        print(f"Error creating/updating post {post_slug}: {str(e)}")
        return None


def process_content_sections(content):
    """Split content into sections based on ## headers."""
    sections = []
    current_section = {"title": "", "content": []}
    lines = content.split("\n")

    for line in lines:
        if line.startswith("## "):
            # If we have content in the current section, save it
            if current_section["content"]:
                sections.append(
                    {
                        "title": current_section["title"],
                        "content": "\n".join(current_section["content"]).strip(),
                    }
                )
            # Start a new section
            current_section = {
                "title": line[3:].strip(),  # Remove "## " prefix
                "content": [],
            }
        else:
            current_section["content"].append(line)

    # Add the last section if it has content
    if current_section["content"]:
        sections.append(
            {
                "title": current_section["title"],
                "content": "\n".join(current_section["content"]).strip(),
            }
        )

    # If no sections were created, use the entire content as one section
    if not sections:
        sections = [{"title": "Main Content", "content": content.strip()}]

    return sections


def import_posts(posts_dir):
    """Import all markdown posts from a directory."""
    app = create_app()
    with app.app_context():
        # Process all markdown files in the directory
        for filename in os.listdir(posts_dir):
            if filename.endswith(".md"):
                md_file = os.path.join(posts_dir, filename)
                try:
                    # Read and parse the markdown file
                    with open(md_file, "r", encoding="utf-8") as f:
                        post_data = frontmatter.load(f)

                    # Extract frontmatter and content
                    metadata = post_data.metadata
                    content = post_data.content

                    # Get post slug from filename
                    post_slug = os.path.splitext(filename)[0]

                    # Create or update the post
                    post = create_or_update_post(metadata, content, post_slug)
                    print(f"Successfully imported/updated post: {post.title}")
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")


if __name__ == "__main__":
    posts_dir = "__blog_old/posts"
    import_posts(posts_dir)
