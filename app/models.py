from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Enum
import enum


class WorkflowStage(str, enum.Enum):
    CONCEPTUALIZATION = "conceptualization"
    DRAFTING = "drafting"
    EDITING = "editing"
    REVIEW = "review"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    concept = db.Column(db.Text)
    published = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    published_at = db.Column(db.DateTime)
    header_image_id = db.Column(db.Integer, db.ForeignKey("image.id"))
    llm_metadata = db.Column(JSON)
    seo_metadata = db.Column(JSON)
    syndication_status = db.Column(JSON)

    # Relationships
    header_image = db.relationship("Image", foreign_keys=[header_image_id])
    sections = db.relationship(
        "PostSection", back_populates="post", order_by="PostSection.position"
    )
    tags = db.relationship("Tag", secondary="post_tags")
    categories = db.relationship("Category", secondary="post_categories")
    workflow_status = db.relationship(
        "WorkflowStatus", back_populates="post", uselist=False
    )


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    path = db.Column(db.String(255), unique=True, nullable=False)
    alt_text = db.Column(db.String(255))
    caption = db.Column(db.Text)
    image_prompt = db.Column(db.Text)
    notes = db.Column(db.Text)
    image_metadata = db.Column(JSON)
    watermarked = db.Column(db.Boolean, default=False)
    watermarked_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class LLMPrompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    prompt_text = db.Column(db.Text, nullable=False)
    system_prompt = db.Column(db.Text)
    parameters = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class LLMInteraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey("llm_prompt.id"))
    input_text = db.Column(db.Text, nullable=False)
    output_text = db.Column(db.Text)
    parameters_used = db.Column(JSON)
    interaction_metadata = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    prompt = db.relationship("LLMPrompt")


# Association tables
post_categories = db.Table(
    "post_categories",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
    db.Column(
        "category_id", db.Integer, db.ForeignKey("category.id"), primary_key=True
    ),
)

post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class WorkflowStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), unique=True)
    current_stage = db.Column(Enum(WorkflowStage))
    stage_data = db.Column(JSON)
    last_updated = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    post = db.relationship("Post", back_populates="workflow_status")
    history = db.relationship("WorkflowStatusHistory", back_populates="workflow_status")


class PostSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    title = db.Column(db.String(200))
    subtitle = db.Column(db.String(200))
    content = db.Column(db.Text)
    position = db.Column(db.Integer, nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey("image.id"))
    content_type = db.Column(db.String(50), default="text")
    video_url = db.Column(db.String(255))
    audio_url = db.Column(db.String(255))
    duration = db.Column(db.Integer)  # Duration in seconds for video/audio content
    keywords = db.Column(JSON)
    social_media_snippets = db.Column(JSON)
    section_metadata = db.Column(JSON)

    # Relationships
    post = db.relationship("Post", back_populates="sections")
    image = db.relationship("Image")


class WorkflowStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workflow_status_id = db.Column(db.Integer, db.ForeignKey("workflow_status.id"))
    from_stage = db.Column(Enum(WorkflowStage))
    to_stage = db.Column(Enum(WorkflowStage))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    workflow_status = db.relationship("WorkflowStatus", back_populates="history")
