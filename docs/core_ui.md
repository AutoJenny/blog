# Core UI Templates

## Overview
The Core UI templates provide a consistent structure for the application's user interface. They include a base template and an index template.

## Base Template (`app/templates/core/base.html`)
- **Purpose**: Serves as the foundation for all Core UI pages.
- **Structure**:
  - Common HTML elements (head, body, header, footer).
  - Navigation and footer placeholders.
  - Content block for page-specific content.
- **Usage**: Extend this template in other templates to maintain a consistent layout.

## Index Template (`app/templates/core/index.html`)
- **Purpose**: Displays the welcome page for the Core UI.
- **Structure**:
  - Extends the base template.
  - Includes a title and welcome message.
- **Usage**: Accessible via the `/core` route.

## Testing
- The templates have been tested and verified to render correctly.
- The `/core` route displays the expected content. 