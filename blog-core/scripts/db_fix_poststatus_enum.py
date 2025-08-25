import os
import psycopg2

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/blog")

SQL_COMMANDS = [
    "ALTER TABLE post ALTER COLUMN status TYPE VARCHAR;",
    "UPDATE post SET status = LOWER(status);",
    "DROP TYPE poststatus;",
    "CREATE TYPE poststatus AS ENUM ('draft', 'in_process', 'published', 'archived');",
    "ALTER TABLE post ALTER COLUMN status TYPE poststatus USING status::poststatus;"
]

def main():
    print(f"Connecting to DB: {DB_URL}")
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        for sql in SQL_COMMANDS:
            print(f"Executing: {sql}")
            cur.execute(sql)
        print("Enum fix complete.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main() 