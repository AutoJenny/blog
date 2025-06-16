from flask import Blueprint, jsonify, request
from ..models.action import ActionModel
from ..schemas.action import ActionSchema

action_bp = Blueprint('action', __name__)
action_schema = ActionSchema()

@action_bp.route('/substage/<int:substage_id>', methods=['GET'])
def get_actions(substage_id):
    """Get all actions for a substage"""
    model = ActionModel()
    actions = model.get_actions_by_substage(substage_id)
    return jsonify(action_schema.dump(actions, many=True))

@action_bp.route('/<int:action_id>', methods=['GET'])
def get_action(action_id):
    """Get a specific action"""
    model = ActionModel(action_id)
    action = model.get_action()
    if not action:
        return jsonify({'error': 'Action not found'}), 404
    return jsonify(action_schema.dump(action))

@action_bp.route('/', methods=['POST'])
def create_action():
    """Create a new action"""
    data = request.get_json()
    errors = action_schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    model = ActionModel()
    action_id = model.create_action(data)
    return jsonify({'id': action_id}), 201

@action_bp.route('/<int:action_id>', methods=['PUT'])
def update_action(action_id):
    """Update an action"""
    data = request.get_json()
    errors = action_schema.validate(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    model = ActionModel(action_id)
    if not model.get_action():
        return jsonify({'error': 'Action not found'}), 404
    
    if model.update_action(data):
        return jsonify({'message': 'Action updated successfully'})
    return jsonify({'error': 'Failed to update action'}), 500

@action_bp.route('/<int:action_id>', methods=['DELETE'])
def delete_action(action_id):
    """Delete an action"""
    model = ActionModel(action_id)
    if not model.get_action():
        return jsonify({'error': 'Action not found'}), 404
    
    if model.delete_action():
        return jsonify({'message': 'Action deleted successfully'})
    return jsonify({'error': 'Failed to delete action'}), 500 