# Tailwind CSS Integration

Tailwind CSS is used for all modern styling in the Blog CMS. This document covers setup, usage, and troubleshooting.

## Setup
- Tailwind config: `tailwind.config.js`
- Source CSS: `app/static/css/src/main.css`
- Output CSS: `app/static/css/dist/main.css`
- Referenced in templates via `<link href="{{ url_for('static', filename='css/dist/main.css') }}" rel="stylesheet">`

## Build Commands
- **Build once:**
  ```bash
  npx tailwindcss -i ./app/static/css/src/main.css -o ./app/static/css/dist/main.css --minify
  ```
- **Watch for changes:**
  ```bash
  npx tailwindcss -i ./app/static/css/src/main.css -o ./app/static/css/dist/main.css --watch
  ```
- These commands are also in `package.json` as `build:css` and `watch:css` scripts.

## Customization
- Custom colors and themes are defined in `tailwind.config.js`.
- Use `@apply` in `main.css` for reusable component styles.

## Troubleshooting
- If styles do not appear, ensure the output CSS is up to date and referenced correctly.
- Rebuild the CSS if you change Tailwind config or source files.
- Check browser cache (hard refresh) if changes are not visible.
- For errors, check the terminal output when running build commands.

## Further Reading
- [Tailwind CSS Documentation](https://tailwindcss.com/docs) 