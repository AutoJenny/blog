# Database Models

## Post Model
The `Post` model represents a blog post with the following key relationships:

### Images
- **Header Image**: Accessed via `post.header_image` property
  - Returns the first image from the post's images collection
  - Used for post previews and headers
  - Path format: `images/posts/<post_slug>/<filename>`

- **Section Images**: Accessed via `post.sections[i].image`
  - Each section can have one associated image
  - Images are stored in the static directory
  - Path format: `images/posts/<post_slug>/<filename>`

### Image Naming Conventions
- Header images: `<post_slug>_header.jpg` or `<post_slug>_header-collage.jpg`
- Section images: `<post_slug>_<section-title-slug>.jpg`
  - Section title slugs replace spaces with hyphens
  - Remove special characters like colons
  - Convert to lowercase

## Image Model
The `Image` model stores image metadata and paths:

```python
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    alt_text = db.Column(db.String(500))
    caption = db.Column(db.Text)
    image_prompt = db.Column(db.Text)  # For AI image generation prompts
    notes = db.Column(db.Text)
    image_metadata = db.Column(db.JSON)
    watermarked = db.Column(db.Boolean, default=False)
    watermarked_path = db.Column(db.String(500))
    post_id = db.Column(db.Integer, db.ForeignKey("post.id", ondelete="CASCADE"))
```

## Workflow Stages
The blog uses a workflow system to track post progress:

```python
class WorkflowStage(str, Enum):
    IDEA = "IDEA"
    BRAINSTORM = "BRAINSTORM"
    SECTIONS = "SECTIONS"
    AUTHORING = "AUTHORING"
    METADATA = "METADATA"
    IMAGES = "IMAGES"
    VALIDATION = "VALIDATION"
    PUBLISHING = "PUBLISHING"
    SYNDICATION = "SYNDICATION"
```

Each stage represents a step in the content creation process, from initial idea to final syndication.

## Image Processing
Images are processed using the following steps:

1. **Upload**: Images are uploaded to `app/static/images/posts/<post_slug>/`
2. **Database Entry**: Image metadata is stored in the database
3. **Association**: Images are linked to posts or sections
4. **Processing**: Optional watermarking and optimization
5. **Serving**: Images are served from the static directory

## Utilities
Several utility scripts manage images:

- `check_images.py`: Verifies and fixes image associations
- `update_section_images.py`: Maps section titles to image filenames 