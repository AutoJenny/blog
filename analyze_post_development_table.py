#!/usr/bin/env python3
"""
Script to analyze the post_development table and identify which fields have content and which are empty.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import dotenv_values

def get_db_conn():
    """Get a database connection."""
    try:
        # Load DATABASE_URL from assistant_config.env
        config_path = os.path.join(os.path.dirname(__file__), 'blog-core/assistant_config.env')
        config = dotenv_values(config_path)
        
        # Parse DATABASE_URL if present
        database_url = config.get('DATABASE_URL')
        if database_url:
            # Parse the DATABASE_URL
            import re
            match = re.match(r"postgres(?:ql)?://([^:]+)(?::([^@]+))?@([^:/]+)(?::(\d+))?/([^\s]+)", database_url)
            if match:
                user = match.group(1)
                password = match.group(2)
                host = match.group(3)
                port = match.group(4) or '5432'
                dbname = match.group(5)
                
                conn = psycopg2.connect(
                    dbname=dbname,
                    user=user,
                    password=password,
                    host=host,
                    port=port,
                    cursor_factory=RealDictCursor
                )
                return conn
        
        # If DATABASE_URL not found, raise an error
        raise Exception("DATABASE_URL not found in assistant_config.env")
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise

def analyze_post_development_table():
    """Analyze the post_development table to find fields with content and empty fields."""
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # First, get the table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'post_development' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"Found {len(columns)} columns in post_development table:")
        for col in columns:
            print(f"  - {col['column_name']} ({col['data_type']})")
        
        print("\n" + "="*80)
        
        # Get total number of rows
        cursor.execute("SELECT COUNT(*) as total_rows FROM post_development")
        total_rows = cursor.fetchone()['total_rows']
        print(f"Total rows in post_development table: {total_rows}")
        
        if total_rows == 0:
            print("Table is empty!")
            return
        
        # Analyze each column for content
        fields_with_content = []
        empty_fields = []
        
        for col in columns:
            column_name = col['column_name']
            
            # Count non-null and non-empty values
            if col['data_type'] in ['text', 'character varying', 'character']:
                # For text fields, check for non-null and non-empty strings
                cursor.execute(f"""
                    SELECT COUNT(*) as non_empty_count 
                    FROM post_development 
                    WHERE {column_name} IS NOT NULL 
                    AND {column_name} != '' 
                    AND {column_name} != ' '
                """)
            else:
                # For other data types, just check for non-null
                cursor.execute(f"""
                    SELECT COUNT(*) as non_empty_count 
                    FROM post_development 
                    WHERE {column_name} IS NOT NULL
                """)
            
            non_empty_count = cursor.fetchone()['non_empty_count']
            
            if non_empty_count > 0:
                fields_with_content.append({
                    'column': column_name,
                    'data_type': col['data_type'],
                    'non_empty_count': non_empty_count,
                    'percentage': round((non_empty_count / total_rows) * 100, 2)
                })
            else:
                empty_fields.append({
                    'column': column_name,
                    'data_type': col['data_type']
                })
        
        # Print results
        print(f"\n{'='*80}")
        print("FIELDS WITH CONTENT:")
        print(f"{'='*80}")
        if fields_with_content:
            for field in fields_with_content:
                print(f"✓ {field['column']} ({field['data_type']}) - {field['non_empty_count']} rows ({field['percentage']}%)")
        else:
            print("No fields with content found!")
        
        print(f"\n{'='*80}")
        print("EMPTY FIELDS:")
        print(f"{'='*80}")
        if empty_fields:
            for field in empty_fields:
                print(f"✗ {field['column']} ({field['data_type']})")
        else:
            print("No empty fields found!")
        
        print(f"\n{'='*80}")
        print("SUMMARY:")
        print(f"{'='*80}")
        print(f"Total columns: {len(columns)}")
        print(f"Fields with content: {len(fields_with_content)}")
        print(f"Empty fields: {len(empty_fields)}")
        print(f"Percentage of fields with content: {round((len(fields_with_content) / len(columns)) * 100, 2)}%")
        
    except Exception as e:
        print(f"Error analyzing table: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    analyze_post_development_table() 