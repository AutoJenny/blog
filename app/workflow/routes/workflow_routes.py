from flask import Blueprint, jsonify, request
from ..models.workflow import WorkflowModel
from ..schemas.workflow import WorkflowSchema

workflow_bp = Blueprint('workflow', __name__)
workflow_schema = WorkflowSchema()

@workflow_bp.route('/', methods=['GET'])
def get_workflows():
    """Get all workflows"""
    model = WorkflowModel()
    workflows = model.get_all_workflows()
    return jsonify(workflow_schema.dump(workflows, many=True))

@workflow_bp.route('/<int:workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """Get a specific workflow"""
    model = WorkflowModel(workflow_id)
    workflow = model.get_workflow()
    if not workflow:
        return jsonify({'error': 'Workflow not found'}), 404
    return jsonify(workflow_schema.dump(workflow))

@workflow_bp.route('/', methods=['POST'])
def create_workflow():
    """Create a new workflow"""
    data = request.get_json()
    errors = workflow_schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    model = WorkflowModel()
    workflow_id = model.create_workflow(data)
    return jsonify({'id': workflow_id}), 201

@workflow_bp.route('/<int:workflow_id>', methods=['PUT'])
def update_workflow(workflow_id):
    """Update a workflow"""
    data = request.get_json()
    errors = workflow_schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    model = WorkflowModel(workflow_id)
    if not model.get_workflow():
        return jsonify({'error': 'Workflow not found'}), 404
    
    if model.update_workflow(data):
        return jsonify({'message': 'Workflow updated successfully'})
    return jsonify({'error': 'Failed to update workflow'}), 500

@workflow_bp.route('/<int:workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id):
    """Delete a workflow"""
    model = WorkflowModel(workflow_id)
    if not model.get_workflow():
        return jsonify({'error': 'Workflow not found'}), 404
    
    if model.delete_workflow():
        return jsonify({'message': 'Workflow deleted successfully'})
    return jsonify({'error': 'Failed to delete workflow'}), 500 