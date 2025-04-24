#!/usr/bin/env python3
import os
import sys
import re
from pathlib import Path
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from db_backup import validate_sqlite_db


def get_sqlite_tables(sqlite_conn):
    """Get all tables and their creation SQL from SQLite"""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    return cursor.fetchall()


def sqlite_to_postgres_type(sqlite_type):
    """Convert SQLite type to PostgreSQL type"""
    type_map = {
        "INTEGER": "INTEGER",
        "REAL": "DOUBLE PRECISION",
        "TEXT": "TEXT",
        "BLOB": "BYTEA",
        "BOOLEAN": "BOOLEAN",
        "DATETIME": "TIMESTAMP",
        "VARCHAR": "VARCHAR",
        "JSON": "JSONB",
    }

    for sqlite_t, pg_t in type_map.items():
        if sqlite_type.upper().startswith(sqlite_t):
            return pg_t
    return "TEXT"  # Default to TEXT for unknown types


def is_reserved_word(word):
    """Check if a word is a PostgreSQL reserved word"""
    reserved_words = {
        "user",
        "group",
        "order",
        "table",
        "index",
        "column",
        "constraint",
        "limit",
        "offset",
        "select",
        "where",
        "check",
        "default",
        "primary",
        "key",
        "references",
    }
    return word.lower() in reserved_words


def quote_identifier(identifier):
    """Quote an identifier if needed"""
    if is_reserved_word(identifier) or not identifier.isalnum():
        return f'"{identifier}"'
    return identifier


def convert_create_table_sql(sqlite_sql):
    """Convert SQLite CREATE TABLE statement to PostgreSQL"""
    # Remove SQLite-specific AUTOINCREMENT
    sql = sqlite_sql.replace("AUTOINCREMENT", "GENERATED ALWAYS AS IDENTITY")

    # Convert data types
    for sqlite_type in [
        "INTEGER",
        "REAL",
        "TEXT",
        "BLOB",
        "BOOLEAN",
        "DATETIME",
        "VARCHAR",
        "JSON",
    ]:
        sql = sql.replace(sqlite_type, sqlite_to_postgres_type(sqlite_type))

    # Extract table name and columns
    match = re.match(r"CREATE TABLE (\w+)\s*\((.*)\)", sql.replace("\n", " "))
    if not match:
        raise ValueError(f"Could not parse CREATE TABLE statement: {sql}")

    table_name, columns_str = match.groups()
    table_name = quote_identifier(table_name)

    # Split columns and constraints
    parts = []
    current_part = []
    parentheses_level = 0

    for char in columns_str:
        if char == "(" and len(current_part) > 0:
            parentheses_level += 1
        elif char == ")" and parentheses_level > 0:
            parentheses_level -= 1
        elif char == "," and parentheses_level == 0:
            parts.append("".join(current_part).strip())
            current_part = []
            continue

        current_part.append(char)

    if current_part:
        parts.append("".join(current_part).strip())

    # Process each column/constraint
    processed_parts = []
    for part in parts:
        # Handle column definitions
        if (
            "CONSTRAINT" not in part.upper()
            and "FOREIGN KEY" not in part.upper()
            and "PRIMARY KEY" not in part.upper()
        ):
            words = part.split()
            if words:
                col_name = words[0].strip(',"')
                processed_parts.append(
                    part.replace(col_name, quote_identifier(col_name), 1)
                )
        else:
            # Handle constraints
            constraint_match = re.match(r"CONSTRAINT (\w+)", part)
            if constraint_match:
                constraint_name = constraint_match.group(1)
                processed_parts.append(
                    part.replace(
                        f"CONSTRAINT {constraint_name}",
                        f"CONSTRAINT {quote_identifier(constraint_name)}",
                    )
                )
            else:
                # Handle REFERENCES in foreign keys
                ref_match = re.search(r"REFERENCES (\w+)", part)
                if ref_match:
                    ref_table = ref_match.group(1)
                    processed_parts.append(
                        part.replace(
                            f"REFERENCES {ref_table}",
                            f"REFERENCES {quote_identifier(ref_table)}",
                        )
                    )
                else:
                    processed_parts.append(part)

    # Reconstruct the CREATE TABLE statement
    return (
        f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(processed_parts) + "\n)"
    )


def get_table_columns(sqlite_conn, table_name):
    """Get column names for a table"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [col[1] for col in cursor.fetchall()]


def migrate_table_data(sqlite_conn, pg_conn, table_name):
    """Migrate data from SQLite table to PostgreSQL"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Get column names and quote them if necessary
    columns = get_table_columns(sqlite_conn, table_name)
    quoted_columns = [quote_identifier(col) for col in columns]
    columns_str = ", ".join(quoted_columns)
    placeholders = ", ".join(["%s"] * len(columns))

    # Fetch all data from SQLite
    sqlite_cursor.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
    rows = sqlite_cursor.fetchall()

    if rows:
        # Insert data into PostgreSQL
        insert_sql = f"INSERT INTO {quote_identifier(table_name)} ({columns_str}) VALUES ({placeholders})"
        pg_cursor.executemany(insert_sql, rows)
        pg_conn.commit()

    return len(rows)


def main():
    # Validate source database
    project_root = Path(__file__).parent.parent
    sqlite_path = project_root / "instance" / "blog.db"

    if not validate_sqlite_db(sqlite_path):
        print("Error: Source database failed integrity check")
        sys.exit(1)

    try:
        # Connect to both databases
        sqlite_conn = sqlite3.connect(sqlite_path)

        # Create PostgreSQL database
        pg_conn = psycopg2.connect(
            dbname="postgres", user="postgres", password="postgres", host="localhost"
        )
        pg_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        pg_cursor = pg_conn.cursor()

        # Create blog database
        pg_cursor.execute("DROP DATABASE IF EXISTS blog")
        pg_cursor.execute("CREATE DATABASE blog")
        pg_conn.close()

        # Connect to new database
        pg_conn = psycopg2.connect(
            dbname="blog", user="postgres", password="postgres", host="localhost"
        )
        pg_cursor = pg_conn.cursor()

        # Get all tables from SQLite
        tables = get_sqlite_tables(sqlite_conn)

        # Create tables in PostgreSQL
        for table_name, create_sql in tables:
            if table_name != "sqlite_sequence":  # Skip SQLite internal tables
                print(f"\nMigrating table: {table_name}")
                pg_sql = convert_create_table_sql(create_sql)
                print(f"Executing SQL:\n{pg_sql}")  # Debug output
                pg_cursor.execute(pg_sql)

                # Migrate data
                rows_migrated = migrate_table_data(sqlite_conn, pg_conn, table_name)
                print(f"  - {rows_migrated} rows migrated")

        pg_conn.commit()
        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)
    finally:
        if "sqlite_conn" in locals():
            sqlite_conn.close()
        if "pg_conn" in locals():
            pg_conn.close()


if __name__ == "__main__":
    main()
