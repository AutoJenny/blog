# Surname Research Plan Review

## Overall Assessment

Your research plan is **excellent** and well-thought-out. The emphasis on fact-checking, explicit uncertainty, and avoiding invention aligns perfectly with best practices. Below are minor clarifications and suggestions.

## Strengths

1. **Strong emphasis on uncertainty** - The repeated instruction to mark uncertainty rather than invent is crucial
2. **Source quality focus** - Preference for specialist sources is appropriate
3. **Heraldry caution** - Correctly emphasizes individual arms, not generic family arms
4. **Cross-checking requirement** - Recording disagreements in uncertainty_flags is good practice
5. **Brevity preference** - "Short and cautious is better than over-detailed and speculative" is wise

## Minor Clarifications & Suggestions

### 1. Etymology Section

**Plan says:** "Identify: The type: patronymic, locational, occupational, descriptive, clan/territorial."

**Schema alignment:** ✅ Matches perfectly - `name_type` field accepts these values.

**Suggestion:** Consider adding guidance for when a name might have **multiple origins** (e.g., some names could be both locational AND occupational). The schema allows only one `name_type`, so you might want to note this in `etymology_summary` if there's genuine ambiguity.

### 2. Early Records Section

**Plan says:** "If no specific date or record is found, set fields to `null` or very generic descriptions"

**Schema alignment:** ✅ Good - all fields are nullable.

**Clarification needed:** For `earliest_attestation.year` - the schema shows `year: 0` in the template. Should `0` be used for "unknown" or should it be `null`? Recommend using `null` for unknown years rather than `0`, as `0` might be confusing.

**Suggestion:** Add explicit guidance: "Use `null` for unknown years, not `0`."

### 3. Distribution Historic

**Plan says:** "Assign qualitative frequency: `very_high` / `high` / `medium` / `low` / `very_low`"

**Schema alignment:** ✅ Perfect match - these are the exact enum values.

**No issues here.**

### 4. Distribution Modern

**Plan says:** "List countries where the name is found, with approximate frequency/ranking where stated."

**Schema alignment:** ✅ Good - `approx_rank` is nullable, which is correct.

**Clarification:** The plan doesn't mention the `trend` field (growing | stable | declining | unknown). Consider adding: "If trend data is available, include it; otherwise use 'unknown'."

### 5. Clan Association

**Plan says:** "If there is **no Scottish link**, set `is_scottish_name` to `false`"

**Schema alignment:** ✅ Good.

**Important note:** The database already has `is_clan` flag. Consider cross-referencing:
- If `is_clan = TRUE` in database, then `clan_association.is_scottish_name` should typically be `TRUE`
- But `is_scottish_name` can be `TRUE` even if not a clan (e.g., septs, territorial families)

**Suggestion:** Add: "Check the database `is_clan` flag - if TRUE, this should inform but not override your research."

### 6. Heraldry

**Plan says:** "Only enter arms where an individual armiger is clearly named."

**Schema alignment:** ✅ Perfect - `arms` array requires `armiger_name`.

**Excellent guidance** - this prevents the common error of generic "family arms."

### 7. Variants

**Plan says:** "Categorise: Straight orthographic variants vs Distinct but related surnames"

**Schema alignment:** ✅ Good - `variant_spellings` for orthographic, `related_surnames` for cognates.

**Clarification:** The schema has both:
- `variant_spellings` - simple array of strings
- `related_surnames` - array of objects with `relationship_type` and `notes`

**Suggestion:** Make this distinction explicit in the plan: "Use `variant_spellings` for simple spelling differences (Macdonald/MacDonald). Use `related_surnames` for cognates or anglicised forms that need explanation."

### 8. Migration

**Plan says:** "Identify phases: Internal movement (Highlands → Lowlands, rural → industrial centres)"

**Schema alignment:** ✅ Good structure.

**Suggestion:** Consider adding guidance on how to handle **generic patterns** vs **surname-specific evidence**. The plan mentions this but could be more explicit: "If evidence is generic (e.g., 'many Highland surnames did X'), note this in `uncertainty_flags` and be cautious in `summary`."

### 9. Notables

**Plan says:** "Only include people who: Are clearly documented and have publicly recognised roles."

**Schema alignment:** ✅ Good.

**Clarification:** The schema has `notability_type` enum. Consider adding: "Categorize each person's `notability_type` (politics, military, arts, scholarship, business, religion, sport, other)."

### 10. Cultural Notes

**Plan says:** "Distinguish: **Documented traditions** from marketing or modern stereotypes."

**Schema alignment:** ✅ Good.

**No issues - excellent guidance.**

### 11. Genealogy Resources

**Plan says:** "URLs where appropriate (if permitted)"

**Schema alignment:** ✅ Good - `url` fields are nullable.

**Suggestion:** Consider adding: "If URLs are not permitted in sources, use descriptive identifiers instead (e.g., 'FamilySearch surname page', 'ScotlandsPeople index')."

## Schema-Specific Considerations

### Missing from Plan (but in Schema)

1. **`variants.canonical_form`** - The plan doesn't mention setting this. Should this match the database `name` field, or can it differ? **Recommendation:** Set it to match the database `name` unless there's a specific reason to differ.

2. **`heraldry.has_documented_arms`** - The plan doesn't explicitly mention this boolean. **Recommendation:** Set to `true` only if `arms` array has entries; otherwise `false`.

3. **`clan_association.is_scottish_name`** - The plan mentions this, but consider: Should this be `true` for Irish names that became Scottish? **Recommendation:** Use `true` if the name has any significant Scottish association (even if originally Irish/English).

### Data Type Clarifications

1. **Years:** Use `null` for unknown, not `0`
2. **Booleans:** Use `true`/`false`, not strings
3. **Arrays:** Use empty arrays `[]` if no items, not `null`
4. **Strings:** Use empty string `""` for optional text fields if nothing to say, or `null` if truly unknown

## Potential Challenges for LLM Implementation

1. **Source Access:** The plan mentions "specialist surname / onomastic sources" - LLMs may have limited access to these. Consider providing a list of recommended sources or allowing web search.

2. **Cross-checking:** The instruction to "cross-check when possible" is good, but LLMs may struggle with this. Consider: "If only one source is found, note this in `metadata.research_confidence`."

3. **Rare Surnames:** The plan says "short and cautious is better" - excellent. Consider adding: "For very rare surnames with minimal documentation, a brief entry with high uncertainty is preferable to speculation."

## Recommended Additions to Plan

1. **Template Usage:** "Start from the template JSON structure. Only populate fields where evidence exists."

2. **Year Handling:** "Use `null` for unknown years, not `0`. Use `approximate: true` when dates are estimated (e.g., 'c. 1400')."

3. **Array Handling:** "Use empty arrays `[]` when no items exist. Do not use `null` for arrays."

4. **Boolean Logic:** 
   - `has_documented_arms = true` only if `arms` array has entries
   - `is_scottish_name = true` if name has any Scottish association (clan, sept, territorial, or historical presence)

5. **Cross-Reference Database:** "Before populating `clan_association`, check the database `is_clan` and `family_septs` relationships for existing data."

6. **Variant Handling:** "Use `variant_spellings` for simple spelling differences. Use `related_surnames` for names that need relationship explanation (cognates, anglicised forms)."

## Final Verdict

**The plan is excellent and ready for implementation** with these minor clarifications. The emphasis on fact-checking, uncertainty, and avoiding invention is exactly right. The main additions needed are:

1. Explicit guidance on `null` vs `0` for years
2. Clarification on `variant_spellings` vs `related_surnames`
3. Cross-reference guidance with existing database fields
4. Boolean logic for `has_documented_arms` and `is_scottish_name`

These are minor refinements - the core approach is sound.

