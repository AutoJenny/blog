from flask import Blueprint, jsonify, request
from ..models.stage import StageModel
from ..schemas.stage import StageSchema

stage_bp = Blueprint('stage', __name__)
stage_schema = StageSchema()

@stage_bp.route('/workflow/<int:workflow_id>', methods=['GET'])
def get_stages(workflow_id):
    """Get all stages for a workflow"""
    model = StageModel()
    stages = model.get_stages_by_workflow(workflow_id)
    return jsonify(stage_schema.dump(stages, many=True))

@stage_bp.route('/<int:stage_id>', methods=['GET'])
def get_stage(stage_id):
    """Get a specific stage"""
    model = StageModel(stage_id)
    stage = model.get_stage()
    if not stage:
        return jsonify({'error': 'Stage not found'}), 404
    return jsonify(stage_schema.dump(stage))

@stage_bp.route('/', methods=['POST'])
def create_stage():
    """Create a new stage"""
    data = request.get_json()
    errors = stage_schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    model = StageModel()
    stage_id = model.create_stage(data)
    return jsonify({'id': stage_id}), 201

@stage_bp.route('/<int:stage_id>', methods=['PUT'])
def update_stage(stage_id):
    """Update a stage"""
    data = request.get_json()
    errors = stage_schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    model = StageModel(stage_id)
    if not model.get_stage():
        return jsonify({'error': 'Stage not found'}), 404
    
    if model.update_stage(data):
        return jsonify({'message': 'Stage updated successfully'})
    return jsonify({'error': 'Failed to update stage'}), 500

@stage_bp.route('/<int:stage_id>', methods=['DELETE'])
def delete_stage(stage_id):
    """Delete a stage"""
    model = StageModel(stage_id)
    if not model.get_stage():
        return jsonify({'error': 'Stage not found'}), 404
    
    if model.delete_stage():
        return jsonify({'message': 'Stage deleted successfully'})
    return jsonify({'error': 'Failed to delete stage'}), 500 