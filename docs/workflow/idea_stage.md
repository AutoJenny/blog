# Idea Stage

## Overview
The Idea stage is the first step in the content creation workflow. It focuses on developing a basic idea from an initial seed concept.

## Fields

### Input Fields
- `idea_seed` (Text): The initial concept or idea to be expanded
- `basic_idea` (Text): The expanded and structured basic idea

### Database Schema
```sql
ALTER TABLE post_development
ADD COLUMN idea_seed TEXT,
ADD COLUMN basic_idea TEXT;
```

## LLM Actions

### Idea Generation
- **Name**: `idea_generation`
- **Description**: Expands an idea seed into a comprehensive basic idea
- **Input Fields**: `idea_seed`
- **Output Fields**: `basic_idea`
- **Prompt Template**: See `app/llm/actions/idea.py`
- **Temperature**: 0.7
- **Max Tokens**: 1000

## API Endpoints

### Test Action
```
POST /api/v1/llm/actions/idea_generation/test
```
Request body:
```json
{
    "input": {
        "idea_seed": "string"
    }
}
```
Response:
```json
{
    "basic_idea": "string"
}
```

### Save Idea
```
POST /api/v1/idea/save/{post_id}
```
Request body:
```json
{
    "basic_idea": "string"
}
```

## Frontend Components
- `IdeaProcessor`: Handles idea generation and saving
- `BaseProcessor`: Base class for all workflow processors

## Usage
1. Enter an idea seed in the input field
2. Click "Generate Idea" to expand the idea
3. Review and edit the generated basic idea
4. Click "Save Idea" to store the result

## Error Handling
- Input validation for required fields
- LLM response validation
- Error messages for failed generations
- Database error handling 