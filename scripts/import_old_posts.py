import os
import sys
import frontmatter
from datetime import datetime
from slugify import slugify

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


def import_posts(posts_dir):
    """Import posts from the old blog format."""
    app = create_app()
    with app.app_context():
        # Ensure we have a default user
        user = User.query.filter_by(username="nick-fiddes").first()
        if not user:
            user = User(username="nick-fiddes", email="nick@clan.com", is_admin=True)
            user.set_password("changeme")
            db.session.add(user)
            db.session.commit()

        # Process each markdown file
        for filename in os.listdir(posts_dir):
            if not filename.endswith(".md"):
                continue

            print(f"Processing {filename}...")
            with open(os.path.join(posts_dir, filename), "r") as f:
                post_data = frontmatter.load(f)

            # Create or get categories and tags
            categories = []
            if "categories" in post_data:
                for cat_name in post_data["categories"]:
                    cat = Category.query.filter_by(name=cat_name).first()
                    if not cat:
                        cat = Category(name=cat_name, slug=slugify(cat_name))
                        db.session.add(cat)
                    categories.append(cat)

            tags = []
            if "tags" in post_data:
                for tag_name in post_data["tags"]:
                    if tag_name == "post":  # Skip the 'post' tag
                        continue
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name, slug=slugify(tag_name))
                        db.session.add(tag)
                    tags.append(tag)

            # Create or update the post
            post = Post.query.filter_by(slug=slugify(post_data["title"])).first()
            if not post:
                post = Post(
                    title=post_data["title"],
                    slug=slugify(post_data["title"]),
                    content=post_data.content,
                    summary=post_data.get("summary", ""),
                    concept=post_data.get("concept", ""),
                    author_id=user.id,
                    published=True,
                    created_at=datetime.strptime(post_data["date"], "%Y-%m-%d"),
                    published_at=datetime.strptime(post_data["date"], "%Y-%m-%d"),
                )
                db.session.add(post)
                db.session.flush()  # Get the post ID

            # Clear existing relationships
            post.categories = []
            post.tags = []

            # Delete existing sections
            PostSection.query.filter_by(post_id=post.id).delete()

            # Add categories and tags
            post.categories = categories
            post.tags = tags

            # Create sections
            if "sections" in post_data:
                for idx, section_data in enumerate(post_data["sections"], 1):
                    section = PostSection(
                        post_id=post.id,
                        title=section_data.get("heading", ""),
                        content=section_data.get("text", ""),
                        position=idx,
                        content_type="text",
                    )
                    if "imageId" in section_data:
                        # TODO: Handle image import
                        pass
                    db.session.add(section)

            # Set workflow status
            if not post.workflow_status:
                workflow = WorkflowStatus(
                    post=post, current_stage=WorkflowStage.PUBLISHING
                )
                db.session.add(workflow)

            try:
                db.session.commit()
                print(f"Imported {post.title}")
            except Exception as e:
                print(f"Error importing {filename}: {str(e)}")
                db.session.rollback()


if __name__ == "__main__":
    posts_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "__blog_old",
        "posts",
    )
    import_posts(posts_dir)
