from flask import jsonify, request
from app.api.llm import bp
from app.api.llm.schemas import ActionSchema, ActionRunSchema
from app.api.llm.models import Action, ActionRun
from app.api.llm.services import execute_action
from app.database import get_db_conn

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

@bp.route('/post_workflow_step_actions/<int:pws_id>', methods=['PUT', 'DELETE'])
def post_workflow_step_action_detail(pws_id):
    if request.method == 'PUT':
        data = request.get_json() or {}
        button_label = data.get('button_label')
        button_order = data.get('button_order')
        input_field = data.get('input_field')
        output_field = data.get('output_field')
        # Upsert logic: check if record exists
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM post_workflow_step_action WHERE id = %s", (pws_id,))
                exists = cur.fetchone()
                if exists:
                    cur.execute("""
                        UPDATE post_workflow_step_action
                        SET button_label = %s, button_order = %s, input_field = %s, output_field = %s
                        WHERE id = %s
                    """, (button_label, button_order, input_field, output_field, pws_id))
                    conn.commit()
                    return jsonify({'status': 'success', 'action': 'updated'})
                else:
                    # Need post_id and step_id to create
                    post_id = data.get('post_id')
                    step_id = data.get('step_id')
                    action_id = data.get('action_id')
                    if not post_id or not step_id or not action_id:
                        return jsonify({'error': 'Missing post_id, step_id, or action_id for upsert'}), 400
                    cur.execute("""
                        INSERT INTO post_workflow_step_action (id, post_id, step_id, action_id, input_field, output_field, button_label, button_order)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (pws_id, post_id, step_id, action_id, input_field, output_field, button_label, button_order))
                    conn.commit()
                    return jsonify({'status': 'success', 'action': 'created'})
    if request.method == 'DELETE':
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM post_workflow_step_action WHERE id = %s", (pws_id,))
                conn.commit()
        return jsonify({'status': 'success'})

# --- Post Workflow Step Action Endpoints ---
@bp.route('/post_workflow_step_actions', methods=['GET', 'POST'])
def post_workflow_step_actions():
    if request.method == 'GET':
        post_id = request.args.get('post_id', type=int)
        step_id = request.args.get('step_id', type=int)
        if not post_id or not step_id:
            return jsonify({'error': 'post_id and step_id required'}), 400
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, post_id, step_id, action_id, input_field, output_field, button_label, button_order
                    FROM post_workflow_step_action
                    WHERE post_id = %s AND step_id = %s
                    ORDER BY button_order, id
                """, (post_id, step_id))
                rows = cur.fetchall()
                actions = []
                for row in rows:
                    if isinstance(row, dict):
                        actions.append(row)
                    else:
                        actions.append({
                            'id': row[0],
                            'post_id': row[1],
                            'step_id': row[2],
                            'action_id': row[3],
                            'input_field': row[4],
                            'output_field': row[5],
                            'button_label': row[6],
                            'button_order': row[7],
                        })
        return jsonify({'actions': actions})

    if request.method == 'POST':
        data = request.get_json() or {}
        post_id = data.get('post_id')
        step_id = data.get('step_id')
        action_id = data.get('action_id')
        input_field = data.get('input_field')
        output_field = data.get('output_field') if 'output_field' in data else None
        button_label = data.get('button_label')
        button_order = data.get('button_order', 0)
        missing = []
        if not post_id:
            missing.append('post_id')
        if not step_id:
            missing.append('step_id')
        if not action_id:
            missing.append('action_id')
        if missing:
            return jsonify({'error': 'post_id, step_id, and action_id required', 'missing': missing, 'data': data}), 400
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO post_workflow_step_action (post_id, step_id, action_id, input_field, output_field, button_label, button_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (post_id, step_id, action_id, input_field, output_field, button_label, button_order))
                new_id = cur.fetchone()[0]
                conn.commit()
        return jsonify({'status': 'success', 'id': new_id}) 