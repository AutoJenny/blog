# PostSection Model Documentation

## Overview
The `PostSection` model represents a discrete content section within a blog post. It enables modular content management, allowing posts to be broken down into reusable, independently manageable sections that can be individually styled, edited, and reordered.

## Schema

### Core Fields
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Primary key | NOT NULL, AUTO INCREMENT |
| post_id | Integer | Reference to Post | NOT NULL, FOREIGN KEY |
| content | Text | Section content | NOT NULL |
| position | Integer | Order within post | NOT NULL |
| content_type | String(50) | Content format type | NOT NULL, DEFAULT 'markdown' |
| created_at | DateTime | Creation timestamp | NOT NULL, DEFAULT now() |
| updated_at | DateTime | Last update timestamp | NOT NULL, DEFAULT now() |
| is_deleted | Boolean | Soft delete flag | NOT NULL, DEFAULT false |

### Metadata Fields
| Field | Type | Description |
|-------|------|-------------|
| title | String(140) | Optional section title |
| subtitle | String(140) | Optional section subtitle |
| style_class | String(50) | CSS class for styling |
| template_id | Integer | Reference to template |
| version | Integer | Content version number |

### Content-Specific Fields
| Field | Type | Description |
|-------|------|-------------|
| raw_content | Text | Original unprocessed content |
| rendered_content | Text | Processed/rendered content |
| metadata | JSONB | Additional content metadata |
| llm_context | JSONB | LLM processing context |

## Relationships

### Many-to-One
- `post`: Post
- `template`: SectionTemplate
- `creator`: User

### One-to-Many
- `revisions`: List of SectionRevision
- `llm_interactions`: List of LLMInteraction

## Methods

### Content Management
```python
def update_content(self, content: str, user_id: int) -> None:
    """Update section content and create revision."""

def render_content(self) -> str:
    """Process and render content based on content_type."""

def revert_to_revision(self, revision_id: int) -> None:
    """Revert content to specific revision."""
```

### Position Management
```python
def move_to(self, new_position: int) -> None:
    """Move section to new position."""

@classmethod
def reorder_sections(cls, post_id: int, section_ids: List[int]) -> None:
    """Reorder multiple sections within a post."""
```

### Template Management
```python
def apply_template(self, template_id: int) -> None:
    """Apply section template."""

def save_as_template(self, name: str, description: str = None) -> 'SectionTemplate':
    """Create new template from section."""
```

### LLM Integration
```python
def process_with_llm(self, prompt: str) -> None:
    """Process section content with LLM."""

def generate_variations(self, count: int = 3) -> List['PostSection']:
    """Generate content variations using LLM."""
```

## Usage Examples

### Creating a Section
```python
section = PostSection(
    post_id=post.id,
    content="# Introduction\nWelcome to my post.",
    position=1,
    content_type='markdown'
)
db.session.add(section)
db.session.commit()
```

### Updating Content
```python
section.update_content(
    content="# Updated Introduction\nNew content here.",
    user_id=current_user.id
)
db.session.commit()
```

### Managing Position
```python
# Move single section
section.move_to(3)

# Reorder multiple sections
PostSection.reorder_sections(
    post_id=1,
    section_ids=[3, 1, 4, 2]
)
```

## Common Queries

### Get Sections by Post
```sql
SELECT * FROM post_section
WHERE post_id = :post_id
  AND is_deleted = false
ORDER BY position;
```

### Get Section with History
```sql
SELECT s.*, r.*
FROM post_section s
LEFT JOIN section_revision r ON s.id = r.section_id
WHERE s.id = :section_id
ORDER BY r.created_at DESC;
```

### Get Template Usage
```sql
SELECT p.title, s.*
FROM post_section s
JOIN post p ON s.post_id = p.id
WHERE s.template_id = :template_id
  AND s.is_deleted = false;
```

## Best Practices

### Content Management
1. Always use `update_content()` to maintain revision history
2. Validate content format against content_type
3. Process content through appropriate renderer
4. Keep raw and rendered content in sync

### Position Management
1. Use provided methods for position changes
2. Validate position ranges
3. Handle position conflicts
4. Maintain continuous position sequence

### Template Usage
1. Validate template compatibility
2. Update template references
3. Track template usage
4. Version template changes

### Performance
1. Lazy load revisions
2. Cache rendered content
3. Batch position updates
4. Index frequently queried fields

## Security Considerations
1. Sanitize HTML content
2. Validate content_type values
3. Check template permissions
4. Protect revision history
5. Validate position changes
6. Sanitize metadata input 