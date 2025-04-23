from app import create_app, db
from app.models import Post, PostSection

app = create_app()

with app.app_context():
    post = Post.query.filter_by(slug="quaich-traditions").first()
    if post:
        print(f"\nPost details:")
        print(f"Title: {post.title}")
        print(f"Concept: {post.concept}")
        print(f"Description: {post.description}")
        print(f"\nSections ({len(post.sections)}):")
        for i, section in enumerate(post.sections):
            print(f"{i+1}. {section.title} (is_conclusion: {section.is_conclusion})")
            print(f"   Content preview: {section.content[:100]}...")
    else:
        print("Post not found!")
