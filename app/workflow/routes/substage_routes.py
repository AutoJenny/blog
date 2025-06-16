from flask import Blueprint, jsonify, request
from ..models.substage import SubstageModel
from ..schemas.substage import SubstageSchema

substage_bp = Blueprint('substage', __name__)
substage_schema = SubstageSchema()

@substage_bp.route('/stage/<int:stage_id>', methods=['GET'])
def get_substages(stage_id):
    """Get all substages for a stage"""
    model = SubstageModel()
    substages = model.get_substages_by_stage(stage_id)
    return jsonify(substage_schema.dump(substages, many=True))

@substage_bp.route('/<int:substage_id>', methods=['GET'])
def get_substage(substage_id):
    """Get a specific substage"""
    model = SubstageModel(substage_id)
    substage = model.get_substage()
    if not substage:
        return jsonify({'error': 'Substage not found'}), 404
    return jsonify(substage_schema.dump(substage))

@substage_bp.route('/', methods=['POST'])
def create_substage():
    """Create a new substage"""
    data = request.get_json()
    errors = substage_schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    model = SubstageModel()
    substage_id = model.create_substage(data)
    return jsonify({'id': substage_id}), 201

@substage_bp.route('/<int:substage_id>', methods=['PUT'])
def update_substage(substage_id):
    """Update a substage"""
    data = request.get_json()
    errors = substage_schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    model = SubstageModel(substage_id)
    if not model.get_substage():
        return jsonify({'error': 'Substage not found'}), 404
    
    if model.update_substage(data):
        return jsonify({'message': 'Substage updated successfully'})
    return jsonify({'error': 'Failed to update substage'}), 500

@substage_bp.route('/<int:substage_id>', methods=['DELETE'])
def delete_substage(substage_id):
    """Delete a substage"""
    model = SubstageModel(substage_id)
    if not model.get_substage():
        return jsonify({'error': 'Substage not found'}), 404
    
    if model.delete_substage():
        return jsonify({'message': 'Substage deleted successfully'})
    return jsonify({'error': 'Failed to delete substage'}), 500 