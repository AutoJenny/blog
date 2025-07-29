# DALL-E Image Generation Scripts

This directory contains scripts for generating images using DALL-E 3 and saving them to the blog-images directory structure.

## Files

- `generate_dalle_image.py` - Main script for generating DALL-E images
- `example_usage.py` - Example script showing how to use the main script
- `README.md` - This documentation file

## Prerequisites

1. **OpenAI API Key**: You need a valid OpenAI API key with DALL-E 3 access
2. **Python Dependencies**: 
   - `openai` (version 1.97.1+)
   - `requests`
   - `pathlib`

## Setup

1. **Set your API key** (choose one method):
   ```bash
   # Method 1: Environment variable (recommended)
   export OPENAI_AUTH_TOKEN="your-api-key-here"
   
   # Method 2: Pass as command line argument (see usage below)
   ```

2. **Install dependencies**:
   ```bash
   pip install openai requests
   ```

## Usage

### Basic Usage

```bash
python generate_dalle_image.py \
  --prompt "Your image generation prompt here" \
  --post-id 53 \
  --section-id 1
```

### Advanced Usage

```bash
python generate_dalle_image.py \
  --prompt "STYLE: Digital art, vibrant colors. SUBJECT: A futuristic cityscape." \
  --post-id 53 \
  --section-id 2 \
  --filename "my_custom_image" \
  --size "1024x1024" \
  --api-key "your-api-key-here"
```

### Parameters

- `--prompt` (required): The image generation prompt
- `--post-id` (required): The blog post ID
- `--section-id` (required): The section ID within the post
- `--api-key` (optional): OpenAI API key (if not set via environment variable)
- `--size` (optional): Image size (default: "1792x1024")
- `--filename` (optional): Custom filename without extension

### Supported Image Sizes

- `1024x1024` (square)
- `1024x1792` (portrait)
- `1792x1024` (landscape) - default

## Output Structure

Images are saved to:
```
/Users/nickfiddes/Code/projects/blog/blog-images/static/content/posts/{post_id}/sections/{section_id}/raw/
```

### Generated Files

1. **Image file**: `dalle_generated_YYYYMMDD_HHMMSS.png` (or custom filename)
2. **Metadata file**: `dalle_generated_YYYYMMDD_HHMMSS_metadata.json`

### Metadata Structure

```json
{
  "post_id": 53,
  "section_id": 1,
  "prompt": "Your original prompt",
  "image_path": "/full/path/to/image.png",
  "generated_at": "2025-07-29T11:20:27.123456",
  "model": "dall-e-3",
  "size": "1792x1024"
}
```

## Examples

### Example 1: Scottish Living Room
```bash
python generate_dalle_image.py \
  --prompt "STYLE: Produce an image in a loose and airy pen & ink wash style, in 1792x1024 landscape orientation. The colouring schema must be colourful but washed out, and the image should 'fade' to pure white on all sides. SUBJECT: A cozy modern Scottish living room, fireplace ablaze with crackling logs, casting a warm, gentle glow." \
  --post-id 53 \
  --section-id 1
```

### Example 2: Futuristic Cityscape
```bash
python generate_dalle_image.py \
  --prompt "STYLE: Digital art, vibrant colors, modern illustration. SUBJECT: A futuristic cityscape with flying cars and neon lights, viewed from above." \
  --post-id 53 \
  --section-id 2 \
  --filename "futuristic_cityscape"
```

## Error Handling

The script includes comprehensive error handling for:
- Missing API key
- Invalid API key
- Network issues
- File system errors
- DALL-E API errors

## Security Notes

- Never commit API keys to version control
- Use environment variables for API keys in production
- The script validates API keys before making requests

## Troubleshooting

### Common Issues

1. **"OpenAI API key required"**: Set the `OPENAI_AUTH_TOKEN` environment variable
2. **"Client.__init__() got an unexpected keyword argument 'proxies'"**: Update your OpenAI library: `pip install --upgrade openai`
3. **"Invalid value for size"**: Use one of the supported sizes listed above
4. **"Permission denied"**: Make sure the script is executable: `chmod +x generate_dalle_image.py`

### Getting Help

Check the script output for detailed error messages. The script provides verbose logging to help diagnose issues.