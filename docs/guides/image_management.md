# Image Management Guide

## Image Organization

### Directory Structure
```
app/
  static/
    images/
      posts/
        <post-slug>/
          <post-slug>_header.jpg
          <post-slug>_<section-title>.jpg
```

### Naming Conventions
1. **Header Images**
   - Format: `<post-slug>_header.jpg` or `<post-slug>_header-collage.jpg`
   - Example: `kilt-evolution_header.jpg`

2. **Section Images**
   - Format: `<post-slug>_<section-title-slug>.jpg`
   - Example: `kilt-evolution_early-origins.jpg`
   - Rules:
     - Convert to lowercase
     - Replace spaces with hyphens
     - Remove special characters
     - Keep it descriptive but concise

## Image Processing

### Adding Images to a Post
1. Place images in the correct directory:
   ```bash
   mkdir -p app/static/images/posts/<post-slug>
   cp your-image.jpg app/static/images/posts/<post-slug>/<post-slug>_header.jpg
   ```

2. Run the check_images script:
   ```bash
   python check_images.py
   ```

### Updating Section Images
1. Ensure images follow naming convention
2. Run the update script:
   ```bash
   python update_section_images.py
   ```

## Image Requirements

### File Formats
- Preferred: JPEG (.jpg)
- Supported: PNG (.png)
- Maximum size: 5MB

### Dimensions
- Header images: 1200x630px (recommended)
- Section images: 800x600px (minimum)
- Maintain aspect ratio

### Optimization
1. Compress images before upload
2. Use appropriate quality settings:
   - JPEG: 80-90% quality
   - PNG: Use for images requiring transparency

## Troubleshooting

### Common Issues
1. **Images Not Displaying**
   - Check file permissions
   - Verify file exists in correct location
   - Ensure naming convention is followed
   - Run `check_images.py`

2. **Wrong Image Associations**
   - Check section title matches filename
   - Run `update_section_images.py`
   - Verify database entries

3. **Missing Header Images**
   - Ensure first image in post's collection
   - Check file naming
   - Run `check_images.py`

### Maintenance
1. Regular checks:
   ```bash
   python check_images.py
   ```

2. Clean unused images:
   ```bash
   # TODO: Add cleanup script
   ```

## Best Practices
1. Use descriptive filenames
2. Optimize before uploading
3. Keep consistent dimensions
4. Regular maintenance
5. Back up image directories

## Scripts Reference

### check_images.py
Verifies and fixes image associations:
- Creates missing Image records
- Sets header images
- Links section images

### update_section_images.py
Maps section titles to images:
- Updates section-image relationships
- Maintains consistent naming
- Fixes broken associations 