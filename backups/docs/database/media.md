# Media Model Documentation

## Overview
The `Media` model manages all media assets in the blog system, with a focus on image handling, watermarking support, and metadata management. It provides centralized storage and processing for images used in blog posts, headers, and other content areas.

## Schema

### Core Fields
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | Integer | Primary key | NOT NULL, AUTO INCREMENT |
| filename | String(255) | Original filename | NOT NULL |
| filepath | String(255) | Storage path | NOT NULL, UNIQUE |
| mimetype | String(100) | Media type | NOT NULL |
| size | Integer | File size in bytes | NOT NULL |
| created_at | DateTime | Creation timestamp | NOT NULL, DEFAULT now() |
| updated_at | DateTime | Last update timestamp | NOT NULL, DEFAULT now() |
| is_deleted | Boolean | Soft delete flag | NOT NULL, DEFAULT false |

### Image-Specific Fields
| Field | Type | Description |
|-------|------|-------------|
| width | Integer | Image width in pixels |
| height | Integer | Image height in pixels |
| format | String(20) | Image format (jpg, png, etc.) |
| has_watermark | Boolean | Watermark status |
| watermark_path | String(255) | Path to watermarked version |

### Metadata Fields
| Field | Type | Description |
|-------|------|-------------|
| title | String(140) | Display title |
| alt_text | String(255) | Accessibility text |
| caption | Text | Image caption |
| credit | String(255) | Attribution/credit |
| exif_data | JSONB | Technical image metadata |
| ai_metadata | JSONB | AI generation metadata |

## Relationships

### One-to-Many
- `post_headers`: List of Post (as header image)
- `post_sections`: List of PostSection
- `watermark_versions`: List of MediaVersion

### Many-to-One
- `uploader`: User
- `original`: Media (for derived versions)

## Methods

### File Management
```python
def save_file(self, file_obj) -> bool:
    """Save uploaded file to storage."""

def delete_file(self) -> bool:
    """Remove file from storage."""

def get_url(self, size: str = None) -> str:
    """Get URL for media access."""
```

### Image Processing
```python
def add_watermark(self, watermark_text: str = None) -> 'Media':
    """Create watermarked version."""

def resize(self, width: int, height: int = None) -> 'Media':
    """Create resized version."""

def optimize(self, quality: int = 85) -> bool:
    """Optimize image for web."""
```

### Metadata Management
```python
def extract_exif(self) -> Dict:
    """Extract EXIF data from image."""

def update_metadata(self, metadata: Dict) -> None:
    """Update media metadata."""

def to_dict(self) -> Dict:
    """Convert to dictionary representation."""
```

## Usage Examples

### Uploading Media
```python
media = Media(
    filename="example.jpg",
    mimetype="image/jpeg"
)
media.save_file(file_obj)
db.session.add(media)
db.session.commit()
```

### Processing Images
```python
# Create watermarked version
watermarked = media.add_watermark("© My Blog 2025")

# Create thumbnail
thumbnail = media.resize(width=300)

# Optimize for web
media.optimize(quality=85)
```

### Managing Metadata
```python
# Extract EXIF data
exif = media.extract_exif()

# Update metadata
media.update_metadata({
    'title': 'Sunset Photo',
    'alt_text': 'Beautiful sunset over mountains',
    'credit': 'John Doe'
})
```

## Common Queries

### Get Images by Type
```sql
SELECT * FROM media
WHERE mimetype LIKE 'image/%'
  AND is_deleted = false
ORDER BY created_at DESC;
```

### Get Post Images
```sql
SELECT m.* FROM media m
JOIN post_section ps ON ps.media_id = m.id
WHERE ps.post_id = :post_id
  AND m.is_deleted = false;
```

### Get Watermarked Versions
```sql
SELECT m.* FROM media m
WHERE m.original_id = :media_id
  AND m.has_watermark = true
  AND m.is_deleted = false;
```

## Best Practices

### File Management
1. Use secure filenames
2. Validate file types
3. Handle storage errors
4. Implement file cleanup

### Image Processing
1. Preserve original files
2. Cache processed versions
3. Use appropriate compression
4. Handle large files efficiently

### Metadata
1. Validate metadata format
2. Preserve EXIF data
3. Handle missing metadata
4. Update timestamps

### Performance
1. Use async processing for large files
2. Implement caching
3. Optimize storage paths
4. Clean up unused files

## Security Considerations
1. Validate file types
2. Sanitize filenames
3. Check file size limits
4. Protect original files
5. Secure metadata storage
6. Control access permissions 