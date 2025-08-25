from datetime import datetime
import click
from app import create_app, db
from app.models import Post, WorkflowStatus
from app.workflow.constants import WORKFLOW_STAGES, SubStageStatus


def initialize_stage_data(stage_name):
    """Initialize stage data with the correct structure"""
    return {
        "started_at": datetime.utcnow().isoformat(),
        "sub_stages": {
            name: {
                "status": SubStageStatus.NOT_STARTED,
                "started_at": None,
                "completed_at": None,
                "content": "",
                "content_updated_at": None,
                "notes": [],
            }
            for name in WORKFLOW_STAGES[stage_name]["sub_stages"]
        },
    }


def fix_stage_data(stage_data, stage_name):
    """Fix stage data structure for a given stage"""
    if not isinstance(stage_data, dict):
        return initialize_stage_data(stage_name)

    # Ensure started_at exists
    if "started_at" not in stage_data:
        stage_data["started_at"] = datetime.utcnow().isoformat()

    # Ensure sub_stages exists and has correct structure
    if "sub_stages" not in stage_data:
        stage_data["sub_stages"] = {}

    # Get expected sub-stages
    expected_sub_stages = WORKFLOW_STAGES[stage_name]["sub_stages"].keys()

    # Fix each sub-stage
    for sub_stage in expected_sub_stages:
        if sub_stage not in stage_data["sub_stages"]:
            stage_data["sub_stages"][sub_stage] = {
                "status": SubStageStatus.NOT_STARTED,
                "started_at": None,
                "completed_at": None,
                "content": "",
                "content_updated_at": None,
                "notes": [],
            }
        else:
            sub_stage_data = stage_data["sub_stages"][sub_stage]

            # Ensure all required fields exist
            if "status" not in sub_stage_data:
                sub_stage_data["status"] = SubStageStatus.NOT_STARTED
            if "started_at" not in sub_stage_data:
                sub_stage_data["started_at"] = None
            if "completed_at" not in sub_stage_data:
                sub_stage_data["completed_at"] = None
            if "content" not in sub_stage_data:
                sub_stage_data["content"] = ""
            if "content_updated_at" not in sub_stage_data:
                sub_stage_data["content_updated_at"] = None
            if "notes" not in sub_stage_data:
                sub_stage_data["notes"] = []

    return stage_data


@click.command()
@click.argument("slug", required=False)
def fix_workflow_status(slug=None):
    """Fix workflow status data structure for one or all posts"""
    app = create_app()

    with app.app_context():
        if slug:
            posts = Post.query.filter_by(slug=slug).all()
        else:
            posts = Post.query.all()

        for post in posts:
            if not post.workflow_status:
                click.echo(f"Post {post.slug} has no workflow status, skipping")
                continue

            click.echo(f"Fixing workflow status for post: {post.slug}")

            # Get current stage data
            stage_data = post.workflow_status.stage_data or {}

            # Fix each stage that exists and initialize missing stages
            fixed_stage_data = {}
            for stage_name in WORKFLOW_STAGES:
                if stage_name in stage_data:
                    fixed_stage_data[stage_name] = fix_stage_data(
                        stage_data[stage_name], stage_name
                    )
                else:
                    fixed_stage_data[stage_name] = initialize_stage_data(stage_name)

            # Update the workflow status
            post.workflow_status.stage_data = fixed_stage_data
            post.workflow_status.last_updated = datetime.utcnow()

            db.session.commit()
            click.echo(f"Fixed workflow status for post: {post.slug}")


if __name__ == "__main__":
    fix_workflow_status()
