from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)

def get_db_conn():
    return psycopg2.connect("dbname=blog user=nickfiddes host=localhost port=5432 password=your_password")

def get_posts():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM post ORDER BY updated_at DESC")
    posts = [{"id": row[0], "title": row[1]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return posts

def get_post(post_id):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM post WHERE id = %s", (post_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {"id": row[0], "title": row[1]}
    return None

def get_post_development(post_id):
    conn = get_db_conn()
    cur = conn.cursor()
    # Get all column names except id and post_id
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post_development' AND column_name NOT IN ('id', 'post_id') ORDER BY ordinal_position;")
    columns = [row[0] for row in cur.fetchall()]
    # Build dynamic SQL
    sql = f"SELECT {', '.join(columns)} FROM post_development WHERE post_id = %s"
    cur.execute(sql, (post_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return dict(zip(columns, row))
    return None

@app.route('/')
def llm_actions():
    post_id = request.args.get('post_id', default=22, type=int)
    post = get_post(post_id)
    if not post:
        post = get_post(22)  # fallback to post 22 if not found
    posts = get_posts()
    post_dev = get_post_development(post_id)
    return render_template('llm_actions.html', posts=posts, post=post, post_dev=post_dev)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 