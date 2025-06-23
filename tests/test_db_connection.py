"""Tests for database connection functionality."""
import os
import pytest
from psycopg2.extras import RealDictCursor
from app.database.routes import get_db_conn

def test_get_db_conn_returns_connection():
    """Test that get_db_conn returns a valid database connection."""
    conn = get_db_conn()
    assert conn is not None
    conn.close()

def test_get_db_conn_uses_real_dict_cursor():
    """Test that get_db_conn uses RealDictCursor."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            assert isinstance(cur, RealDictCursor)

def test_get_db_conn_can_execute_query():
    """Test that get_db_conn can execute a simple query."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 as test")
            result = cur.fetchone()
            assert result['test'] == 1

def test_get_db_conn_handles_missing_env_file(monkeypatch):
    """Test that get_db_conn handles missing environment file gracefully."""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://nickfiddes@localhost/blog')
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 as test")
            result = cur.fetchone()
            assert result['test'] == 1

def test_get_db_conn_uses_context_manager():
    """Test that get_db_conn works with context manager."""
    with get_db_conn() as conn:
        assert not conn.closed
    assert conn.closed

def test_get_db_conn_handles_transaction():
    """Test that get_db_conn properly handles transactions."""
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            # Create a temporary table
            cur.execute("""
                CREATE TEMPORARY TABLE test_table (
                    id serial PRIMARY KEY,
                    value text
                )
            """)
            # Insert some data
            cur.execute("INSERT INTO test_table (value) VALUES ('test')")
            # Verify the data
            cur.execute("SELECT value FROM test_table")
            result = cur.fetchone()
            assert result['value'] == 'test'
    # Connection and transaction should be closed
    assert conn.closed 