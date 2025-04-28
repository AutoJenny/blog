from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Enum
import enum


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


class PromptTemplate(db.Model):
    """Model for storing prompt templates"""

    __tablename__ = "prompt_template"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<PromptTemplate {self.name}>"


class LLMAction(db.Model):
    __tablename__ = 'llm_action'
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(100), nullable=False, unique=True)  # e.g. 'provisional_title'
    stage_name = db.Column(db.String(100), nullable=True)  # e.g. 'Idea Stage'
    source_field = db.Column(db.String(100), nullable=False, default='')  # The source field for this action
    prompt_template = db.Column(db.Text, nullable=False)
    llm_model = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.Float, nullable=False, default=0.7)
    max_tokens = db.Column(db.Integer, nullable=False, default=64)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
