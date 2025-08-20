# IMPLEMENTATION PLAN - FIX UPLOAD PROCESS

## ABSOLUTE INSTRUCTIONS - MUST NOT BE IGNORED
**BEFORE I DO ANYTHING, I MUST:**
1. Tell you EXACTLY what I am going to do
2. Show you the specific code/file changes I will make
3. Wait for your explicit permission to proceed
4. NOT start any work until you approve

**I WILL NOT:**
- Make any changes without telling you first
- Start coding without your permission
- Assume I know what to do
- Proceed without explicit approval

**EVERY ACTION REQUIRES:**
- Clear statement of what I will do
- Specific files I will modify
- Exact changes I will make
- Your permission before proceeding

## CRITICAL RULE: NO DEVIATION FROM THIS SEQUENCE
- I will NOT divert to parallel processes
- I will NOT try to "fix" things while working on other stages
- I will follow this exact order with no additions

## STAGE 1: GET THE PREVIEW CORRECT
**Goal**: Ensure `http://localhost:5001/preview/53?meta=off` returns perfect HTML with all images and content

**What I will do**:
1. Check if Flask server is running on port 5001
2. Test the preview endpoint returns complete HTML
3. Verify all 7 sections display correctly with images
4. Fix ONLY preview issues, nothing else

**What I will NOT do**:
- Touch the upload script
- Modify clan_post template
- Add any new features
- "Improve" anything not preview-related

## STAGE 2: GET THE CLAN_POST TEMPLATE CORRECT  
**Goal**: Create clan_post.html that is identical to preview HTML except for upload-specific cleanup

**What I will do**:
1. Copy the working preview HTML structure exactly
2. Remove ONLY preview-specific meta/context elements
3. Keep all content, images, and structure identical
4. Add clan widget in the correct location

**What I will NOT do**:
- Rebuild the template from scratch
- Add new functionality
- Modify content structure
- Touch the upload script

## STAGE 3: GET THE UPLOAD SCRIPT CORRECT
**Goal**: Modify upload script to use clan_post template as source

**What I will do**:
1. Change upload script to render clan_post.html template
2. Ensure image paths are correctly translated
3. Test upload produces identical HTML to clan_post template
4. Verify clan widget appears correctly

**What I will NOT do**:
- Rebuild the upload logic
- Add new image processing
- Modify the template
- Touch the preview

## SUCCESS CRITERIA
- Preview shows all 7 sections with images
- clan_post template is identical to preview (minus meta)
- Upload produces identical HTML to clan_post template
- Clan widget appears correctly on live site

## FAILURE CONDITIONS (STOP IMMEDIATELY)
- If I try to "fix" anything not in current stage
- If I add new features not requested
- If I rebuild systems that already work
- If I deviate from this exact sequence

I understand this plan and will follow it exactly without deviation.
