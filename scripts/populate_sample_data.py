import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load DATABASE_URL from assistant_config.env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assistant_config.env'))
DATABASE_URL = os.getenv('DATABASE_URL')

def main():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    try:
        # Categories
        categories = [
            ('News', 'news', 'News category'),
            ('Tech', 'tech', 'Technology category'),
            ('Opinion', 'opinion', 'Opinion pieces'),
        ]
        for name, slug, desc in categories:
            cur.execute("INSERT INTO category (name, slug, description) VALUES (%s, %s, %s) ON CONFLICT (slug) DO NOTHING;", (name, slug, desc))
        # Tags
        tags = [
            ('General', 'general', 'General tag'),
            ('AI', 'ai', 'Artificial Intelligence'),
            ('Python', 'python', 'Python programming'),
        ]
        for name, slug, desc in tags:
            cur.execute("INSERT INTO tag (name, slug, description) VALUES (%s, %s, %s) ON CONFLICT (slug) DO NOTHING;", (name, slug, desc))
        # Posts
        posts = [
            ('Sample Post', 'sample-post', 'This is a sample post.', 'Sample summary', True, 'published'),
            ('Tech Trends', 'tech-trends', 'Latest in tech.', 'Tech summary', True, 'published'),
            ('Opinion Piece', 'opinion-piece', 'My opinion.', 'Opinion summary', False, 'draft'),
        ]
        post_ids = []
        for title, slug, content, summary, published, status in posts:
            cur.execute("""
                INSERT INTO post (title, slug, content, summary, published, deleted, created_at, updated_at, status)
                VALUES (%s, %s, %s, %s, %s, FALSE, NOW(), NOW(), %s)
                ON CONFLICT (slug) DO UPDATE SET title=EXCLUDED.title RETURNING id;
            """, (title, slug, content, summary, published, status))
            post = cur.fetchone()
            if not post:
                cur.execute("SELECT id FROM post WHERE slug=%s", (slug,))
                post = cur.fetchone()
            post_ids.append(post['id'])
        # PostDevelopment
        devs = [
            ('Sample idea', 'Sample Title'),
            ('Tech idea', 'Tech Title'),
            ('Opinion idea', 'Opinion Title'),
        ]
        for post_id, (basic_idea, provisional_title) in zip(post_ids, devs):
            cur.execute("""
                INSERT INTO post_development (post_id, basic_idea, provisional_title)
                VALUES (%s, %s, %s)
                ON CONFLICT (post_id) DO NOTHING;
            """, (post_id, basic_idea, provisional_title))
        # PostSection
        for post_id in post_ids:
            for i in range(1, 4):
                cur.execute("""
                    INSERT INTO post_section (post_id, section_order, section_heading)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (post_id, i, f'Section {i} for post {post_id}'))
        conn.commit()
        print("Sample data (3 rows per table) inserted successfully.")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main() 