from typing import Dict, List, Optional, Tuple
from datetime import datetime

from app import db
from app.models import Post, WorkflowStatus, WorkflowStatusHistory, WorkflowStage
from app.workflow.constants import WORKFLOW_STAGES, VALID_TRANSITIONS, SubStageStatus
from app.workflow.validators import validate_stage


class WorkflowError(Exception):
    """Base exception for workflow errors"""

    pass


class InvalidTransitionError(WorkflowError):
    """Raised when attempting an invalid stage transition"""

    pass


class ValidationError(WorkflowError):
    """Raised when stage validation fails"""

    pass


class WorkflowManager:
    def __init__(self, post: Post):
        self.post = post
        self.workflow_status = post.workflow_status or self._create_initial_status()

    def _create_initial_status(self) -> WorkflowStatus:
        """Create initial workflow status for a post"""
        workflow_status = WorkflowStatus(
            post=self.post,
            current_stage=WorkflowStage.IDEA,
            stage_data={
                "idea": {
                    "started_at": datetime.utcnow().isoformat(),
                    "sub_stages": {
                        "basic_idea": {
                            "status": SubStageStatus.NOT_STARTED,
                            "started_at": None,
                            "completed_at": None,
                            "notes": [],
                        },
                        "audience_definition": {
                            "status": SubStageStatus.NOT_STARTED,
                            "started_at": None,
                            "completed_at": None,
                            "notes": [],
                        },
                        "value_proposition": {
                            "status": SubStageStatus.NOT_STARTED,
                            "started_at": None,
                            "completed_at": None,
                            "notes": [],
                        },
                    },
                }
            },
        )
        db.session.add(workflow_status)
        db.session.commit()
        return workflow_status

    def get_current_stage(self) -> str:
        """Get the current workflow stage"""
        return self.workflow_status.current_stage

    def get_stage_progress(self, stage: str) -> Tuple[int, int]:
        """Get progress for a specific stage (completed sub-stages / total sub-stages)"""
        if stage not in WORKFLOW_STAGES:
            raise ValueError(f"Invalid stage: {stage}")

        stage_data = self.workflow_status.stage_data.get(stage, {})
        sub_stages = stage_data.get("sub_stages", {})
        total_required = sum(
            1 for s in WORKFLOW_STAGES[stage]["sub_stages"].values() if s["required"]
        )
        completed_required = sum(
            1
            for name, s in sub_stages.items()
            if WORKFLOW_STAGES[stage]["sub_stages"][name]["required"]
            and s.get("status") == SubStageStatus.COMPLETED
        )
        return completed_required, total_required

    def get_available_transitions(self) -> List[str]:
        """Get list of stages that can be transitioned to from current stage"""
        return VALID_TRANSITIONS.get(self.workflow_status.current_stage, [])

    def can_transition_to(self, target_stage: str) -> bool:
        """Check if transition to target stage is valid"""
        return target_stage in self.get_available_transitions()

    def transition_to(self, target_stage: str, user_id: int, notes: str = "") -> None:
        """
        Transition to a new stage if valid and all requirements are met
        """
        if not self.can_transition_to(target_stage):
            raise InvalidTransitionError(
                f"Cannot transition from {self.workflow_status.current_stage} to {target_stage}"
            )

        # Validate current stage completion if moving forward
        current_idx = list(WORKFLOW_STAGES.keys()).index(
            self.workflow_status.current_stage
        )
        target_idx = list(WORKFLOW_STAGES.keys()).index(target_stage)

        if target_idx > current_idx:  # Moving forward
            completed, total = self.get_stage_progress(
                self.workflow_status.current_stage
            )
            if completed < total:
                raise ValidationError(
                    f"Cannot proceed: {completed}/{total} required sub-stages completed"
                )

        # Initialize stage data if not exists
        if target_stage not in self.workflow_status.stage_data:
            self.workflow_status.stage_data[target_stage] = {
                "started_at": datetime.utcnow().isoformat(),
                "sub_stages": {
                    name: {
                        "status": SubStageStatus.NOT_STARTED,
                        "started_at": None,
                        "completed_at": None,
                        "notes": [],
                    }
                    for name in WORKFLOW_STAGES[target_stage]["sub_stages"]
                },
            }

        # Create history entry
        history = WorkflowStatusHistory(
            workflow_status=self.workflow_status,
            from_stage=self.workflow_status.current_stage,
            to_stage=target_stage,
            notes=notes,
            user_id=user_id,
        )
        db.session.add(history)

        # Update current stage
        self.workflow_status.current_stage = target_stage
        self.workflow_status.last_updated = datetime.utcnow()
        db.session.commit()

    def update_sub_stage(
        self,
        sub_stage: str,
        status: Optional[SubStageStatus] = None,
        note: Optional[str] = None,
        content: Optional[str] = None,
    ) -> None:
        """Update the status and/or content of a sub-stage"""
        current_stage = self.workflow_status.current_stage
        if current_stage not in self.workflow_status.stage_data:
            raise WorkflowError(f"Stage data not initialized for {current_stage}")

        stage_data = self.workflow_status.stage_data[current_stage]
        if sub_stage not in stage_data["sub_stages"]:
            raise WorkflowError(f"Invalid sub-stage: {sub_stage}")

        sub_stage_data = stage_data["sub_stages"][sub_stage]

        # Update content if provided
        if content is not None:
            sub_stage_data["content"] = content
            sub_stage_data["content_updated_at"] = datetime.utcnow().isoformat()

        # Update status if provided
        if status is not None:
            old_status = sub_stage_data.get("status")
            sub_stage_data["status"] = status

            if (
                status == SubStageStatus.IN_PROGRESS
                and old_status == SubStageStatus.NOT_STARTED
            ):
                sub_stage_data["started_at"] = datetime.utcnow().isoformat()
            elif (
                status == SubStageStatus.COMPLETED
                and old_status != SubStageStatus.COMPLETED
            ):
                sub_stage_data["completed_at"] = datetime.utcnow().isoformat()

        # Add note if provided
        if note:
            if "notes" not in sub_stage_data:
                sub_stage_data["notes"] = []
            sub_stage_data["notes"].append(
                {"text": note, "timestamp": datetime.utcnow().isoformat()}
            )

        # Validate if completing the stage
        if status == SubStageStatus.COMPLETED:
            stage_config = WORKFLOW_STAGES[current_stage]["sub_stages"][sub_stage]
            validate_stage(
                self.post, current_stage, sub_stage, stage_config["validation_rules"]
            )

        db.session.commit()

    def get_sub_stage_status(self, stage: str, sub_stage: str) -> Dict:
        """Get the current status and metadata for a sub-stage"""
        if stage not in self.workflow_status.stage_data:
            raise WorkflowError(f"Stage data not initialized for {stage}")

        stage_data = self.workflow_status.stage_data[stage]
        if sub_stage not in stage_data["sub_stages"]:
            raise WorkflowError(f"Invalid sub-stage: {sub_stage}")

        return stage_data["sub_stages"][sub_stage]
