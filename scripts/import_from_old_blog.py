import os
import glob
import json
import frontmatter
import shutil
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import create_app, db
from app.models import Post, PostSection, Image
from flask import Flask
from datetime import datetime
from sqlalchemy import exists

OLD_POSTS_DIR = '__blog_old/posts/'
IMAGE_LIBRARY_PATH = '__blog_old/_data/image_library.json'
NEW_IMAGE_DIR = '../../app/static/images/posts/'
WORKFLOW_STATUS_PATH = '../../blog_old/_data/workflow_status.json'

app = create_app()
app.app_context().push()

def main():
    # 1. Parse Markdown posts
    post_files = glob.glob(os.path.join(OLD_POSTS_DIR, '*.md'))
    posts = []
    for path in post_files:
        with open(path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            posts.append({'path': path, 'frontmatter': post.metadata, 'content': post.content})

    # 2. Parse image library
    with open(IMAGE_LIBRARY_PATH, 'r', encoding='utf-8') as f:
        image_library = json.load(f)

    # Import images
    image_objs = {}
    imported_images = 0
    skipped_images = 0
    for img_id, img_data in image_library.items():
        sd = img_data.get('source_details', {})
        if 'local_dir' not in sd or 'filename_local' not in sd:
            print(f"Warning: Skipping image {img_id} due to missing local_dir or filename_local.")
            continue
        filename = sd['filename_local']
        # Fix image path: if local_dir starts with '/images/posts/', use '__blog_old/_site/images/posts/'
        local_dir = sd['local_dir']
        if local_dir.startswith('/images/posts/'):
            local_dir = os.path.join('__blog_old/_site', local_dir.lstrip('/'))
        full_path = os.path.join(local_dir, filename)
        # Check if image already exists by filename
        if db.session.query(exists().where(Image.filename == filename)).scalar():
            skipped_images += 1
            continue
        # Copy image file to new location
        dest_dir = os.path.join(NEW_IMAGE_DIR)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)
        try:
            shutil.copy2(full_path, dest_path)
        except Exception as e:
            print(f"Warning: Could not copy image {full_path} to {dest_path}: {e}")
        image = Image(
            filename=filename,
            path=dest_path,
            alt_text=img_data.get('metadata', {}).get('alt', ''),
            caption=img_data.get('metadata', {}).get('blog_caption', ''),
            image_prompt=img_data.get('prompt', ''),
            notes=img_data.get('notes', ''),
            image_metadata=img_data,
        )
        db.session.add(image)
        db.session.flush()  # get image.id
        image_objs[img_id] = image
        imported_images += 1

    # Import posts and sections
    imported_posts = 0
    skipped_posts = 0
    imported_sections = 0
    for post in posts:
        fm = post['frontmatter']
        slug = fm.get('slug') or os.path.splitext(os.path.basename(post['path']))[0]
        # Check if post already exists by slug
        if db.session.query(exists().where(Post.slug == slug)).scalar():
            skipped_posts += 1
            continue
        title = fm.get('title', slug)[:200]
        summary = fm.get('summary', '')
        published = fm.get('published', False)
        deleted = fm.get('deleted', False)
        created_at = fm.get('date', datetime.utcnow())
        header_image_id = None
        if 'headerImageId' in fm and fm['headerImageId'] in image_objs:
            header_image_id = image_objs[fm['headerImageId']].id
        p = Post(
            title=title,
            slug=slug,
            summary=summary,
            published=published,
            deleted=deleted,
            created_at=created_at,
            header_image_id=header_image_id
        )
        db.session.add(p)
        db.session.flush()  # get p.id
        imported_posts += 1
        # Sections
        for i, section in enumerate(fm.get('sections', [])):
            s = PostSection(
                post_id=p.id,
                section_order=i,
                section_heading=section.get('heading', ''),
                first_draft=section.get('text', ''),
            )
            db.session.add(s)
            imported_sections += 1
    db.session.commit()
    print(f"Imported {imported_posts} posts, {imported_sections} sections, {imported_images} images.")
    print(f"Skipped {skipped_posts} posts, {skipped_images} images (already existed).")

if __name__ == '__main__':
    main() 