# Models Documentation

## Content Models

### Post
The core content model representing a blog post.

```python
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    concept = db.Column(db.Text)
    basic_idea = db.Column(db.Text)
    published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    header_image_id = db.Column(db.Integer, db.ForeignKey("image.id"))
    llm_metadata = db.Column(JSON)
    seo_metadata = db.Column(JSON)
    syndication_status = db.Column(JSON)
```

#### Relationships
- `header_image`: One-to-one with Image
- `sections`: One-to-many with PostSection
- `tags`: Many-to-many with Tag
- `categories`: Many-to-many with Category
- `workflow_status`: One-to-one with WorkflowStatus

### PostSection
Represents a section within a blog post.

```python
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
    duration = db.Column(db.Integer)
    keywords = db.Column(JSON)
    social_media_snippets = db.Column(JSON)
    section_metadata = db.Column(JSON)
```

## Media Models

### Image
Handles image assets and their metadata.

```python
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
```

## Taxonomy Models

### Category
```python
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
```

### Tag
```python
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
```

## Workflow Models

### WorkflowStage
```python
class WorkflowStage(str, enum.Enum):
    CONCEPTUALIZATION = "conceptualization"
    DRAFTING = "drafting"
    EDITING = "editing"
    REVIEW = "review"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    ARCHIVED = "archived"
```

### WorkflowStatus
```python
class WorkflowStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), unique=True)
    current_stage = db.Column(Enum(WorkflowStage))
    stage_data = db.Column(JSON)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### WorkflowStatusHistory
```python
class WorkflowStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workflow_status_id = db.Column(db.Integer, db.ForeignKey("workflow_status.id"))
    from_stage = db.Column(Enum(WorkflowStage))
    to_stage = db.Column(Enum(WorkflowStage))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## LLM Integration Models

### LLMPrompt
```python
class LLMPrompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    prompt_text = db.Column(db.Text, nullable=False)
    system_prompt = db.Column(db.Text)
    parameters = db.Column(JSON)
```

### LLMInteraction
```python
class LLMInteraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey("llm_prompt.id"))
    input_text = db.Column(db.Text, nullable=False)
    output_text = db.Column(db.Text)
    parameters_used = db.Column(JSON)
    interaction_metadata = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## JSON Field Schemas

### Post Metadata
- `llm_metadata`: AI generation details
- `seo_metadata`: SEO optimization data
- `syndication_status`: Publishing status on external platforms

### Section Metadata
- `keywords`: SEO and categorization keywords
- `social_media_snippets`: Pre-generated social content
- `section_metadata`: Additional section-specific data

### Image Metadata
- `image_metadata`: EXIF data, dimensions, etc.

### Workflow Stage Data
- `stage_data`: Stage-specific information and requirements 