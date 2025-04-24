from app import create_app
from app.models import Post
from flask import current_app

app = create_app()
with app.app_context():
    posts = Post.query.all()
    print(f"\nTotal posts in database: {len(posts)}")
    print("\nPost details:")
    for post in posts:
        print(f"\nID: {post.id}")
        print(f"Title: {post.title}")
        print(f"Slug: {post.slug}")
        print(f"Published: {post.published}")
        print(f"Deleted: {post.deleted}")
        print("-" * 50)
