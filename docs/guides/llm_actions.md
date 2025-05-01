# LLM Actions Guide

## Overview

The LLM Actions system allows you to define reusable content generation actions that use LLMs (Language Model Models) to process content from one field and generate content for another field. Each action is configured with:

- Source field (where to get input from)
- Prompt template (how to process the input)
- LLM model (which model to use)
- Model parameters (temperature, max tokens)

## Creating an Action

1. Go to the LLM Actions page (`/llm/actions`)
2. Click "New Action"
3. Fill in the form:
   - Field Name: The destination field where the output will go
   - Source Field: Select from available workflow fields
   - Prompt Template: Select from existing templates
   - LLM Model: Choose the model to use
   - Temperature: Set creativity level (0.0-2.0)
   - Max Tokens: Set output length limit

## Testing an Action

Before saving an action, you can test it:

1. Enter test input in the "Test Input" field
2. Click "Test"
3. Review the output
4. Adjust parameters if needed
5. Save when satisfied

## Using Actions in Blog Posts

1. Open a blog post in development mode
2. Look for the LLM widget next to fields
3. Click "Generate" to run the action
4. Review and edit the generated content
5. Save the post when done

## Managing Actions

- Edit: Click the edit icon next to an action
- Delete: Click the delete icon
- View History: Click the history icon to see past runs
- Test: Click the test icon to try an action

## Prompt Templates

Actions use prompt templates that can include variables:

- `{{input}}`: The content from the source field
- `{{post_title}}`: The post's title
- `{{post_summary}}`: The post's summary

Example template:
```
Generate a catchy title based on this summary: {{input}}

Make it:
- Engaging and click-worthy
- Under 60 characters
- Include a key topic
```

## LLM Models

Available models:
- GPT-3.5 Turbo: Fast, good for most tasks
- GPT-4: Most capable, best for complex tasks
- Mistral: Local model, good for basic tasks
- Claude-3: High quality, good for long content

## Parameters

- Temperature (0.0-2.0):
  - 0.0: Most deterministic
  - 0.7: Balanced (default)
  - 1.0+: More creative
- Max Tokens (1-4096):
  - Limits output length
  - Higher = more content
  - Default: 1000

## Error Handling

Common errors and solutions:

1. Model Timeout
   - Try a smaller model
   - Reduce max tokens
   - Check model status

2. Invalid Input
   - Check source field content
   - Verify prompt template
   - Test with sample input

3. Rate Limiting
   - Wait and retry
   - Use local models
   - Contact admin for limits

## Best Practices

1. Testing
   - Always test before saving
   - Try edge cases
   - Verify output quality

2. Prompts
   - Be specific
   - Include constraints
   - Use examples

3. Models
   - Match to task complexity
   - Consider speed vs quality
   - Monitor usage

4. Workflow
   - Start with drafts
   - Review all output
   - Keep history for reference

## Monitoring

The system tracks:
- Action usage
- Success rates
- Error patterns
- Performance metrics
- Cost (for paid models)

## Support

For help:
1. Check error messages
2. Review this guide
3. Contact admin
4. Submit bug reports 