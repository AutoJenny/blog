#!/usr/bin/env python3
import os
import sys
import yaml
import shutil
from datetime import datetime, UTC
from pathlib import Path

# Add the application root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import (
    Post,
    Category,
    Tag,
    Image,
    PostSection,
    WorkflowStatus,
    WorkflowStage,
    WorkflowStatusHistory,
)
from app.auth.models import User


def load_markdown_with_frontmatter(file_path):
    """Load a markdown file with YAML frontmatter."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Skip any comments or empty lines at the start of the file
    lines = content.split("\n")
    start_index = -1
    for i, line in enumerate(lines):
        if line.strip() == "---":
            start_index = i
            break

    if start_index >= 0:
        # Find the end of frontmatter
        end_index = -1
        for i in range(start_index + 1, len(lines)):
            if lines[i].strip() == "---":
                end_index = i
                break

        if end_index > start_index:
            # Extract frontmatter and content
            frontmatter = "\n".join(lines[start_index + 1 : end_index])
            content = "\n".join(lines[end_index + 1 :])

            print(f"\nDebug: Processing frontmatter for {file_path}")
            print("Raw frontmatter content:")
            print(frontmatter)
            print("---")

            # Parse the YAML frontmatter
            try:
                metadata = yaml.safe_load(frontmatter)
                print("Parsed metadata:")
                print(metadata)
            except yaml.YAMLError as e:
                print(f"Warning: Failed to parse YAML frontmatter in {file_path}: {e}")
                metadata = {}
        else:
            print(
                f"Warning: Invalid frontmatter format in {file_path} (no closing delimiter)"
            )
            metadata = {}
    else:
        print(f"Warning: No frontmatter found in {file_path} (no opening delimiter)")
        metadata = {}
        content = content

    return metadata, content.strip()


def ensure_category(name, session):
    """Ensure a category exists in the database."""
    category = Category.query.filter_by(name=name).first()
    if not category:
        category = Category()
        category.name = name
        category.slug = name.lower().replace(" ", "-")
        category.description = None
        session.add(category)
        session.flush()
    return category


def ensure_tag(name, session):
    """Ensure a tag exists in the database."""
    tag = Tag.query.filter_by(name=name).first()
    if not tag:
        tag = Tag()
        tag.name = name
        tag.slug = name.lower().replace(" ", "-")
        tag.description = None
        session.add(tag)
        session.flush()
    return tag


def find_image_file(image_id, post_slug, old_images_dir):
    """Find the corresponding image file for an image ID."""
    post_images_dir = os.path.join(old_images_dir, "posts", post_slug)
    if not os.path.exists(post_images_dir):
        print(f"Warning: Post images directory not found at {post_images_dir}")
        return None

    # For header image
    if image_id == "IMG00001":
        # Try different formats for header image
        for ext in [".jpg", ".png", ".webp"]:
            header_file = os.path.join(post_images_dir, f"{post_slug}_header{ext}")
            if os.path.exists(header_file):
                return header_file
        print(f"Warning: Header image not found for {post_slug} in any format")
        return None

    # For section images, try to find by scanning directory
    processed_images = []
    for file in os.listdir(post_images_dir):
        # Skip raw files
        if any(f"_raw.{ext}" in file.lower() for ext in ["jpg", "png", "webp"]):
            continue
        # Skip header
        if any(f"_header.{ext}" in file.lower() for ext in ["jpg", "png", "webp"]):
            continue
        # Found a processed image file
        if any(file.lower().endswith(ext) for ext in [".jpg", ".png", ".webp"]):
            processed_images.append(os.path.join(post_images_dir, file))

    if processed_images:
        # If multiple processed images found, prefer jpg > png > webp
        for ext in [".jpg", ".png", ".webp"]:
            for img in processed_images:
                if img.lower().endswith(ext):
                    return img
        # If no preferred format found, return the first one
        return processed_images[0]

    print(f"Warning: No suitable image found for ID {image_id} in {post_images_dir}")
    return None


def migrate_image(image_id, post_slug, static_dir, old_images_dir, session):
    """Migrate an image file and create an Image record."""
    image_file = find_image_file(image_id, post_slug, old_images_dir)
    if not image_file:
        print(f"Warning: Image file not found for ID {image_id}")
        return None

    filename = os.path.basename(image_file)
    original_filename = filename.replace(".jpg", "_raw.jpg")
    new_path = f"images/posts/{post_slug}/{filename}"  # Remove leading /static/ as it's added by url_for

    # Check if image already exists
    existing_image = Image.query.filter_by(path=new_path).first()
    if existing_image:
        print(f"Image already exists with path {new_path}")
        return existing_image

    image = Image()
    image.filename = filename
    image.original_filename = original_filename
    image.path = new_path
    image.alt_text = ""  # Can be updated later
    image.caption = ""  # Can be updated later
    image.image_prompt = ""  # No prompt for migrated images
    image.notes = f"Migrated from old blog - ID: {image_id}"
    image.image_metadata = {
        "original_id": image_id,
        "has_raw_version": os.path.exists(
            os.path.join(os.path.dirname(image_file), original_filename)
        ),
    }
    image.watermarked = False
    image.watermarked_path = None
    image.created_at = datetime.now(UTC)  # Use timezone-aware datetime
    image.updated_at = datetime.now(UTC)  # Use timezone-aware datetime

    session.add(image)
    session.flush()

    # Copy both processed and raw files if they exist
    target_dir = os.path.join(static_dir, "images", "posts", post_slug)
    os.makedirs(target_dir, exist_ok=True)

    # Copy processed image
    shutil.copy2(image_file, os.path.join(target_dir, filename))

    # Copy raw image if it exists
    raw_file = os.path.join(os.path.dirname(image_file), original_filename)
    if os.path.exists(raw_file):
        shutil.copy2(raw_file, os.path.join(target_dir, original_filename))

    return image


def migrate_post(file_path, app):
    """Migrate a single post."""
    print(f"\nProcessing file: {file_path}")
    metadata, content = load_markdown_with_frontmatter(file_path)
    if not metadata:
        print(f"Warning: No metadata found in {file_path}")
        print("Available metadata keys:", list(metadata.keys()) if metadata else "None")
        return

    print("Found metadata with keys:", list(metadata.keys()))

    with app.app_context():
        # Start a transaction
        try:
            # Generate slug from title if not provided
            slug = metadata.get("slug", "").strip()
            title = metadata.get("title", "").strip()

            if not slug and not title:
                print(f"Warning: Neither slug nor title found in {file_path}")
                print("Available metadata:", metadata)
                return

            if not slug:
                # Remove quotes if present in title
                title = title.strip('"').strip("'")
                # Generate slug from title
                slug = title.lower().replace(" ", "-")
                # Remove any non-alphanumeric characters except hyphens
                slug = "".join(c for c in slug if c.isalnum() or c == "-")
                # Replace multiple hyphens with single hyphen
                slug = "-".join(filter(None, slug.split("-")))
                print(f"Generated slug '{slug}' from title '{title}'")

            if not slug:  # If we still don't have a slug
                print(f"Warning: Could not generate valid slug for {file_path}")
                return

            # Check if post already exists and update it if it does
            post = Post.query.filter_by(slug=slug).first()
            is_update = post is not None

            if is_update:
                print(f"Post with slug '{slug}' already exists, updating...")
                # Delete existing sections to recreate them
                PostSection.query.filter_by(post_id=post.id).delete()
                db.session.flush()
            else:
                post = Post()
                print(f"Creating new post: {title} (slug: {slug})")

            # Get the date, handling both string and datetime objects
            post_date = metadata.get("date")
            if isinstance(post_date, str):
                try:
                    post_date = datetime.strptime(post_date, "%Y-%m-%d")
                except ValueError:
                    print(
                        f"Warning: Invalid date format in {file_path}, using current time"
                    )
                    post_date = datetime.now(UTC)
            elif not isinstance(post_date, datetime):
                post_date = datetime.now(UTC)

            # Update post
            post.title = title
            post.slug = slug
            post.content = ""  # Content will be in sections
            post.summary = metadata.get("summary", "")
            post.concept = metadata.get("concept", "")
            post.published = True
            post.deleted = False
            if not is_update:
                post.created_at = post_date
                post.published_at = post_date
            post.updated_at = datetime.now(UTC)
            post.author_id = 1  # Placeholder author ID
            if "headerImage" in metadata and metadata["headerImage"].get("src"):
                print("Found header image in metadata")
                header_image = migrate_image(
                    "IMG00001",
                    slug,
                    os.path.join(app.root_path, "static"),
                    os.path.join(app.root_path, "..", "images"),
                    db.session,
                )
                post.header_image = header_image
            post.llm_metadata = post.llm_metadata or {}
            post.seo_metadata = {"description": metadata.get("description", "")}
            post.syndication_status = post.syndication_status or {}

            if not is_update:
                print(f"Adding new post to session: {post.title}")
                db.session.add(post)
            db.session.flush()  # Get the post ID

            # Handle workflow status
            workflow_status = WorkflowStatus.query.filter_by(post_id=post.id).first()
            if not workflow_status:
                workflow_status = WorkflowStatus()
                workflow_status.post_id = post.id
                workflow_status.current_stage = WorkflowStage.PUBLISHING
                workflow_status.stage_data = {}
                workflow_status.last_updated = datetime.now(UTC)
                db.session.add(workflow_status)
                db.session.flush()

                # Create workflow history
                history = WorkflowStatusHistory()
                history.workflow_status_id = workflow_status.id
                history.from_stage = WorkflowStage.CONCEPTUALIZATION
                history.to_stage = WorkflowStage.PUBLISHING
                history.user_id = 1  # Placeholder user ID
                history.notes = "Post migrated from old blog"
                db.session.add(history)

            # Handle tags
            if not is_update:
                for tag_name in metadata.get("tags", []):
                    tag = ensure_tag(tag_name, db.session)
                    if tag and tag not in post.tags:
                        post.tags.append(tag)

            # Handle sections
            position = 1
            sections = metadata.get("sections", [])
            print(f"Processing {len(sections)} sections")

            for section in sections:
                print(f"Processing section {position}: {section.get('heading', '')}")

                # Handle section image
                section_image = None
                if "imageId" in section:
                    print(f"Found section image ID: {section['imageId']}")
                    section_image = migrate_image(
                        section["imageId"],
                        slug,
                        os.path.join(app.root_path, "static"),
                        os.path.join(app.root_path, "..", "images"),
                        db.session,
                    )

                post_section = PostSection()
                post_section.post_id = post.id
                post_section.title = section.get("heading", "")
                post_section.subtitle = section.get("subheading", "")
                post_section.content = section.get("text", "")
                post_section.position = position
                post_section.image = section_image
                post_section.content_type = section.get("type", "text")
                post_section.video_url = section.get("videoUrl", None)
                post_section.audio_url = section.get("audioUrl", None)
                post_section.duration = section.get("duration", None)

                # Extract keywords if present
                keywords = section.get("keywords", [])
                if isinstance(keywords, str):
                    keywords = [k.strip() for k in keywords.split(",")]
                post_section.keywords = {"keywords": keywords} if keywords else {}

                # Initialize social media snippets
                post_section.social_media_snippets = {
                    "twitter": section.get("twitterSnippet", ""),
                    "facebook": section.get("facebookSnippet", ""),
                    "instagram": section.get("instagramSnippet", ""),
                }

                # Store all remaining metadata
                section_metadata = {
                    k: v
                    for k, v in section.items()
                    if k
                    not in [
                        "heading",
                        "subheading",
                        "text",
                        "type",
                        "videoUrl",
                        "audioUrl",
                        "duration",
                        "keywords",
                        "twitterSnippet",
                        "facebookSnippet",
                        "instagramSnippet",
                        "imageId",
                    ]
                }
                post_section.section_metadata = section_metadata

                print(f"Adding section {position} to post {post.title}")
                db.session.add(post_section)
                position += 1

            # Handle conclusion as final section if present
            if "conclusion" in metadata:
                conclusion = metadata["conclusion"]
                print("Processing conclusion section")

                conclusion_image = None
                if "imageId" in conclusion:
                    print(f"Found conclusion image ID: {conclusion['imageId']}")
                    conclusion_image = migrate_image(
                        conclusion["imageId"],
                        slug,
                        os.path.join(app.root_path, "static"),
                        os.path.join(app.root_path, "..", "images"),
                        db.session,
                    )

                post_section = PostSection()
                post_section.post_id = post.id
                post_section.title = conclusion.get("heading", "Conclusion")
                post_section.subtitle = conclusion.get("subheading", "")
                post_section.content = conclusion.get("text", "")
                post_section.position = position
                post_section.image = conclusion_image
                post_section.content_type = conclusion.get("type", "text")
                post_section.video_url = conclusion.get("videoUrl", None)
                post_section.audio_url = conclusion.get("audioUrl", None)
                post_section.duration = conclusion.get("duration", None)

                # Extract keywords if present
                keywords = conclusion.get("keywords", [])
                if isinstance(keywords, str):
                    keywords = [k.strip() for k in keywords.split(",")]
                post_section.keywords = {"keywords": keywords} if keywords else {}

                # Initialize social media snippets
                post_section.social_media_snippets = {
                    "twitter": conclusion.get("twitterSnippet", ""),
                    "facebook": conclusion.get("facebookSnippet", ""),
                    "instagram": conclusion.get("instagramSnippet", ""),
                }

                # Store all remaining metadata plus conclusion flag
                section_metadata = {
                    k: v
                    for k, v in conclusion.items()
                    if k
                    not in [
                        "heading",
                        "subheading",
                        "text",
                        "type",
                        "videoUrl",
                        "audioUrl",
                        "duration",
                        "keywords",
                        "twitterSnippet",
                        "facebookSnippet",
                        "instagramSnippet",
                        "imageId",
                    ]
                }
                section_metadata["is_conclusion"] = True
                post_section.section_metadata = section_metadata

                print(f"Adding conclusion section to post {post.title}")
                db.session.add(post_section)

            print(f"Committing changes for post: {post.title}")
            db.session.commit()
            print(
                f"Successfully {'updated' if is_update else 'migrated'} post: {post.title}"
            )

        except Exception as e:
            db.session.rollback()
            print(f"Failed to migrate {file_path}: {str(e)}")
            import traceback

            traceback.print_exc()
            raise


def main():
    """Main migration function."""
    app = create_app()
    old_posts_dir = os.path.join(app.root_path, "..", "__blog_old", "posts")

    # Ensure the old posts directory exists
    if not os.path.exists(old_posts_dir):
        print(f"Error: Old posts directory not found at {old_posts_dir}")
        return

    # Process each markdown file
    for file_path in Path(old_posts_dir).glob("*.md"):
        try:
            migrate_post(file_path, app)
        except Exception as e:
            print(f"Failed to migrate {file_path}: {str(e)}")


if __name__ == "__main__":
    main()
