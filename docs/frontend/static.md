# Static Assets

Static files are served from `app/static/` and include CSS, JS, and images.

## Directory Structure
- `app/static/css/`: All CSS files (Tailwind, admin, custom)
- `app/static/js/`: JavaScript files
- `app/static/images/`: Images for posts, site, and watermarked versions
- `app/static/uploads/`: User-uploaded files
- `app/static/comfyui_output/`: Output from ComfyUI (if used)
- `app/static/cache/`: Cached files

## Adding New Assets
- Place new CSS/JS/images in the appropriate subdirectory
- Reference in templates using `url_for('static', filename='<path>')`

## Notes
- Tailwind CSS is built from `src/main.css` to `dist/main.css`
- Keep static assets organized for maintainability 