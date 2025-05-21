from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Enum
import enum
from jinja2 import Template
from flask import current_app
from sqlalchemy import event
from sqlalchemy.orm import Session
import subprocess
import os
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship


class WorkflowStage(str, enum.Enum):
    IDEA = "idea"
    RESEARCH = "research"
    OUTLINING = "outlining"
    AUTHORING = "authoring"
    IMAGES = "images"
    METADATA = "metadata"
    REVIEW = "review"
    PUBLISHING = "publishing"
    UPDATES = "updates"
    SYNDICATION = "syndication"

    def __str__(self):
        return self.value


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
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    published = db.Column(db.Boolean, default=False)
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
        "PostSection", backref=db.backref("post"), order_by="PostSection.section_order"
    )
    tags = db.relationship("Tag", secondary="post_tags")
    categories = db.relationship("Category", secondary="post_categories")


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
    order = db.Column(db.Integer, default=0, nullable=False)
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


class PostSection(db.Model):
    __tablename__ = "post_section"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    section_order = db.Column(db.Integer)
    section_heading = db.Column(db.Text)
    ideas_to_include = db.Column(db.Text)
    facts_to_include = db.Column(db.Text)
    # Per-section fields (all nullable)
    first_draft = db.Column(db.Text)
    uk_british = db.Column(db.Text)
    highlighting = db.Column(db.Text)
    image_concepts = db.Column(db.Text)
    image_prompts = db.Column(db.Text)
    generation = db.Column(db.Text)
    optimization = db.Column(db.Text)
    watermarking = db.Column(db.Text)
    image_meta_descriptions = db.Column(db.Text)
    image_captions = db.Column(db.Text)
    image_prompt_example_id = db.Column(db.Integer, db.ForeignKey('image_prompt_example.id'), nullable=True)
    generated_image_url = db.Column(db.String(512), nullable=True)
    image_generation_metadata = db.Column(JSON, nullable=True)


class PostDevelopment(db.Model):
    __tablename__ = "post_development"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(
        db.Integer, db.ForeignKey("post.id"), unique=True, nullable=False
    )
    # Global fields (all nullable)
    basic_idea = db.Column(db.Text)
    provisional_title = db.Column(db.Text)
    idea_scope = db.Column(db.Text)
    topics_to_cover = db.Column(db.Text)
    interesting_facts = db.Column(db.Text)
    tartans_products = db.Column(db.Text)
    section_planning = db.Column(db.Text)
    section_headings = db.Column(db.Text)
    section_order = db.Column(db.Text)
    main_title = db.Column(db.Text)
    subtitle = db.Column(db.Text)
    intro_blurb = db.Column(db.Text)
    conclusion = db.Column(db.Text)
    basic_metadata = db.Column(db.Text)
    tags = db.Column(db.Text)
    categories = db.Column(db.Text)
    image_captions = db.Column(db.Text)
    seo_optimization = db.Column(db.Text)
    self_review = db.Column(db.Text)
    peer_review = db.Column(db.Text)
    final_check = db.Column(db.Text)
    scheduling = db.Column(db.Text)
    deployment = db.Column(db.Text)
    verification = db.Column(db.Text)
    feedback_collection = db.Column(db.Text)
    content_updates = db.Column(db.Text)
    version_control = db.Column(db.Text)
    platform_selection = db.Column(db.Text)
    content_adaptation = db.Column(db.Text)
    distribution = db.Column(db.Text)
    engagement_tracking = db.Column(db.Text)
    post = db.relationship("Post", backref=db.backref("development", uselist=False))


class LLMConfig(db.Model):
    """Configuration for LLM providers"""

    id = db.Column(db.Integer, primary_key=True)
    provider_type = db.Column(db.String(50), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    api_base = db.Column(db.String(200), nullable=False)
    auth_token = db.Column(db.String(200))  # Authentication token for the provider
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<LLMConfig {self.provider_type}:{self.model_name}>"


class LLMAction(db.Model):
    """Model for storing LLM action configurations."""
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(128), nullable=False)
    prompt_template = db.Column(db.Text, nullable=False)
    prompt_template_id = db.Column(db.Integer, db.ForeignKey('llm_prompt.id'), nullable=False)
    llm_model = db.Column(db.String(128), nullable=False)
    temperature = db.Column(db.Float, default=0.7)
    max_tokens = db.Column(db.Integer, default=1000)
    order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to history
    history = db.relationship('LLMActionHistory', backref='action', lazy='dynamic')
    
    def process_template(self, fields: dict) -> str:
        """Process the prompt template with the given fields dict.
        Supports {{field}} syntax for any field in the dict.
        """
        try:
            template = Template(self.prompt_template)
            return template.render(**fields)
        except Exception as e:
            # Log the template and fields for debugging
            current_app.logger.error(f"Template rendering error: {e}\nTemplate: {self.prompt_template}\nFields: {fields}")
            raise ValueError(f"Error processing prompt template: {e}")
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'field_name': self.field_name,
            'prompt_template': self.prompt_template,
            'prompt_template_id': self.prompt_template_id,
            'llm_model': self.llm_model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'order': self.order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class LLMActionHistory(db.Model):
    """Model for storing LLM action execution history."""
    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.Integer, db.ForeignKey('llm_action.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    input_text = db.Column(db.Text, nullable=False)
    output_text = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, success, error
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'action_id': self.action_id,
            'post_id': self.post_id,
            'input_text': self.input_text,
            'output_text': self.output_text,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class User(db.Model):
    """User model for authentication and tracking."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'


class ImageStyle(db.Model):
    __tablename__ = 'image_style'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ImageFormat(db.Model):
    __tablename__ = 'image_format'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    width = db.Column(db.Integer, nullable=True)  # SD/ComfyUI
    height = db.Column(db.Integer, nullable=True) # SD/ComfyUI
    steps = db.Column(db.Integer, nullable=True)  # SD/ComfyUI
    guidance_scale = db.Column(db.Float, nullable=True) # SD/ComfyUI
    extra_settings = db.Column(db.Text, nullable=True)  # JSON or freeform for advanced/provider-specific options
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'width': self.width,
            'height': self.height,
            'steps': self.steps,
            'guidance_scale': self.guidance_scale,
            'extra_settings': self.extra_settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ImageSetting(db.Model):
    __tablename__ = 'image_setting'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    style_id = db.Column(db.Integer, db.ForeignKey('image_style.id'), nullable=False)
    format_id = db.Column(db.Integer, db.ForeignKey('image_format.id'), nullable=False)
    width = db.Column(db.Integer, nullable=True)  # SD/ComfyUI
    height = db.Column(db.Integer, nullable=True) # SD/ComfyUI
    steps = db.Column(db.Integer, nullable=True)  # SD/ComfyUI
    guidance_scale = db.Column(db.Float, nullable=True) # SD/ComfyUI
    extra_settings = db.Column(db.Text, nullable=True)  # JSON or freeform for advanced/provider-specific options
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    style = db.relationship('ImageStyle', backref='image_settings')
    format = db.relationship('ImageFormat', backref='image_settings')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'style_id': self.style_id,
            'format_id': self.format_id,
            'width': self.width,
            'height': self.height,
            'steps': self.steps,
            'guidance_scale': self.guidance_scale,
            'extra_settings': self.extra_settings,
            'style': self.style.to_dict() if self.style else None,
            'format': self.format.to_dict() if self.format else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# New: Prompt Example model
class ImagePromptExample(db.Model):
    __tablename__ = 'image_prompt_example'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    style_id = db.Column(db.Integer, db.ForeignKey('image_style.id'), nullable=False)
    format_id = db.Column(db.Integer, db.ForeignKey('image_format.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # e.g., 'sd', 'openai'
    image_setting_id = db.Column(db.Integer, db.ForeignKey('image_setting.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    style = db.relationship('ImageStyle')
    format = db.relationship('ImageFormat')
    image_setting = db.relationship('ImageSetting')

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'style_id': self.style_id,
            'format_id': self.format_id,
            'provider': self.provider,
            'image_setting_id': self.image_setting_id,
            'style': self.style.to_dict() if self.style else None,
            'format': self.format.to_dict() if self.format else None,
            'image_setting': self.image_setting.to_dict() if self.image_setting else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# --- Automatic backup after DB commit ---
def backup_after_commit(session):
    # Only backup if there were changes
    if session.new or session.dirty or session.deleted:
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/blog")
        try:
            subprocess.Popen(["python", "scripts/db_backup.py"])  # Non-blocking
        except Exception as e:
            print(f"[Backup Trigger] Failed to run backup: {e}")

# Register the event listener for all sessions
try:
    event.listen(Session, "after_commit", backup_after_commit)
except Exception as e:
    print(f"[Backup Trigger] Could not register after_commit event: {e}")


class WorkflowStatus(db.Model):
    __tablename__ = 'workflow_status'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), unique=True, nullable=False)
    conceptualisation = db.Column(db.String(32), default='not_started')
    authoring = db.Column(db.String(32), default='not_started')
    meta_status = db.Column(db.String(32), default='not_started')
    images = db.Column(db.String(32), default='not_started')
    validation = db.Column(db.String(32), default='not_started')
    publishing = db.Column(db.String(32), default='not_started')
    syndication = db.Column(db.String(32), default='not_started')
    log = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    post = db.relationship('Post', backref=db.backref('workflow_status', uselist=False))
