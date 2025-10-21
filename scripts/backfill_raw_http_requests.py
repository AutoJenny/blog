#!/usr/bin/env python3
"""
Backfill raw_http_request field for existing llm_message_intercepts records
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_manager
import json

def backfill_raw_http_requests():
    """Backfill raw_http_request field for existing records that have raw_messages"""
    
    with db_manager.get_cursor() as cursor:
        # Get all records that have raw_messages but no raw_http_request
        cursor.execute("""
            SELECT id, post_id, section_id, raw_messages, intercepted_message
            FROM llm_message_intercepts 
            WHERE raw_messages IS NOT NULL 
            AND raw_http_request IS NULL
            ORDER BY created_at DESC
        """)
        
        records = cursor.fetchall()
        print(f"Found {len(records)} records to backfill")
        
        for record in records:
            try:
                raw_messages = record['raw_messages']
                intercepted_message = record['intercepted_message']
                
                # Extract provider and model from intercepted_message
                provider = 'ollama'  # Default based on the logs
                model = 'llama3.2:latest'  # Default based on the logs
                
                if 'PROVIDER:' in intercepted_message:
                    provider_line = [line for line in intercepted_message.split('\n') if 'PROVIDER:' in line][0]
                    provider = provider_line.split('PROVIDER:')[1].strip().lower()
                
                if 'MODEL:' in intercepted_message:
                    model_line = [line for line in intercepted_message.split('\n') if 'MODEL:' in line][0]
                    model = model_line.split('MODEL:')[1].strip()
                
                # Build the raw HTTP request
                if provider == 'ollama':
                    url = "http://localhost:11434/api/chat"
                    headers = {"Content-Type": "application/json"}
                    data = {
                        "model": model,
                        "messages": raw_messages,
                        "stream": False,
                        "options": {
                            "num_predict": 4000
                        }
                    }
                else:  # openai
                    url = "https://api.openai.com/v1/chat/completions"
                    headers = {
                        "Authorization": "Bearer [API_KEY]",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": model,
                        "messages": raw_messages,
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                
                # Build the exact raw HTTP request
                raw_request = f"POST {url} HTTP/1.1\n"
                for header_name, header_value in headers.items():
                    raw_request += f"{header_name}: {header_value}\n"
                raw_request += "\n"
                raw_request += json.dumps(data, indent=2)
                
                # Update the record
                cursor.execute("""
                    UPDATE llm_message_intercepts
                    SET raw_http_request = %s
                    WHERE id = %s
                """, (raw_request, record['id']))
                
                print(f"Updated record {record['id']} (post {record['post_id']}, section {record['section_id']})")
                
            except Exception as e:
                print(f"Error processing record {record['id']}: {e}")
                continue
        
        cursor.connection.commit()
        print(f"Backfill completed for {len(records)} records")

if __name__ == "__main__":
    backfill_raw_http_requests()
