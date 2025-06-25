# LLM Panel Module Endpoints

This document describes the key endpoints used by the LLM Panel module for field selection, persistence, and workflow operations.

## 1. Field Mappings Endpoint

```http
GET /workflow/api/field_mappings/
```

Returns all available fields mapped to their respective stages and substages. Used to populate the field selector dropdowns.

**Query Parameters:**
- `stage` (optional): Current workflow stage (defaults to 'planning')
- `substage` (optional): Current workflow substage (defaults to 'idea')
- `step` (optional): Current workflow step (defaults to 'Initial')

**Response Format:**
```json
{
  "stage_name": {
    "substage_name": {
      "inputs": [
        {
          "field_name": "string",
          "display_name": "string"
        }
      ],
      "outputs": [
        {
          "field_name": "string",
          "display_name": "string"
        }
      ]
    }
  }
}
```

**Example Response:**
```json
{
  "planning": {
    "idea": {
      "inputs": [
        {
          "field_name": "idea_seed",
          "display_name": "Idea Seed"
        }
      ],
      "outputs": [
        {
          "field_name": "basic_idea",
          "display_name": "Basic Idea"
        }
      ]
    }
  }
}
```

## 2. Update Field Mapping Endpoint

```http
POST /workflow/api/update_field_mapping/
```

Updates the mapping between a field selector and a database field.

**Request Body:**
```json
{
  "target_id": "string",    // The ID of the input/output target
  "field_name": "string",   // The selected field name
  "section": "string",      // Either "inputs" or "outputs"
  "stage": "string",        // Optional: workflow stage
  "substage": "string",     // Optional: workflow substage
  "step": "string"         // Optional: workflow step (defaults to "initial")
}
```

**Example Request:**
```json
{
  "target_id": "input1",
  "field_name": "idea_seed",
  "section": "inputs",
  "stage": "planning",
  "substage": "idea"
}
```

**Response Format:**
```json
{
  "field_name": "string",
  "section": "string",
  "table_name": "string"
}
```

**Example Response:**
```json
{
  "field_name": "idea_seed",
  "section": "inputs",
  "table_name": "post_development"
}
```

## 3. Post Development Fields Endpoint

```http
GET /blog/api/v1/post/{post_id}/development
```

Gets all field values for a post's development data.

**Response Format:**
```json
{
  "field_name": "field_value",
  // ... all fields from post_development table
}
```

**Example Response:**
```json
{
  "idea_seed": "story-telling",
  "basic_idea": "Story-telling has long been...",
  "provisional_title": "Weaving Words: Uncovering..."
}
```

## 4. Update Post Development Endpoint

```http
PATCH /blog/api/v1/post/{post_id}/development
```

Updates specific fields in the post_development table.

**Request Body:**
```json
{
  "field_name": "new_value"
  // ... any number of fields to update
}
```

**Example Request:**
```json
{
  "idea_seed": "updated story concept"
}
```

**Response Format:**
```json
{
  "success": true
}
```

## Usage Flow

1. When the panel loads, it fetches available fields from `/workflow/api/field_mappings/`
2. When a field is selected in a dropdown, it calls `/workflow/api/update_field_mapping/` to get the database field mapping
3. The panel loads current field values from `/blog/api/v1/post/{post_id}/development`
4. When field values change, they are persisted using `/blog/api/v1/post/{post_id}/development` (PATCH)

## Testing the Endpoints

You can test these endpoints using curl:

```bash
# Get field mappings
curl -s "http://localhost:5000/workflow/api/field_mappings/?stage=planning&substage=idea" | python3 -m json.tool

# Update field mapping
curl -s -X POST "http://localhost:5000/workflow/api/update_field_mapping/" \
  -H "Content-Type: application/json" \
  -d '{"target_id":"input1", "field_name":"idea_seed", "section":"inputs", "stage":"planning", "substage":"idea"}' \
  | python3 -m json.tool

# Get post development fields
curl -s "http://localhost:5000/blog/api/v1/post/22/development" | python3 -m json.tool

# Update post development field
curl -s -X PATCH "http://localhost:5000/blog/api/v1/post/22/development" \
  -H "Content-Type: application/json" \
  -d '{"idea_seed": "new value"}' \
  | python3 -m json.tool
```

## LLM Actions Endpoints

### List Actions
```