# Blog Core

**Main orchestrator service that embeds microservices as iframes within workflow pages.**

## ⚠️ CRITICAL: Iframe-Based Architecture

This is the **main orchestrator service** that serves workflow pages and embeds microservices as iframes:

- **Main Workflow URL**: `http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`
- **Iframe Embedding**: Embeds blog-llm-actions (port 5002) and blog-post-sections (port 5003) as iframes
- **URL Parameter Passing**: Passes `stage`, `substage`, `step`, `post_id`, `step_id` to embedded services
- **Cross-Service Communication**: Manages communication between embedded iframes

### How It Works

1. **User accesses**: `http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`
2. **blog-core** renders workflow.html with iframe embeddings:
   - **LLM Actions iframe**: `http://localhost:5002/?stage=planning&substage=idea&step=initial_concept&post_id=1&step_id=41`
   - **Sections iframe**: `http://localhost:5003/sections?stage=planning&substage=idea&step=initial_concept&post_id=1`
3. **Microservices** receive context from URL parameters and initialize properly
4. **Cross-iframe communication** enables coordinated functionality

### Testing

**✅ CORRECT WAY TO TEST THE SYSTEM:**
```
http://localhost:5000/workflow/posts/1/planning/idea/initial_concept
```

**❌ DO NOT TEST MICROSERVICES DIRECTLY:**
- `http://localhost:5002` (will fail - missing parameters)
- `http://localhost:5003` (will fail - missing parameters)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the Flask development server:
```bash
python app.py
```

The application will be available at:
- Main page: http://localhost:5000
- Health check: http://localhost:5000/health

## Project Structure

```
blog-core/
├── app.py              # Main Flask application
├── templates/
│   └── test.html      # Test page template
├── requirements.txt    # Python dependencies
└── README.md          # This file
``` 