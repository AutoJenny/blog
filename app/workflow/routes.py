from flask import jsonify, request

from app import db
from app.models import Post
from app.workflow.manager import (
    WorkflowManager,
    WorkflowError,
    InvalidTransitionError,
    ValidationError,
)
from app.workflow.constants import WORKFLOW_STAGES, SubStageStatus
from app.workflow import bp


@bp.route("/<slug>/status")
def get_workflow_status(slug):
    """Get the current workflow status and available transitions"""
    post = Post.query.filter_by(slug=slug).first_or_404()
    manager = WorkflowManager(post)

    current_stage = manager.get_current_stage()
    stage_data = post.workflow_status.stage_data.get(current_stage, {})
    available_transitions = manager.get_available_transitions()
    completed, total = manager.get_stage_progress(current_stage)

    return jsonify(
        {
            "current_stage": current_stage,
            "stage_description": WORKFLOW_STAGES[current_stage]["description"],
            "stage_data": stage_data,
            "progress": {
                "completed": completed,
                "total": total,
                "percentage": (completed / total * 100) if total > 0 else 0,
            },
            "available_transitions": available_transitions,
        }
    )


@bp.route("/<slug>/transition", methods=["POST"])
def transition_stage(slug):
    """Transition to a new workflow stage"""
    data = request.get_json()
    if not data or "target_stage" not in data:
        return jsonify({"error": "target_stage is required"}), 400

    post = Post.query.filter_by(slug=slug).first_or_404()
    manager = WorkflowManager(post)

    try:
        manager.transition_to(
            data["target_stage"], data.get("user_id"), data.get("notes", "")
        )
        return jsonify({"message": "Workflow updated successfully"})
    except (InvalidTransitionError, ValidationError) as e:
        return jsonify({"error": str(e)}), 400
    except WorkflowError as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<slug>/sub-stage", methods=["POST"])
def update_sub_stage(slug):
    """Update a sub-stage status, content, or add a note"""
    data = request.get_json()
    if not data or "sub_stage" not in data:
        return jsonify({"error": "sub_stage is required"}), 400

    # Get optional parameters
    status = SubStageStatus(data["status"]) if "status" in data else None
    note = data.get("note")
    content = data.get("content")

    # Validate that at least one update parameter is provided
    if status is None and note is None and content is None:
        return (
            jsonify(
                {"error": "At least one of status, note, or content must be provided"}
            ),
            400,
        )

    post = Post.query.filter_by(slug=slug).first_or_404()
    manager = WorkflowManager(post)

    try:
        manager.update_sub_stage(
            data["sub_stage"], status=status, note=note, content=content
        )
        return jsonify({"message": "Sub-stage updated successfully"})
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except WorkflowError as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<slug>/history")
def get_history(slug):
    """Get the workflow history for a post"""
    post = Post.query.filter_by(slug=slug).first_or_404()

    history = []
    for entry in post.workflow_status.history:
        history.append(
            {
                "from_stage": entry.from_stage,
                "to_stage": entry.to_stage,
                "notes": entry.notes,
                "user_id": entry.user_id,
                "created_at": entry.created_at.isoformat(),
            }
        )

    return jsonify({"history": history})
