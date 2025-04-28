#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# Add the application root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import (
    Post,
    WorkflowStatus,
    WorkflowStage,
    WorkflowStageEntity,
    WorkflowSubStageEntity,
)
from app.workflow.constants import WORKFLOW_STAGES, SubStageStatus


def update_workflow_status(slug):
    """Update workflow status data for a post to match the expected structure."""
    app = create_app()
    with app.app_context():
        # Get the post
        post = Post.query.filter_by(slug=slug).first()
        if not post:
            print(f"Post with slug '{slug}' not found")
            return

        # Get or create workflow status
        workflow_status = post.workflow_status
        if not workflow_status:
            workflow_status = WorkflowStatus()
            workflow_status.post = post
            db.session.add(workflow_status)

        # Initialize current stage if not set
        if not workflow_status.current_stage:
            workflow_status.current_stage = WorkflowStage.IDEA

        # Initialize stage data with proper structure
        if not workflow_status.stage_data:
            workflow_status.stage_data = {}

        # Ensure each stage has proper structure
        for stage, stage_config in WORKFLOW_STAGES.items():
            if stage not in workflow_status.stage_data:
                workflow_status.stage_data[stage] = {
                    "started_at": None,
                    "sub_stages": {},
                }

            # Initialize sub-stages
            for sub_stage, sub_stage_config in stage_config["sub_stages"].items():
                if sub_stage not in workflow_status.stage_data[stage]["sub_stages"]:
                    workflow_status.stage_data[stage]["sub_stages"][sub_stage] = {
                        "status": SubStageStatus.NOT_STARTED,
                        "started_at": None,
                        "completed_at": None,
                        "notes": [],
                        "content": "",
                    }

        # Set started_at for current stage if not set
        current_stage = workflow_status.current_stage
        if not workflow_status.stage_data[current_stage]["started_at"]:
            workflow_status.stage_data[current_stage][
                "started_at"
            ] = datetime.utcnow().isoformat()

        # Update last_updated timestamp
        workflow_status.last_updated = datetime.utcnow()

        try:
            db.session.commit()
            print(f"Successfully updated workflow status for post '{post.title}'")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating workflow status: {str(e)}")


# Example workflow stages and sub-stages
STAGES = [
    {
        "name": "idea",
        "description": "Initial idea stage",
        "order": 1,
        "sub_stages": [
            {
                "name": "basic_idea",
                "description": "Describe the basic idea",
                "order": 1,
            },
            {"name": "concept", "description": "Develop the concept", "order": 2},
        ],
    },
    {
        "name": "research",
        "description": "Research stage",
        "order": 2,
        "sub_stages": [
            {"name": "sources", "description": "List sources", "order": 1},
            {"name": "notes", "description": "Take research notes", "order": 2},
        ],
    },
]


def seed_workflow_stages():
    app = create_app()
    with app.app_context():
        for stage_data in STAGES:
            stage = WorkflowStageEntity.query.filter_by(name=stage_data["name"]).first()
            if not stage:
                stage = WorkflowStageEntity()
                stage.name = stage_data["name"]
                stage.description = stage_data["description"]
                stage.order = stage_data["order"]
                db.session.add(stage)
                db.session.flush()  # Assigns ID
            for sub_stage_data in stage_data["sub_stages"]:
                sub_stage = WorkflowSubStageEntity.query.filter_by(
                    name=sub_stage_data["name"], stage_id=stage.id
                ).first()
                if not sub_stage:
                    sub_stage = WorkflowSubStageEntity()
                    sub_stage.stage_id = stage.id
                    sub_stage.name = sub_stage_data["name"]
                    sub_stage.description = sub_stage_data["description"]
                    sub_stage.order = sub_stage_data["order"]
                    db.session.add(sub_stage)
        db.session.commit()
        print("Seeded workflow stages and sub-stages.")


def update_workflow_entities():
    app = create_app()
    with app.app_context():
        for order, (stage_name, stage_data) in enumerate(
            WORKFLOW_STAGES.items(), start=1
        ):
            stage = WorkflowStageEntity.query.filter_by(name=stage_name).first()
            if not stage:
                stage = WorkflowStageEntity(
                    name=stage_name, description=stage_data["description"], order=order
                )
                db.session.add(stage)
                db.session.flush()
                print(f"Created stage: {stage_name}")
            else:
                print(f"Stage already exists: {stage_name}")
            # Ensure all sub-stages exist
            for sub_order, (sub_name, sub_data) in enumerate(
                stage_data["sub_stages"].items(), start=1
            ):
                sub_stage = WorkflowSubStageEntity.query.filter_by(
                    stage_id=stage.id, name=sub_name
                ).first()
                if not sub_stage:
                    sub_stage = WorkflowSubStageEntity(
                        stage_id=stage.id,
                        name=sub_name,
                        description=sub_data["description"],
                        order=sub_order,
                    )
                    db.session.add(sub_stage)
                    print(f"  Created sub-stage: {sub_name} (stage: {stage_name})")
                else:
                    print(
                        f"  Sub-stage already exists: {sub_name} (stage: {stage_name})"
                    )
        db.session.commit()
        print("Workflow stages and sub-stages are up to date.")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        update_workflow_status(sys.argv[1])
    else:
        update_workflow_entities()
