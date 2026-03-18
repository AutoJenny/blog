from app import create_app, db
from app.models import (
    Post,
    PostWorkflowStage,
    PostWorkflowSubStage,
    WorkflowStageEntity,
    WorkflowSubStageEntity,
)


def inspect_workflow(slug):
    app = create_app()
    with app.app_context():
        post = Post.query.filter_by(slug=slug).first()
        if not post:
            print(f"Post with slug '{slug}' not found.")
            return

        print(f"Post: {post.id} - {post.slug}")
        stages = PostWorkflowStage.query.filter_by(post_id=post.id).all()
        for stage in stages:
            stage_entity = WorkflowStageEntity.query.get(stage.stage_id)
            print(
                f"  Stage: {stage.id} ({stage_entity.name if stage_entity else 'Unknown'})"
            )
            sub_stages = PostWorkflowSubStage.query.filter_by(
                post_workflow_stage_id=stage.id
            ).all()
            for sub in sub_stages:
                sub_entity = WorkflowSubStageEntity.query.get(sub.sub_stage_id)
                print(
                    f"    Sub-Stage: {sub.id} ({sub_entity.name if sub_entity else 'Unknown'})"
                )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python scripts/inspect_workflow.py <post-slug>")
    else:
        inspect_workflow(sys.argv[1])
