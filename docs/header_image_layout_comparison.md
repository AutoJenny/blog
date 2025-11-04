# Header Image Page: Current vs Proposed Layout

## Current Messy Layout (5 Complex Panels)

### Panel 1: Model Selection Panel
- Accordion with model selection dropdown
- Complex parameter controls (SDXL, DALL-E, LoRA settings)
- Hidden by default

### Panel 2: Image Prompt Builder Panel
- Complex accordion with multiple nested steps:
  - Input Data (theme + expanded idea) - hidden
  - Step 1: System Instructions - hidden
  - Step 2: Task Template with style checkboxes - hidden
  - Step 3: Compiled Prompt - hidden
  - Batch Generation info - hidden
- Everything is collapsed by default
- Too many clicks to see anything

### Panel 3: Image Generation Panel
- Has TWO buttons in header: "Generate Prompt" and "Generate Image"
- Compiled prompt textarea (confusing - same as Step 3 above?)
- Source data accordion (duplicate of Input Data?)
- Single image preview (only shows one orientation)
- Everything collapsed by default

### Panel 4: Image Details Panel
- Caption and alt text generation
- Separate from image generation
- Collapsed by default

### Panel 5: Image Optimization Panel
- Optimization button
- Single image preview (only optimized)
- Collapsed by default

## Issues with Current Layout

1. **Too Many Accordions**: 5 panels, all collapsed, user has to click to see anything
2. **Duplication**: Input data shown in multiple places
3. **Unclear Workflow**: Not obvious what order to do things
4. **Missing Images**: Only shows one image, not both landscape and portrait
5. **Complex Prompt Builder**: Multi-step process that's confusing
6. **Buttons Scattered**: Generate buttons in different panels
7. **No Clear Separation**: LLM settings for prompt generation vs image generation mixed together

## Proposed Clean Layout (8 Simple Panels)

### Panel 1: Input Data
**Status:** Always visible (no accordion)
- Theme Name: [display]
- Expanded Idea: [display]

### Panel 2: LLM Prompts
**Status:** Collapsible (default: open)
- System Prompt: [read-only display]
- Task Prompt: [read-only display]

### Panel 3: LLM Settings
**Status:** Collapsible (default: closed)
- Provider: [Ollama/OpenAI]
- Model: [llama3.2:latest/gpt-4]
- Temperature, Max Tokens
- **Button in header:** "Generate LLM-Imaging Message"

### Panel 4: Generated Prompt
**Status:** Auto-expands when generated
- Large textarea with generated image generation prompt
- Read-only (but editable checkbox)

### Panel 5: Image Generation Settings
**Status:** Collapsible (default: closed)
- Model: [gpt-image-1]
- Landscape Size: [1536x1024]
- Portrait Size: [1024x1536]
- Quality: [HD]
- **Button in header:** "Generate Images (Landscape + Portrait)"

### Panel 6: Raw Generated Images
**Status:** Auto-expands when images generated
- **Layout:** Two columns
- Landscape Image: [image]
- Portrait Image: [image]
- Both images visible side-by-side

### Panel 7: Image Optimization
**Status:** Collapsible (default: closed)
- Optimization settings (if any)
- **Button in header:** "Optimize and Watermark"

### Panel 8: Optimized Images
**Status:** Auto-expands when optimization complete
- **Layout:** Two columns
- Landscape Image (Optimized): [image]
- Portrait Image (Optimized): [image]
- Both images visible side-by-side

## Benefits of Proposed Layout

1. **Clear Workflow**: Linear progression from top to bottom
2. **Fewer Clicks**: Input data always visible, prompts open by default
3. **Better Organization**: Related functions grouped logically
4. **Complete Image Display**: Both landscape and portrait always visible
5. **Simpler Prompts**: No complex multi-step assembly
6. **Clear Separation**: LLM settings separate from image generation settings
7. **Action Buttons in Headers**: Easy to find, contextually placed
8. **Auto-Expanding Results**: Generated content automatically appears

## Implementation Notes

- Remove: Model Selection Panel (merge into Image Generation Settings)
- Simplify: Prompt Builder Panel (remove complex steps, just show prompts)
- Enhance: Image Generation Panel (show both landscape and portrait)
- Add: Separate LLM Settings panel for prompt generation
- Reorganize: Linear flow from input → prompts → LLM → prompt → image settings → images → optimization → optimized images

