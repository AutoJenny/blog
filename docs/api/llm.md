# LLM Integration API

## Overview
The LLM Integration API provides endpoints for content generation, text analysis, and prompt management using Language Models (LLMs).

## Content Generation

### Generate Content
```http
POST /api/v1/llm/generate
```

#### Request Body
```json
{
  "prompt": "Write a blog post about AI",
  "model": "gpt-4",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 1.0
  },
  "format": "markdown",
  "metadata": {
    "purpose": "blog_post",
    "target_audience": "technical"
  }
}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "content": "# Understanding AI\n\nArtificial Intelligence...",
    "metadata": {
      "tokens": {
        "prompt": 10,
        "completion": 850,
        "total": 860
      },
      "model": "gpt-4",
      "finish_reason": "stop"
    }
  }
}
```

### Generate Variations
```http
POST /api/v1/llm/variations
```

#### Request Body
```json
{
  "content": "Original content here",
  "count": 3,
  "parameters": {
    "temperature": 0.8,
    "creativity": "high"
  },
  "constraints": {
    "tone": "professional",
    "length": "similar"
  }
}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "variations": [
      {
        "content": "First variation...",
        "similarity_score": 0.85
      },
      {
        "content": "Second variation...",
        "similarity_score": 0.78
      },
      {
        "content": "Third variation...",
        "similarity_score": 0.92
      }
    ],
    "metadata": {
      "model": "gpt-4",
      "total_tokens": 2500
    }
  }
}
```

## Text Analysis

### Analyze Content
```http
POST /api/v1/llm/analyze
```

#### Request Body
```json
{
  "content": "Content to analyze",
  "analyses": [
    "sentiment",
    "readability",
    "keywords",
    "topics"
  ],
  "parameters": {
    "detail_level": "high",
    "format": "structured"
  }
}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "sentiment": {
      "score": 0.8,
      "label": "positive",
      "confidence": 0.92
    },
    "readability": {
      "grade_level": 12,
      "scores": {
        "flesch_kincaid": 65,
        "gunning_fog": 14
      }
    },
    "keywords": [
      {
        "term": "artificial intelligence",
        "relevance": 0.95
      }
    ],
    "topics": [
      {
        "name": "Technology",
        "confidence": 0.88
      }
    ]
  }
}
```

### Optimize Content
```http
POST /api/v1/llm/optimize
```

#### Request Body
```json
{
  "content": "Content to optimize",
  "targets": {
    "seo": true,
    "readability": true,
    "engagement": true
  },
  "constraints": {
    "max_length": 1000,
    "tone": "professional",
    "keywords": ["AI", "machine learning"]
  }
}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "optimized_content": "Optimized version...",
    "improvements": {
      "seo": {
        "score": 85,
        "changes": ["Added keywords", "Improved headings"]
      },
      "readability": {
        "score": 75,
        "changes": ["Simplified sentences", "Added subheadings"]
      }
    }
  }
}
```

## Prompt Management

### List Prompts
```http
GET /api/v1/llm/prompts
```

#### Response
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Blog Post Generator",
      "template": "Write a blog post about {{topic}}...",
      "parameters": {
        "temperature": 0.7,
        "max_tokens": 1000
      },
      "metadata": {
        "purpose": "content_generation",
        "version": 1
      },
      "created_at": "2025-04-23T15:34:10Z"
    }
  ]
}
```

### Create Prompt
```http
POST /api/v1/llm/prompts
```

#### Request Body
```json
{
  "name": "SEO Title Generator",
  "template": "Generate an SEO-friendly title for: {{content}}",
  "parameters": {
    "temperature": 0.5,
    "max_tokens": 50
  },
  "metadata": {
    "purpose": "seo_optimization",
    "target_length": "60-70 chars"
  }
}
```

### Update Prompt
```http
PUT /api/v1/llm/prompts/{id}
```

#### Request Body
```json
{
  "template": "Updated template text...",
  "parameters": {
    "temperature": 0.6
  }
}
```

## Batch Operations

### Batch Generate
```http
POST /api/v1/llm/batch/generate
```

#### Request Body
```json
{
  "items": [
    {
      "prompt": "First prompt",
      "parameters": {}
    },
    {
      "prompt": "Second prompt",
      "parameters": {}
    }
  ],
  "common_parameters": {
    "model": "gpt-4",
    "temperature": 0.7
  }
}
```

### Batch Analyze
```http
POST /api/v1/llm/batch/analyze
```

#### Request Body
```json
{
  "items": [
    {
      "content": "First content",
      "analyses": ["sentiment"]
    },
    {
      "content": "Second content",
      "analyses": ["readability"]
    }
  ]
}
```

## Error Responses

### Generation Error
```json
{
  "status": "error",
  "error": {
    "code": "GENERATION_ERROR",
    "message": "Content generation failed",
    "details": {
      "reason": "Token limit exceeded",
      "limit": 1000
    }
  }
}
```

### Analysis Error
```json
{
  "status": "error",
  "error": {
    "code": "ANALYSIS_ERROR",
    "message": "Content analysis failed",
    "details": {
      "analysis": "sentiment",
      "reason": "Invalid content format"
    }
  }
}
```

## Best Practices

### Content Generation
1. Use appropriate temperature
2. Set reasonable token limits
3. Include clear constraints
4. Handle timeouts

### Prompt Management
1. Version prompts
2. Test variations
3. Monitor performance
4. Document usage

### Analysis
1. Validate input
2. Handle edge cases
3. Cache results
4. Track accuracy

### Performance
1. Use async processing
2. Implement retries
3. Cache responses
4. Monitor usage

## Usage Examples

### Generate Content
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Write a blog post", "model": "gpt-4"}' \
     https://api.blog.com/v1/llm/generate
```

### Analyze Content
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"content": "Text to analyze", "analyses": ["sentiment"]}' \
     https://api.blog.com/v1/llm/analyze
```

### Create Prompt
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Title Generator", "template": "Generate title: {{content}}"}' \
     https://api.blog.com/v1/llm/prompts
``` 