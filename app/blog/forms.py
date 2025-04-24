from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    SelectMultipleField,
    SubmitField,
    TextAreaField,
    HiddenField,
)
from wtforms.validators import DataRequired, Length, Optional
from app.models import WorkflowStage


class PostForm(FlaskForm):
    """Form for creating and editing blog posts."""

    # Hidden field for workflow stage transitions
    next_stage = HiddenField("Next Stage")

    # Idea Stage
    concept = TextAreaField(
        "Initial Idea",
        validators=[
            Optional(),
            Length(max=2000, message="Concept must be less than 2000 characters"),
        ],
    )

    # Brainstorm Stage
    brainstorm = TextAreaField(
        "Brainstorming Notes",
        validators=[
            Optional(),
            Length(
                max=5000,
                message="Brainstorming notes must be less than 5000 characters",
            ),
        ],
    )

    # Sections Stage
    sections_plan = TextAreaField(
        "Section Plan",
        validators=[
            Optional(),
            Length(max=5000, message="Section plan must be less than 5000 characters"),
        ],
    )

    # Basic Fields (Authoring Stage)
    title = StringField(
        "Title",
        validators=[
            DataRequired(),
            Length(max=200, message="Title must be less than 200 characters"),
        ],
    )

    summary = TextAreaField(
        "Summary",
        validators=[
            DataRequired(),
            Length(max=500, message="Summary must be less than 500 characters"),
        ],
    )

    content = TextAreaField(
        "Content",
        validators=[
            DataRequired(),
            Length(min=100, message="Content must be at least 100 characters"),
        ],
    )

    # Metadata Stage
    categories = SelectMultipleField(
        "Categories",
        validators=[DataRequired(message="At least one category is required")],
        coerce=int,
    )

    tags = StringField("Tags", validators=[Optional()])

    seo_title = StringField(
        "SEO Title",
        validators=[
            Optional(),
            Length(max=60, message="SEO title must be less than 60 characters"),
        ],
    )

    seo_description = TextAreaField(
        "SEO Description",
        validators=[
            Optional(),
            Length(max=160, message="SEO description must be less than 160 characters"),
        ],
    )

    # Images Stage
    header_image = FileField(
        "Header Image", validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only!")]
    )

    header_image_alt = StringField(
        "Header Image Alt Text",
        validators=[
            Optional(),
            Length(max=200, message="Alt text must be less than 200 characters"),
        ],
    )

    # Validation Stage
    validation_notes = TextAreaField(
        "Validation Notes",
        validators=[
            Optional(),
            Length(
                max=1000, message="Validation notes must be less than 1000 characters"
            ),
        ],
    )

    # Publishing Stage
    schedule_publish = StringField(
        "Schedule Publish Date/Time", validators=[Optional()]
    )

    # Syndication Stage
    syndication_platforms = SelectMultipleField(
        "Syndication Platforms",
        choices=[("clan_com", "Clan.com")],
        validators=[Optional()],
    )

    def validate_for_stage(self, stage):
        """Validate form data for a specific workflow stage."""
        if stage == WorkflowStage.IDEA:
            return bool(self.concept.data)

        elif stage == WorkflowStage.BRAINSTORM:
            return bool(self.brainstorm.data)

        elif stage == WorkflowStage.SECTIONS:
            return bool(self.sections_plan.data)

        elif stage == WorkflowStage.AUTHORING:
            return bool(self.title.data and self.content.data and self.summary.data)

        elif stage == WorkflowStage.METADATA:
            return bool(
                self.categories.data
                and self.seo_title.data
                and self.seo_description.data
            )

        elif stage == WorkflowStage.IMAGES:
            # For existing posts, don't require header_image if one already exists
            return bool(self.header_image.data or self.header_image_alt.data)

        elif stage == WorkflowStage.VALIDATION:
            # All previous stages must be valid
            return all(
                [
                    self.validate_for_stage(WorkflowStage.IDEA),
                    self.validate_for_stage(WorkflowStage.BRAINSTORM),
                    self.validate_for_stage(WorkflowStage.SECTIONS),
                    self.validate_for_stage(WorkflowStage.AUTHORING),
                    self.validate_for_stage(WorkflowStage.METADATA),
                    self.validate_for_stage(WorkflowStage.IMAGES),
                ]
            )

        return True  # Other stages don't have specific validation

    submit = SubmitField("Save Changes")
