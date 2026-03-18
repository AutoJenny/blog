# Blog Launchpad Microservice

**Microservice that provides preview and publishing functionality, designed to be embedded as an iframe within the main workflow interface.**

## ⚠️ CRITICAL: Iframe-Based Architecture

**This service is designed to work ONLY when embedded as an iframe within the main workflow interface:**

- **Main Workflow URL**: `http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`
- **Iframe Embedding**: The main workflow embeds this service as an iframe with URL parameters
- **Required Parameters**: `stage`, `substage`, `step`, `post_id`
- **Direct Access**: Accessing `http://localhost:5001` directly will fail with missing parameters

### How It Works

1. **Main Workflow** (`http://localhost:5000/workflow/posts/1/planning/idea/initial_concept`) loads
2. **blog-core** embeds this service as an iframe with proper URL parameters when needed
3. **This service** receives context from URL parameters and initializes properly
4. **Direct access** to `http://localhost:5001` will fail because no parameters are provided

### Testing

**✅ CORRECT WAY TO TEST:**
```
http://localhost:5000/workflow/posts/1/planning/idea/initial_concept
```

**❌ INCORRECT WAY TO TEST:**
```
http://localhost:5001
```

## Overview

The blog-launchpad microservice provides preview and publishing functionality for the blog system. It handles post previews, publishing workflows, and content management operations.

## Features

- **Post Preview**: Live preview of posts before publishing
- **Publishing Workflow**: Manage the publishing process
- **Content Management**: Handle content operations and workflows
- **Integration**: Works with other microservices for complete functionality

## Port

**Port 5001**

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the service:
   ```bash
   python app.py
   ```

## Integration

This service integrates with:
- **blog-core**: Main workflow orchestrator
- **blog-llm-actions**: LLM processing capabilities
- **blog-post-sections**: Section content management
- **blog-post-info**: Post metadata management
- **blog-images**: Image generation and processing 