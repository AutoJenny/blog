from app import create_app, db
from app.models import LLMAction

app = create_app()

with app.app_context():
    total_actions = LLMAction.query.count()
    null_stage_names = LLMAction.query.filter_by(stage_name=None).count()
    
    print(f'Total LLMAction records: {total_actions}')
    print(f'Records with NULL stage_name: {null_stage_names}')
    
    if null_stage_names > 0:
        print('\nSample of records with NULL stage_name:')
        null_records = LLMAction.query.filter_by(stage_name=None).limit(5).all()
        for record in null_records:
            print(f'ID: {record.id}, Field Name: {record.field_name}, Source: {record.source_field}, Model: {record.llm_model}')
        
        # Fix the records
        print('\nFixing records...')
        for record in LLMAction.query.filter_by(stage_name=None).all():
            record.stage_name = 'Idea Stage'
        db.session.commit()
        print('Records fixed. New counts:')
        
        # Print updated counts
        total_actions = LLMAction.query.count()
        null_stage_names = LLMAction.query.filter_by(stage_name=None).count()
        print(f'Total LLMAction records: {total_actions}')
        print(f'Records with NULL stage_name: {null_stage_names}') 