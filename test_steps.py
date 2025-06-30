#!/usr/bin/env python3

import os
import sys
import psycopg2
import psycopg2.extras

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app

app = create_app()

with app.app_context():
    from app.db import get_db_conn
    
    with get_db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get all steps with their stage and substage
            cur.execute("""
                SELECT 
                    wse.id,
                    wse.name as step_name,
                    wse.config,
                    wsse.name as substage_name,
                    wst.name as stage_name
                FROM workflow_step_entity wse
                JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                WHERE wst.name ILIKE 'planning' AND wsse.name ILIKE 'idea'
                ORDER BY wse.step_order
            """)
            
            steps = cur.fetchall()
            print("Steps in planning/idea:")
            for step in steps:
                print(f"  ID: {step['id']}, Name: '{step['step_name']}', Config: {step['config'] is not None}")
                
            # Check for initial concept specifically
            cur.execute("""
                SELECT 
                    wse.id,
                    wse.name as step_name,
                    wse.config,
                    wsse.name as substage_name,
                    wst.name as stage_name
                FROM workflow_step_entity wse
                JOIN workflow_sub_stage_entity wsse ON wse.sub_stage_id = wsse.id
                JOIN workflow_stage_entity wst ON wsse.stage_id = wst.id
                WHERE wse.name ILIKE '%initial%concept%'
                OR wse.name ILIKE '%Initial%Concept%'
                OR wse.name ILIKE '%initial_concept%'
            """)
            
            initial_steps = cur.fetchall()
            print("\nInitial concept steps:")
            for step in initial_steps:
                print(f"  ID: {step['id']}, Name: '{step['step_name']}', Stage: {step['stage_name']}, Substage: {step['substage_name']}")
                if step['config']:
                    print(f"    Config: {step['config']}") 