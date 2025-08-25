import os
import sys
from datetime import datetime
from flask import Flask
from app import create_app, db
from app.models import Post, PostDevelopment, PostSection, Image

# Import MOCK_POSTS from preview
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/preview')))
from __init__ import MOCK_POSTS

def migrate_mock_posts():
    with create_app().app_context():
        for mock in MOCK_POSTS:
            # Check for existing post by slug or title
            slug = mock['title'].lower().replace(' ', '-')[:80]
            post = Post.query.filter_by(slug=slug).first()
            if not post:
                post = Post(
                    title=mock['title'],
                    slug=slug,
                    summary=mock.get('summary', ''),
                    published=False,
                    deleted=False,
                    created_at=mock.get('created_at', datetime.utcnow()),
                    updated_at=mock.get('created_at', datetime.utcnow()),
                    conclusion=mock.get('conclusion', {}).get('text', ''),
                    footer='',
                    status='IN_PROCESS',
                )
                db.session.add(post)
                db.session.flush()
            # PostDevelopment
            dev = PostDevelopment.query.filter_by(post_id=post.id).first()
            if not dev:
                dev = PostDevelopment(post_id=post.id, basic_idea=mock.get('summary', ''))
                db.session.add(dev)
            # Sections
            for i, section in enumerate(mock.get('sections', [])):
                sec = PostSection.query.filter_by(post_id=post.id, section_order=i).first()
                if not sec:
                    sec = PostSection(
                        post_id=post.id,
                        section_order=i,
                        section_heading=section.get('heading', ''),
                        first_draft=section.get('text', ''),
                    )
                    db.session.add(sec)
                    db.session.flush()
                # Image
                img_data = section.get('image')
                if img_data:
                    img = Image.query.filter_by(path=img_data['src']).first()
                    if not img:
                        img = Image(
                            filename=os.path.basename(img_data['src']),
                            path=img_data['src'],
                            alt_text=img_data.get('alt', ''),
                            caption=img_data.get('caption', ''),
                        )
                        db.session.add(img)
                        db.session.flush()
                    sec.image_id = img.id
            db.session.commit()
        print('Migration complete. All MOCK_POSTS migrated to development database.')

if __name__ == '__main__':
    migrate_mock_posts() 