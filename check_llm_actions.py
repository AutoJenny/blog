from app import create_app, db

app = create_app()

with app.app_context():
    total_actions = db.session.execute("SELECT COUNT(*) FROM llm_actions").fetchone()[0]
    null_stage_names = db.session.execute("SELECT COUNT(*) FROM llm_actions WHERE stage_name IS NULL").fetchone()[0]
    
    print(f'Total LLMAction records: {total_actions}')
    print(f'Records with NULL stage_name: {null_stage_names}')
    
    if null_stage_names > 0:
        print('\nSample of records with NULL stage_name:')
        null_records = db.session.execute("SELECT id, field_name, source_field, llm_model FROM llm_actions WHERE stage_name IS NULL LIMIT 5").fetchall()
        for record in null_records:
            print(f'ID: {record[0]}, Field Name: {record[1]}, Source: {record[2]}, Model: {record[3]}')
        
        # Fix the records
        print('\nFixing records...')
        db.session.execute("UPDATE llm_actions SET stage_name = 'Idea Stage'")
        db.session.commit()
        print('Records fixed. New counts:')
        
        # Print updated counts
        total_actions = db.session.execute("SELECT COUNT(*) FROM llm_actions").fetchone()[0]
        null_stage_names = db.session.execute("SELECT COUNT(*) FROM llm_actions WHERE stage_name IS NULL").fetchone()[0]
        print(f'Total LLMAction records: {total_actions}')
        print(f'Records with NULL stage_name: {null_stage_names}') 