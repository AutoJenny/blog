# Blog Post Sections Microservice

**Microservice that powers the green Sections panel, designed to be embedded as an iframe within the main workflow interface.**

## ⚠️ CRITICAL: Iframe-Based Architecture

**This service is designed to work ONLY when embedded as an iframe within the main workflow interface:**

- **Main Workflow URL**: `http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`
- **Iframe Embedding**: The main workflow embeds this service as an iframe with URL parameters
- **Required Parameters**: `stage`, `substage`, `step`, `post_id`
- **Direct Access**: Accessing `http://localhost:5003` directly will fail with missing parameters

### How It Works

1. **Main Workflow** (`http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`) loads
2. **blog-core** embeds this service as an iframe with proper URL parameters:
   ```
   http://localhost:5003/sections?stage=planning&substage=idea&step=initial_concept&post_id=1
   ```
3. **This service** receives context from URL parameters and initializes properly
4. **Direct access** to `http://localhost:5003` will fail because no parameters are provided

### Testing

**✅ CORRECT WAY TO TEST:**
```
http://localhost:5000/workflow/posts/1/planning/idea/initial_concept
```

**❌ INCORRECT WAY TO TEST:**
```
http://localhost:5003
```

This microservice powers the green Sections panel in the writing stage of BlogForge when properly embedded.

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```

The service will be available at http://localhost:5003/

## Development
- Edit `templates/index.html` for the UI.
- Add Flask routes and logic in `app.py`.

## Integration
- This service is embedded in blog-core (port 5001) as an iframe in the writing stage. 