# Header Image Page Layout Proposal

## Current Layout (Too Many Panels)

1. **Model Selection Panel** - Image generation model selection (gpt-image-1, DALL-E, etc.)
2. **Image Prompt Builder Panel** - Complex accordion with:
   - Input Data (theme + expanded idea)
   - Step 1: System Instructions
   - Step 2: Task Template (with style settings)
   - Step 3: Compiled Prompt
   - Batch Generation info
3. **Image Generation Panel** - Has:
   - "Generate Prompt" button
   - "Generate Image" button
   - Compiled prompt textarea
   - Source data accordion
   - Image preview (single image)
4. **Image Details Panel** - Caption and alt text generation
5. **Image Optimization Panel** - Optimization button and preview

**Issues:**
- Too many accordions to open/close
- Prompt builder is overly complex with multiple steps
- Information is scattered across multiple panels
- Not clear what the workflow is
- Model selection is separate from image generation
- No clear display of both landscape and portrait images

## Proposed Simplified Layout

### Panel 1: Input Data (Read-only, Always Visible)
- **Title:** Input Data
- **Content:** 
  - Theme Name: [display]
  - Expanded Idea: [display]
- **Status:** Always expanded, no accordion

### Panel 2: LLM Prompts (Read-only, Collapsible)
- **Title:** LLM Prompts for Image Message Generation
- **Content:**
  - System Prompt: [display read-only]
  - Task Prompt: [display read-only]
- **Status:** Collapsible accordion

### Panel 3: LLM Settings (Collapsible)
- **Title:** LLM Settings
- **Content:**
  - Provider: [Ollama/OpenAI dropdown]
  - Model: [llama3.2:latest/gpt-4 dropdown]
  - Temperature and other parameters
- **Status:** Collapsible accordion
- **Button:** "Generate LLM-Imaging Message" (in header)

### Panel 4: Generated LLM-Imaging Message (Expandable)
- **Title:** Generated Image Generation Prompt
- **Content:**
  - Large textarea displaying the generated prompt
  - Read-only (but editable if needed)
- **Status:** Auto-expands when prompt is generated

### Panel 5: Image Generation Settings (Collapsible)
- **Title:** Image Generation Settings
- **Content:**
  - Model: [gpt-image-1 dropdown]
  - Size (Landscape): [1536x1024]
  - Size (Portrait): [1024x1536]
  - Quality: [HD dropdown]
- **Status:** Collapsible accordion
- **Button:** "Generate Images (Landscape + Portrait)" (in header)

### Panel 6: Raw Generated Images (Expandable)
- **Title:** Raw Generated Images
- **Content:**
  - Landscape Image: [image display]
  - Portrait Image: [image display]
- **Status:** Auto-expands when images are generated
- **Layout:** Side-by-side or stacked

### Panel 7: Image Optimization (Collapsible)
- **Title:** Image Optimization
- **Content:**
  - Optimization settings (if any)
- **Status:** Collapsible accordion
- **Button:** "Optimize and Watermark" (in header)

### Panel 8: Optimized Images (Expandable)
- **Title:** Optimized Images
- **Content:**
  - Landscape Image (Optimized): [image display]
  - Portrait Image (Optimized): [image display]
- **Status:** Auto-expands when optimization is complete
- **Layout:** Side-by-side or stacked

## Workflow Clarity

The flow is now linear and clear:
1. **View Input** → See theme and expanded idea
2. **View Prompts** → See system/task prompts (read-only)
3. **Configure LLM** → Set provider/model for prompt generation
4. **Generate Prompt** → Click button → See generated prompt
5. **Configure Image Generation** → Set model and parameters
6. **Generate Images** → Click button → See raw landscape + portrait
7. **Optimize** → Click button → See optimized landscape + portrait

## Benefits

- **Fewer panels** (8 instead of 5 complex ones)
- **Clear workflow** (linear progression)
- **Less clicking** (read-only panels stay open, buttons in headers)
- **Better organization** (related functions grouped)
- **Clear image display** (both orientations visible)
- **Simpler prompts panel** (no complex step-by-step assembly)

