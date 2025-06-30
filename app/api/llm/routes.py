from flask import jsonify, request
from app.api.llm import bp
from app.api.llm.schemas import ActionSchema, ActionRunSchema
from app.api.llm.models import Action, ActionRun
from app.api.llm.services import execute_action

@bp.route("/actions", methods=["GET"])
@bp.require_auth
@bp.version("v1")
@bp.document({
    "tags": ["LLM"],
    "summary": "List all LLM actions",
    "responses": {
        "200": {
            "description": "List of actions",
            "schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "actions": {
                                "type": "array",
                                "items": {"$ref": "#/definitions/Action"}
                            }
                        }
                    }
                }
            }
        }
    }
})
def list_actions():
    """List all available LLM actions."""
    actions = Action.query.all()
    return {
        "data": {
            "actions": ActionSchema(many=True).dump(actions)
        }
    }

@bp.route("/actions/<int:action_id>/execute", methods=["POST"])
@bp.require_auth
@bp.validate_request(ActionRunSchema)
@bp.version("v1")
@bp.document({
    "tags": ["LLM"],
    "summary": "Execute an LLM action",
    "parameters": [
        {
            "name": "action_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "ID of the action to execute"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "input_data": {
                        "type": "object",
                        "additionalProperties": True
                    }
                }
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Action execution result",
            "schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "action_run": {"$ref": "#/definitions/ActionRun"}
                        }
                    }
                }
            }
        }
    }
})
def execute_action_route(action_id: int, validated_data: dict):
    """Execute an LLM action with the provided input data."""
    action = Action.query.get_or_404(action_id)
    action_run = execute_action(action, validated_data["input_data"])
    return {
        "data": {
            "action_run": ActionRunSchema().dump(action_run)
        }
    }

@bp.route("/actions/<int:action_id>/runs/<int:run_id>", methods=["GET"])
@bp.require_auth
@bp.version("v1")
@bp.document({
    "tags": ["LLM"],
    "summary": "Get an action run",
    "parameters": [
        {
            "name": "action_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "ID of the action"
        },
        {
            "name": "run_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "ID of the action run"
        }
    ],
    "responses": {
        "200": {
            "description": "Action run details",
            "schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "action_run": {"$ref": "#/definitions/ActionRun"}
                        }
                    }
                }
            }
        }
    }
})
def get_action_run(action_id: int, run_id: int):
    """Get details of an action run."""
    action_run = ActionRun.query.filter_by(
        action_id=action_id,
        id=run_id
    ).first_or_404()
    return {
        "data": {
            "action_run": ActionRunSchema().dump(action_run)
        }
    } 