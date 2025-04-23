# Post Model Documentation

## Overview
The `Post` model represents a blog post in the system. It serves as the main container for blog content, managing both the content itself and associated metadata for publishing, SEO, and syndication.

## Schema

### Core Fields
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Primary key | NOT NULL, AUTO INCREMENT |
| title | String(140) | Post title | NOT NULL |
| slug | String(140) | URL-friendly title | NOT NULL, UNIQUE |
| subtitle | String(140) | Optional subtitle | |
| summary | Text | Post summary | |
| content | Text | Main post content | |
| created_at | DateTime | Creation timestamp | NOT NULL, DEFAULT now() |
| updated_at | DateTime | Last update timestamp | NOT NULL, DEFAULT now() |
| published_at | DateTime | Publication timestamp | |
| author_id | Integer | Reference to User | FOREIGN KEY |
| header_image_id | Integer | Reference to Image | FOREIGN KEY |
| is_deleted | Boolean | Soft delete flag | NOT NULL, DEFAULT false |

### Metadata Fields
| Field | Type | Description |
|-------|------|-------------|
| seo_title | String(70) | SEO-optimized title |
| seo_description | String(160) | Meta description |
| social_title | String(100) | Social media title |
| social_description | String(200) | Social media description |
| keywords | ARRAY[String] | SEO keywords |
| canonical_url | String | Canonical URL |

### Workflow Fields
| Field | Type | Description |
|-------|------|-------------|
| workflow_status_id | Integer | Current workflow stage |
| is_published | Boolean | Publication status |
| is_draft | Boolean | Draft status |
| publish_date | DateTime | Scheduled publish date |
| unpublish_date | DateTime | Scheduled unpublish date |

## Relationships

### One-to-Many
- `sections`: List of PostSection
- `workflow_history`: List of WorkflowStatusHistory
- `llm_interactions`: List of LLMInteraction

### Many-to-Many
- `categories`: List of Category through post_categories
- `tags`: List of Tag through post_tags

### Many-to-One
- `author`: User
- `header_image`: Image
- `workflow_status`: WorkflowStatus

## Methods

### Content Management
```python
def add_section(self, content, position=None) -> PostSection:
    """Add a new section to the post."""

def reorder_sections(self, section_ids: List[int]) -> None:
    """Reorder sections based on provided IDs."""

def duplicate(self) -> 'Post':
    """Create a copy of the post with sections."""
```

### Workflow Management
```python
def publish(self, schedule: Optional[datetime] = None) -> None:
    """Publish or schedule post publication."""

def unpublish(self, schedule: Optional[datetime] = None) -> None:
    """Unpublish or schedule post unpublication."""

def update_workflow_status(self, status: str, user_id: int) -> None:
    """Update workflow status with history tracking."""
```

### Utility Methods
```python
def to_dict(self) -> Dict:
    """Convert post to dictionary representation."""

def from_dict(self, data: Dict) -> None:
    """Update post from dictionary data."""

@property
def reading_time(self) -> int:
    """Calculate estimated reading time in minutes."""
```

## Usage Examples

### Creating a Post
```python
post = Post(
    title="My First Post",
    slug="my-first-post",
    author_id=current_user.id
)
db.session.add(post)
db.session.commit()
```

### Adding Sections
```python
section = post.add_section(
    content="Hello World",
    position=1
)
db.session.commit()
```

### Publishing Workflow
```python
# Immediate publish
post.publish()

# Schedule publish
post.publish(schedule=datetime.now() + timedelta(days=1))

# Update workflow status
post.update_workflow_status("REVIEW", user_id=1)
```

## Common Queries

### Get Published Posts
```sql
SELECT * FROM post 
WHERE is_published = true 
  AND is_deleted = false 
  AND (publish_date IS NULL OR publish_date <= NOW())
  AND (unpublish_date IS NULL OR unpublish_date > NOW())
ORDER BY published_at DESC;
```

### Get Posts by Category
```sql
SELECT p.* FROM post p
JOIN post_categories pc ON p.id = pc.post_id
WHERE pc.category_id = :category_id
  AND p.is_published = true
  AND p.is_deleted = false;
```

### Get Post with Sections
```sql
SELECT p.*, s.* 
FROM post p
LEFT JOIN post_section s ON p.id = s.post_id
WHERE p.slug = :slug
  AND p.is_deleted = false
ORDER BY s.position;
```

## Best Practices

### Content Management
1. Always use the `add_section()` method to maintain proper section ordering
2. Use `duplicate()` for creating templates or variations
3. Validate slugs for uniqueness before saving
4. Keep SEO fields within length limits

### Workflow
1. Use `update_workflow_status()` to maintain history
2. Check workflow stage requirements before transitions
3. Use scheduling methods for timed publications
4. Validate workflow status changes

### Performance
1. Use eager loading for sections when needed
2. Index on commonly queried fields (slug, publish_date)
3. Use soft deletes instead of hard deletes
4. Cache frequently accessed posts

## Security Considerations
1. Validate user permissions for workflow changes
2. Sanitize HTML content
3. Validate external URLs
4. Protect draft posts from unauthorized access 