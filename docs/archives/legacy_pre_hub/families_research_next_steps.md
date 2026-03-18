# Families Research - Next Steps

## Current Status

✅ **Completed:**
- Database schema with `research_data` JSONB field
- Research guide (`docs/surname_research_guide.md`)
- Implementation plan (`docs/families_research_implementation_plan.md`)
- Research tool script (`scripts/research_family.py`)
- Test case template generated (`data/research_Abernethy_6762.json`)
- UI for browsing and filtering families

📋 **Ready for:**
- Test case research (Abernethy - ID: 6762)
- Process refinement
- Batch processing setup

## Next Steps - Choose Your Approach

### Option 1: Manual Test Research (Recommended First)

**Process:**
1. Research Abernethy manually using the guide
2. Populate the JSON template
3. Validate and review
4. Refine the process based on experience

**Pros:**
- Full control over quality
- Learn the process thoroughly
- Identify any guide gaps

**Cons:**
- Time-consuming
- May reveal process issues only after doing it

### Option 2: LLM-Assisted Test Research

**Process:**
1. Create an LLM research script that:
   - Takes family context from database
   - Uses research guide as instructions
   - Populates JSON following the schema
   - Marks uncertainty appropriately
2. Review and fact-check LLM output
3. Refine prompts/process based on results

**Pros:**
- Faster initial research
- Can test the LLM workflow
- Good for identifying what LLMs can/can't do well

**Cons:**
- Requires fact-checking
- May need multiple iterations to get right
- LLM may invent data if not carefully constrained

### Option 3: Hybrid Approach

**Process:**
1. LLM does initial research for test case
2. Human fact-checks and enhances
3. Use this to refine both manual and LLM processes

**Pros:**
- Best of both worlds
- Tests both workflows
- Faster than pure manual

**Cons:**
- More complex setup
- Need to manage two processes

## Recommended Next Step

**I recommend Option 2 (LLM-Assisted) for the test case** because:

1. **Faster iteration** - You can test the process quickly
2. **Identify issues early** - See what LLMs struggle with
3. **Refine prompts** - Adjust the research guide based on actual LLM behavior
4. **Still requires review** - You'll fact-check, so quality is maintained

## Implementation Plan

### Step 1: Create LLM Research Script

Create a script that:
- Loads family context from database
- Uses research guide as system prompt
- Calls LLM with structured instructions
- Parses LLM response into JSON
- Validates output
- Saves for review

### Step 2: Test with Abernethy

- Run LLM research on Abernethy
- Review output
- Fact-check key claims
- Identify issues

### Step 3: Refine

- Update research guide based on issues
- Refine LLM prompts
- Adjust validation rules
- Update tool if needed

### Step 4: Decide on Batch Approach

After test case:
- If LLM works well → Use for batch processing
- If LLM struggles → Use manual or hybrid
- If manual preferred → Continue manually

## What Would You Like to Do?

1. **Create LLM research script** - I can build a script that uses your LLM service to research families
2. **Do manual test research** - You research Abernethy manually, I help refine the process
3. **Set up batch processing** - Create scripts to process multiple families
4. **Something else** - Tell me what you prefer

Which approach would you like to take?

