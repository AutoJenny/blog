# DALL-E Integration Quick Reference

## Quick Start

### 1. Set API Key
```bash
export OPENAI_AUTH_TOKEN="your-api-key-here"
```

### 2. Basic Image Generation
```bash
python scripts/generate_dalle_image.py \
  --prompt "Your prompt here" \
  --post-id 53 \
  --section-id 1
```

### 3. Custom Filename
```bash
python scripts/generate_dalle_image.py \
  --prompt "Your prompt here" \
  --post-id 53 \
  --section-id 1 \
  --filename "my_custom_image"
```

## Common Commands

### Generate Landscape Image (Default)
```bash
python scripts/generate_dalle_image.py \
  --prompt "STYLE: Digital art. SUBJECT: Futuristic cityscape." \
  --post-id 53 \
  --section-id 1
```

### Generate Square Image
```bash
python scripts/generate_dalle_image.py \
  --prompt "STYLE: Watercolor. SUBJECT: Mountain landscape." \
  --post-id 53 \
  --section-id 2 \
  --size "1024x1024"
```

### Generate Portrait Image
```bash
python scripts/generate_dalle_image.py \
  --prompt "STYLE: Oil painting. SUBJECT: Portrait of a person." \
  --post-id 53 \
  --section-id 3 \
  --size "1024x1792"
```

### Use Explicit API Key
```bash
python scripts/generate_dalle_image.py \
  --prompt "Your prompt here" \
  --post-id 53 \
  --section-id 1 \
  --api-key "your-api-key-here"
```

## Prompt Templates

### Scottish Theme
```bash
--prompt "STYLE: Produce an image in a loose and airy pen & ink wash style, in 1792x1024 landscape orientation. The colouring schema must be colourful but washed out, and the image should 'fade' to pure white on all sides. SUBJECT: A cozy modern Scottish living room, fireplace ablaze with crackling logs, casting a warm, gentle glow."
```

### Digital Art
```bash
--prompt "STYLE: Digital art, vibrant colors, modern illustration. SUBJECT: A futuristic cityscape with flying cars and neon lights, viewed from above."
```

### Watercolor
```bash
--prompt "STYLE: Watercolor painting, soft pastels, gentle brushstrokes. SUBJECT: A serene mountain lake at sunset with reflections."
```

### Minimalist
```bash
--prompt "STYLE: Minimalist design, clean lines, simple shapes. SUBJECT: A red circle on a white background."
```

## Output Locations

### Default Structure
```
/Users/nickfiddes/Code/projects/blog/blog-images/static/content/posts/{post_id}/sections/{section_id}/raw/
```

### Example Paths
- Post 53, Section 1: `posts/53/sections/1/raw/`
- Post 53, Section 2: `posts/53/sections/2/raw/`
- Post 100, Section 5: `posts/100/sections/5/raw/`

## File Naming

### Auto-Generated Names
- Format: `dalle_generated_YYYYMMDD_HHMMSS.png`
- Example: `dalle_generated_20250729_132646.png`

### Custom Names
- Format: `{filename}.png`
- Example: `my_custom_image.png`

## Metadata Files

### Auto-Generated Metadata
- Format: `dalle_generated_YYYYMMDD_HHMMSS_metadata.json`
- Contains: prompt, timestamps, model info, file paths

### Custom Metadata
- Format: `{filename}_metadata.json`
- Example: `my_custom_image_metadata.json`

## Error Messages

### Common Issues & Solutions

| Error | Solution |
|-------|----------|
| "OpenAI API key required" | Set `export OPENAI_AUTH_TOKEN="your-key"` |
| "Client.__init__() got unexpected keyword argument 'proxies'" | Run `pip install --upgrade openai` |
| "Invalid value for size" | Use: `1024x1024`, `1024x1792`, or `1792x1024` |
| "Permission denied" | Run `chmod +x scripts/generate_dalle_image.py` |

## Size Reference

| Size | Aspect Ratio | Use Case |
|------|--------------|----------|
| `1024x1024` | 1:1 (Square) | Profile pictures, icons, thumbnails |
| `1024x1792` | 3:5 (Portrait) | Mobile screens, tall images |
| `1792x1024` | 7:4 (Landscape) | Desktop screens, wide images |

## Script Location

```
/Users/nickfiddes/Code/projects/blog/blog-images/scripts/generate_dalle_image.py
```

## Help Command

```bash
python scripts/generate_dalle_image.py --help
```

## Example Usage Script

```bash
python scripts/example_usage.py
```

---

*Quick Reference - Last Updated: 2025-07-29*