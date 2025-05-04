# LLM Integration Guide

This document outlines the LangChain integration in our blog content management system, which provides AI-assisted content creation and enhancement capabilities.

## Overview

The system uses LangChain to provide AI assistance in content creation, primarily focusing on:
- Content enhancement and refinement
- SEO optimization
- Metadata generation
- Social media content creation

## Architecture

### Core Components

1. **LLMService** (`app/services/llm_service.py`)
   - Main service class for LLM operations
   - Handles interactions with OpenAI via LangChain
   - Manages prompt execution and response processing
   ```python
   llm_service = LLMService()
   summary = llm_service.generate_post_summary(post_id)
   tags = llm_service.suggest_tags(post_id)
   ```

2. **Provider System** (`app/llm/`)
   - Flexible provider architecture supporting multiple LLM backends
   - OpenAI integration through LangChain
   - Local model support via Ollama
   - Factory pattern for provider management

3. **Prompt Management** (`app/models.py`)
   - `LLMPrompt`: Database model for storing prompt templates
   - `LLMInteraction`: Tracks all LLM interactions
   - Template-based system for dynamic prompt generation

### Key Features

1. **Content Enhancement**
   ```python
   # Available methods
   generate_post_summary(post_id, max_length=200)
   suggest_tags(post_id, max_tags=5)
   enhance_seo(post_id)
   improve_readability(post_id)
   generate_social_media_content(post_id, platform)
   ```

2. **Metadata Generation**
   - Title optimization
   - SEO description generation
   - Keyword extraction
   - Scottish/Celtic heritage focus

3. **Performance Monitoring**
   - Token usage tracking
   - Response time monitoring
   - Error logging
   - Usage analytics

## Configuration

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=your-api-key
OPENAI_ORG_ID=your-org-id  # Optional
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_DEFAULT_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# LLM Settings
LLM_PROVIDER_TYPE=openai  # or 'ollama'
LLM_MODEL_NAME=gpt-3.5-turbo  # or local model name
LLM_API_BASE=  # Optional: custom API endpoint
```

## Usage Examples

### 1. Generating Post Summary
```python
from app.services.llm_service import LLMService

llm_service = LLMService()
summary = llm_service.generate_post_summary(post_id, max_length=200)
```

### 2. SEO Enhancement
```python
seo_improvements = llm_service.enhance_seo(post_id)
# Returns suggestions for title, meta description, and keywords
```

### 3. Content Improvement
```python
readability_changes = llm_service.improve_readability(post_id)
# Returns suggested improvements for clarity and engagement
```

### 4. Social Media Content
```python
twitter_content = llm_service.generate_social_media_content(post_id, 'twitter')
facebook_content = llm_service.generate_social_media_content(post_id, 'facebook')
```

## Monitoring and Analytics

The system tracks all LLM interactions in the database:
- Prompt used
- Input/output text
- Token usage
- Response time
- Model details

Query example:
```python
from app.models import LLMInteraction

# Get recent interactions
recent = LLMInteraction.query.order_by(LLMInteraction.created_at.desc()).limit(10).all()

# Get token usage by prompt type
token_usage = db.session.query(
    LLMPrompt.name,
    func.sum(LLMInteraction.tokens_used)
).join(LLMPrompt).group_by(LLMPrompt.name).all()
```

## Best Practices

1. **Prompt Management**
   - Keep prompts in database for easy updates
   - Use templating for dynamic content
   - Include specific instructions for Scottish/Celtic context

2. **Error Handling**
   - All LLM calls are wrapped in try-except blocks
   - Failed interactions are logged but don't break the application
   - Fallback options are provided where possible

3. **Performance**
   - Use appropriate token limits for each task
   - Cache frequently used results
   - Monitor token usage and costs

4. **Content Quality**
   - Review AI-generated content before publishing
   - Use AI suggestions as enhancements, not replacements
   - Maintain brand voice and style guidelines

## Extending the System

### Adding New Providers
1. Create new provider class inheriting from `LLMProvider`
2. Implement required methods
3. Register provider in `LLMFactory`

### Creating New Features
1. Add new prompt template to database
2. Create method in `LLMService`
3. Add corresponding API endpoint if needed

### Custom Prompts
1. Create new `LLMPrompt` record
2. Define template with variables
3. Add processing method in service layer 