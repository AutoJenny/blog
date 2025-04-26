#!/usr/bin/env python3
import os
import sys
from datetime import datetime

# Add the application root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import Post, WorkflowStatus, WorkflowStage
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_workflow.py <post-slug>")
        sys.exit(1)

    update_workflow_status(sys.argv[1])
