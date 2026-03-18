# Pipeline Diagnostics System

## Overview

The Pipeline Diagnostics System provides comprehensive testing and debugging capabilities for the GPT-Image-1 prompt rendering pipeline. It identifies exactly where style integration fails and provides detailed analysis of each stage.

## Components

### 1. Diagnostic API Endpoint

**Endpoint**: `GET /imaging/api/diagnostic/posts/<int:post_id>/sections/<section_id>/prompt-pipeline`

**Parameters**:
- `post_id` (int): Post ID to test
- `section_id` (string): Section ID to test  
- `model_key` (query param): Model to test (default: gpt-image-1)

**Response**: JSON with detailed stage-by-stage results

### 2. CLI Diagnostic Script

**File**: `scripts/diagnose_prompt_pipeline.py`

**Usage**:
```bash
python3 scripts/diagnose_prompt_pipeline.py --post-id 69 --section-id 1 --model gpt-image-1
```

**Output**: Console-based diagnostic report with stage-by-stage analysis

### 3. UI Diagnostic Button

**Location**: Image Generation page (`/imaging/sections/image_generation`)

**Functionality**: 
- Click "🔍 Test Prompt Pipeline" button
- Displays results in formatted panel
- Shows overall status and individual stage results

## Diagnostic Stages

### Stage 1: Database Retrieval
- Verifies post exists and has `extra_settings`
- Checks for active imaging style configuration
- Validates `post_development.sections` data structure
- Confirms target section exists with `image_prompts`

### Stage 2: Canonical Prompt Creation
- Tests `prompt_service.get_canonical_prompt()`
- Verifies style JSON is loaded correctly
- Checks canonical prompt structure and content

### Stage 3: Renderer Selection
- Tests `PromptRendererFactory.create_renderer()`
- Verifies correct renderer class instantiation
- Validates model constraints

### Stage 4: Style Integration
- Tests `renderer._integrate_style_details()`
- Verifies style JSON processing
- Checks for key style elements (watercolor, pastel)

### Stage 5: Full Rendering
- Tests complete `renderer.render()` process
- Validates final prompt length and content
- Checks for all required style guidelines

### Stage 6: API Integration
- Tests `prompt_service.render_prompt_for_model()`
- Verifies service matches direct render
- Validates metadata and debug information

## Usage Examples

### CLI Testing
```bash
# Test specific post/section
python3 scripts/diagnose_prompt_pipeline.py --post-id 69 --section-id 1 --model gpt-image-1

# Test different model
python3 scripts/diagnose_prompt_pipeline.py --post-id 69 --section-id 1 --model sdxl-lora
```

### API Testing
```bash
# Test via curl
curl "http://localhost:5000/imaging/api/diagnostic/posts/69/sections/1/prompt-pipeline?model_key=gpt-image-1"

# Test different section
curl "http://localhost:5000/imaging/api/diagnostic/posts/69/sections/2/prompt-pipeline?model_key=gpt-image-1"
```

### UI Testing
1. Navigate to `/imaging/sections/image_generation`
2. Select desired model from dropdown
3. Click "🔍 Test Prompt Pipeline" button
4. Review results in diagnostic panel

## Interpreting Results

### Overall Status
- `passed`: All stages completed successfully
- `failed`: One or more stages failed
- `error`: Unexpected error occurred

### Stage Results
Each stage returns:
- `success`: Boolean indicating if stage passed
- `error`: Error message if stage failed
- Stage-specific data (lengths, previews, flags)

### Style Guidelines Check
The system validates presence of:
- ✅ watercolor
- ✅ pastel colors
- ✅ white margins
- ✅ visible brushstrokes
- ✅ pen and ink details
- ✅ avoiding dark colors
- ✅ avoiding saturated colors
- ✅ avoiding digital appearance

## Troubleshooting

### Common Issues

1. **Database Stage Fails**
   - Post doesn't exist
   - No active style configured
   - Missing `post_development` data

2. **Canonical Prompt Stage Fails**
   - Section not found in `post_development.sections`
   - Malformed JSON in database
   - Missing `image_prompts` data

3. **Renderer Stage Fails**
   - Unknown model key
   - Missing renderer class
   - Import errors

4. **Style Integration Stage Fails**
   - Empty or malformed `style_json`
   - Missing style integration method
   - Style processing errors

5. **Rendering Stage Fails**
   - Prompt too long for model
   - Renderer method errors
   - Style conflict issues

6. **API Integration Stage Fails**
   - Service method errors
   - Metadata generation issues
   - Endpoint routing problems

## Implementation Details

### Files Modified
- `blueprints/imaging.py`: Added diagnostic endpoint
- `scripts/diagnose_prompt_pipeline.py`: Created CLI script
- `templates/imaging/sections/image_generation.html`: Added diagnostic button
- `static/js/imaging/model-selection.js`: Added diagnostic handler

### Dependencies
- `modules.prompt_service`: For canonical prompt creation
- `modules.prompt_renderers`: For renderer testing
- `config.database`: For database access
- Flask: For API endpoint

## Best Practices

1. **Run diagnostics before debugging**: Always use diagnostics to identify the failing stage
2. **Test with real data**: Use actual post/section combinations
3. **Check multiple sections**: Test different sections to identify patterns
4. **Monitor style conflicts**: Look for conflicting instructions in source material
5. **Validate character limits**: Ensure prompts fit within model constraints

## Future Enhancements

- Add style conflict detection
- Implement automatic style override
- Add performance metrics
- Create diagnostic history/logging
- Add batch testing capabilities
