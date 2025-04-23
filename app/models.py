from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
import jwt
from time import time
from flask import current_app
import json
from enum import Enum
from flask_login import UserMixin


class WorkflowStage(Enum):
    CONCEPTUALIZATION = "conceptualization"
    AUTHORING = "authoring"
    METADATA = "metadata"
    IMAGES = "images"
    VALIDATION = "validation"
    PUBLISHING = "publishing"
    SYNDICATION = "syndication"


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    posts = relationship("Post", backref="author", lazy="dynamic")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["reset_password"]
        except:
            return None
        return User.query.get(id)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    children = relationship(
        "app.models.Category", backref=db.backref("parent", remote_side=[id])
    )
    posts = relationship(
        "app.models.Post", secondary="post_categories", backref="categories"
    )


class PostCategories(db.Model):
    __tablename__ = "post_categories"
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), primary_key=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(200))
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))
    concept = db.Column(db.Text)
    description = db.Column(db.Text)
    published = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    published_at = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tags = relationship("Tag", secondary="post_tags", backref="posts")
    sections = relationship(
        "app.models.PostSection", backref="post", order_by="PostSection.position"
    )
    header_image_id = db.Column(db.Integer, db.ForeignKey("image.id"))
    header_image = relationship("app.models.Image", foreign_keys=[header_image_id])
    clan_com_post_id = db.Column(db.String(100))  # ID on clan.com when published
    workflow_status = relationship(
        "app.models.WorkflowStatus", backref="post", uselist=False
    )
    llm_metadata = db.Column(db.JSON)
    seo_metadata = db.Column(db.JSON)
    syndication_status = db.Column(db.JSON)

    @hybrid_property
    def reading_time(self):
        words_per_minute = 200
        word_count = len(self.content.split())
        minutes = word_count / words_per_minute
        return round(minutes)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "summary": self.summary,
            "concept": self.concept,
            "published": self.published,
            "deleted": self.deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": (
                self.published_at.isoformat() if self.published_at else None
            ),
            "author": (
                {
                    "id": self.author.id,
                    "username": self.author.username,
                    "email": self.author.email,
                }
                if self.author
                else None
            ),
            "tags": [
                {"id": tag.id, "name": tag.name, "slug": tag.slug}
                for tag in (self.tags or [])
            ],
            "categories": [
                {"id": cat.id, "name": cat.name, "slug": cat.slug}
                for cat in (self.categories or [])
            ],
            "header_image": self.header_image.to_dict() if self.header_image else None,
            "workflow_status": (
                self.workflow_status.to_dict() if self.workflow_status else None
            ),
            "clan_com_post_id": self.clan_com_post_id,
            "seo_metadata": self.seo_metadata or {},
            "syndication_status": self.syndication_status or {},
            "llm_metadata": self.llm_metadata or {},
        }


class PostSection(db.Model):
    """A section of a blog post that can be repurposed for different content formats.

    This model represents a discrete section of content within a blog post that can be
    independently repurposed for various social media platforms and content formats.
    Each section can contain text, images, video, or audio content, along with
    metadata for content repurposing.

    Attributes:
        id (int): Primary key
        post_id (int): Foreign key to the parent Post
        title (str): Optional title for the section
        subtitle (str): Optional subtitle/description for the section
        content (str): Main content text
        position (int): Order within the post (unique per post)
        image_id (int): Optional foreign key to an associated image
        image (Image): Relationship to the Image model
        video_url (str): Optional URL to video content
        audio_url (str): Optional URL to audio content
        content_type (str): Type of content ('text', 'image', 'video', 'audio')
        duration (int): Duration in seconds for video/audio content
        keywords (dict): JSON field for SEO and content discovery
        social_media_snippets (dict): JSON field for platform-specific content versions
        section_metadata (dict): JSON field for additional metadata
        created_at (datetime): Timestamp of creation
        updated_at (datetime): Timestamp of last update
    """

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(
        db.Integer, db.ForeignKey("post.id", ondelete="CASCADE"), nullable=False
    )
    title = db.Column(db.String(200))
    subtitle = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey("image.id", ondelete="SET NULL"))
    image = relationship("Image", foreign_keys=[image_id])
    video_url = db.Column(db.String(500))
    audio_url = db.Column(db.String(500))
    content_type = db.Column(db.String(50), nullable=False, default="text")
    duration = db.Column(db.Integer)  # Duration in seconds for video/audio content
    keywords = db.Column(db.JSON)
    social_media_snippets = db.Column(db.JSON)
    section_metadata = db.Column(db.JSON)
    is_conclusion = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.Index("idx_post_section_position", "post_id", "position", unique=True),
        db.Index("idx_post_section_content_type", "content_type"),
        db.Index("idx_post_section_created", "created_at"),
    )

    def to_dict(self):
        """Convert the section to a dictionary representation."""
        return {
            "id": self.id,
            "post_id": self.post_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "content": self.content,
            "position": self.position,
            "image": self.image.to_dict() if self.image else None,
            "video_url": self.video_url,
            "audio_url": self.audio_url,
            "content_type": self.content_type,
            "duration": self.duration,
            "keywords": self.keywords,
            "social_media_snippets": self.social_media_snippets,
            "section_metadata": self.section_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def get_social_media_content(self, platform):
        """Get platform-specific content for a social media platform.

        Args:
            platform (str): The target platform (e.g., 'tiktok', 'youtube', 'instagram')

        Returns:
            dict: Platform-specific content and metadata
        """
        if not self.social_media_snippets or platform not in self.social_media_snippets:
            return None
        return self.social_media_snippets.get(platform)

    def set_social_media_content(self, platform, content):
        """Set platform-specific content for a social media platform.

        Args:
            platform (str): The target platform (e.g., 'tiktok', 'youtube', 'instagram')
            content (dict): Platform-specific content and metadata
        """
        if not self.social_media_snippets:
            self.social_media_snippets = {}
        self.social_media_snippets[platform] = content

    @property
    def has_media(self):
        """Check if the section has any media content."""
        return bool(self.image_id or self.video_url or self.audio_url)

    @property
    def word_count(self):
        """Get the word count of the content."""
        return len(self.content.split()) if self.content else 0

    @property
    def reading_time(self):
        """Estimate reading time in seconds."""
        words_per_minute = 200
        return (self.word_count / words_per_minute) * 60 if self.word_count else 0


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)


class PostTags(db.Model):
    __tablename__ = "post_tags"
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tag.id"), primary_key=True)


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    alt_text = db.Column(db.String(500))
    caption = db.Column(db.Text)
    image_prompt = db.Column(db.Text)  # For AI image generation prompts
    notes = db.Column(db.Text)
    image_metadata = db.Column(db.JSON)  # For EXIF and other technical metadata
    watermarked = db.Column(db.Boolean, default=False)
    watermarked_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "path": self.path,
            "alt_text": self.alt_text,
            "caption": self.caption,
            "image_prompt": self.image_prompt,
            "notes": self.notes,
            "image_metadata": self.image_metadata,
            "watermarked": self.watermarked,
            "watermarked_path": self.watermarked_path,
        }


class WorkflowStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    current_stage = db.Column(
        db.Enum(WorkflowStage), nullable=False, default=WorkflowStage.CONCEPTUALIZATION
    )
    stage_data = db.Column(db.JSON)  # Stores stage-specific data
    last_updated = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    history = relationship(
        "app.models.WorkflowStatusHistory",
        backref="workflow_status",
        order_by="WorkflowStatusHistory.created_at.desc()",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "current_stage": self.current_stage.value,
            "stage_data": self.stage_data,
            "last_updated": self.last_updated.isoformat(),
            "history": [h.to_dict() for h in self.history],
        }


class WorkflowStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workflow_status_id = db.Column(
        db.Integer, db.ForeignKey("workflow_status.id"), nullable=False
    )
    from_stage = db.Column(db.Enum(WorkflowStage), nullable=False)
    to_stage = db.Column(db.Enum(WorkflowStage), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = relationship("app.models.User")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "from_stage": self.from_stage.value if self.from_stage else None,
            "to_stage": self.to_stage.value if self.to_stage else None,
            "user": self.user.username if self.user else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LLMPrompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    prompt_template = db.Column(db.Text, nullable=False)
    parameters = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def get_formatted_prompt(self, **kwargs):
        return self.prompt_template.format(**kwargs)


class LLMInteraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey("llm_prompt.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    input_text = db.Column(db.Text, nullable=False)
    output_text = db.Column(db.Text, nullable=False)
    model_used = db.Column(db.String(50), nullable=False)
    parameters = db.Column(db.JSON)
    tokens_used = db.Column(db.Integer)
    duration = db.Column(db.Float)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "post_id": self.post_id,
            "input_text": self.input_text,
            "output_text": self.output_text,
            "model_used": self.model_used,
            "parameters": (
                json.loads(self.parameters)
                if isinstance(self.parameters, str)
                else self.parameters
            ),
            "tokens_used": self.tokens_used,
            "duration": self.duration,
            "created_at": self.created_at.isoformat(),
        }
