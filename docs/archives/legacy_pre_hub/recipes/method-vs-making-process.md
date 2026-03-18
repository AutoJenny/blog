# Method vs Making Process - Recipe Sections Clarification

## Method Section (`recipe_method`)

**Purpose:** Text content - step-by-step cooking instructions  
**Content Type:** Written instructions (text/HTML)  
**Display:** Numbered list of cooking steps  
**Example:**
1. Heat the butter in a large pan
2. Add the onion and cook until soft
3. Add the haddock and cook for 5 minutes
4. Serve hot

**Purpose:** Tells the reader HOW to cook the dish

## Making Process Section (`recipe_gallery`)

**Purpose:** Visual/image - showing one step of the recipe preparation  
**Content Type:** Image (stored in `post_images` table)  
**Display:** Single image with caption describing which step is shown  
**Example:**
- Image showing: "Adding the haddock to the pan"
- Caption: "Step 3: Gently add the smoked haddock pieces to the hot butter and onion mixture"

**Purpose:** Shows a visual representation of ONE step in the cooking process

## Key Differences

| Aspect | Method (`recipe_method`) | Making Process (`recipe_gallery`) |
|--------|-------------------------|----------------------------------|
| **Type** | Text content | Image |
| **Purpose** | Complete instructions | Single visual example |
| **Content** | All steps written out | One image showing one step |
| **Storage** | `post_section.polished` or `post_section.draft` | `post_images` table linked via `section_id` |
| **Display** | Numbered list | Image with caption |

## Why Both?

- **Method** provides the complete recipe instructions in text
- **Making Process** provides a visual aid showing one key step (often the most interesting or challenging step)

The Making Process image complements the Method text by showing readers what a step looks like visually.

