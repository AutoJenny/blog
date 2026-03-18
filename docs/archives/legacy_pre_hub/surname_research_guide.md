# Surname Research Guide (for LLM Use)

**Goal:**  

For each surname, fill a JSON record with *fact-checked* information and explicit uncertainty.  

Never invent specific records, dates, or people. When evidence is weak, say so.

## General Rules

- Prefer **specialist surname / onomastic sources**, reputable encyclopedias, and national archive/genealogy portals.

- Cross-check when possible. If sources conflict, **record the disagreement** in `uncertainty_flags`.

- For rare surnames, short and cautious is better than over-detailed and speculative.

- Avoid implying that coats of arms or tartans belong to *all* bearers of a surname.

- **Start from the template JSON structure.** Only populate fields where evidence exists.

- **Data handling:**
  - Use `null` for unknown values, not `0` or empty strings
  - Use empty arrays `[]` when no items exist (not `null`)
  - Use `true`/`false` for booleans, not strings
  - For optional text fields, use empty string `""` if nothing to say, or `null` if truly unknown

---

## 1. `etymology`

**Objective:**  

Explain what the surname likely means, which language(s) it comes from, and what type of surname it is.

**Steps:**

1. Look up the surname in:
   - Surname dictionaries / onomastic references.
   - Reputable encyclopedic or linguistic sources.

2. Identify:
   - The **type**: patronymic, locational, occupational, descriptive, clan/territorial, habitational, religious, other, unknown.
   - Likely **origin language(s)** (Gaelic, Scots, Norse, Norman French, etc.).
   - Root words and their meanings.

3. Capture:
   - Root forms and meanings in `root_words`.
   - Earliest known forms (spellings) if mentioned.

4. In `etymology_summary`, give a concise narrative including:
   - Leading theory.
   - Any serious alternatives.
   - Explicit note if evidence is thin or speculative.
   - **If a name has multiple possible origins** (e.g., both locational AND occupational), note this in the summary even though `name_type` can only hold one value.

---

## 2. `early_records`

**Objective:**  

Record the earliest documented sightings of the surname.

**Steps:**

1. Search for earliest mentions in:
   - Tax rolls, charters, parish records, archive indexes, surname sites.

2. Only record **specific dates/places** when a source clearly states them.

3. Fill:
   - `earliest_attestation` with the **earliest reliable** record.
   - `other_attestations` with a few additional early examples if available.

4. Use `record_confidence` to indicate strength of evidence.

5. In `record_notes`, briefly explain:
   - Whether early records cluster in a particular region.
   - Any key spelling variants.

6. **Important:** 
   - Use `null` for unknown years, **not `0`**.
   - Use `approximate: true` when dates are estimated (e.g., 'c. 1400').
   - Set `year: null` if no specific date is found.

**If no specific date or record is found**, set fields to `null` or very generic descriptions and explain the gap in `record_notes`.

---

## 3. `distribution_historic`

**Objective:**  

Describe where the surname historically clustered (pre-1900).

**Steps:**

1. Use:
   - Older censuses, parish index summaries, surname-mapping tools, or historical surname studies.

2. Identify **regional hotspots** (counties, parishes, islands).

3. For each region:
   - Assign qualitative frequency: `very_high` / `high` / `medium` / `low` / `very_low` / `unknown`.

4. In `summary`:
   - Describe main concentrations and any apparent expansion patterns.

5. Note uncertainties (e.g. sparse data, limited time periods) in `uncertainty_flags`.

---

## 4. `distribution_modern`

**Objective:**  

Describe present-day or late-20th/early-21st century distribution.

**Steps:**

1. Use:
   - Modern surnames-by-country tools, statistical releases, or academic studies.

2. List countries where the name is found, with approximate frequency/ranking where stated.

3. Include `trend` field if data is available (growing | stable | declining | unknown); otherwise use 'unknown'.

4. In `notes`, mention:
   - Major diaspora destinations.
   - Whether the name remains strongly local or widely dispersed.

---

## 5. `clan_association` (Scottish focus)

**Objective:**  

Clarify whether the surname has any Scottish clan or kindred connection.

**Steps:**

1. **Before researching, check the database:**
   - Check the `is_clan` flag in the families table.
   - Check `family_septs` relationships for existing sept associations.
   - This should inform but not override your research.

2. Consult:
   - Official and well-regarded clan/sept lists.
   - Recognised clan websites and Scottish heraldic authorities.

3. Determine:
   - Whether the name is a sept of a known clan.
   - Whether it's a territorial family or part of a kindred.

4. Set:
   - `official_status` based on whether the association is formally recognised, traditional, commercial-only, or unknown.
   - `is_scottish_name = true` if the name has **any Scottish association** (clan, sept, territorial, or historical presence), even if originally Irish/English.

5. In `association_notes`:
   - Explain any disputes or weak associations clearly.

**If there is **no Scottish link**, set `is_scottish_name` to `false` and explain briefly.

---

## 6. `heraldry`

**Objective:**  

Record **individual** arms, mottoes, and tartans, with clear limits.

**Steps:**

1. Look at:
   - Official heraldic registers, serious heraldry sites, and tartan registers.

2. Only enter arms where an individual armiger is clearly named.

3. **Set `has_documented_arms = true` only if the `arms` array has entries.** Otherwise set to `false`.

4. For tartans:
   - Record registered tartans **by name**, with status (clan, family, fashion, corporate).

5. Add a short `disclaimer` reminding that heraldry and tartans belong to individuals/registered entities, not automatically to all with the surname.

**Do **not** claim a generic "family coat of arms" for all bearers.**

---

## 7. `variants`

**Objective:**  

List spelling and language variants and explain their relationships.

**Steps:**

1. Gather variant forms from:
   - Surname dictionaries, record indexes, and variant lists.
   - **Also check the database:** `family_spellings` and `family_aliases` tables for existing relationships.

2. **Distinguish between:**
   - **`variant_spellings`** (simple array of strings): Use for straightforward orthographic variants (Macdonald/MacDonald, Smith/Smyth).
   - **`related_surnames`** (array of objects with relationship_type): Use for cognates, anglicised forms, or names that need explanation of their relationship.

3. Set `canonical_form` to match the database `name` field unless there's a specific reason to differ.

4. In `variant_notes`, mention:
   - Common pitfalls (e.g. two unrelated surnames that look similar).
   - Cases where a variant appears in a different language (Gaelic vs English).
   - How variants relate to the canonical form.

---

## 8. `migration`

**Objective:**  

Outline how the surname moved over time, especially in Scottish and British contexts.

**Steps:**

1. Use:
   - Historical overviews, surname-mapping over time, and diaspora studies.

2. Identify phases:
   - Internal movement (Highlands → Lowlands, rural → industrial centres).
   - Overseas emigration waves (to Canada, USA, Australia, etc.).

3. In each `phases` entry:
   - Record from/to regions and main drivers (clearances, famine, industrialisation).

4. In `summary`, tie this together into a short chronological narrative.

5. **Important:** If evidence is generic (e.g., "many Highland surnames did X"), note this explicitly in `uncertainty_flags` and be cautious in `summary`. Distinguish between surname-specific evidence and general patterns.

---

## 9. `notables`

**Objective:**  

List verifiable notable individuals with the surname.

**Steps:**

1. Check:
   - Biographical dictionaries, encyclopedias, reputable databases.

2. Only include people who:
   - Are clearly documented and have publicly recognised roles.

3. For each:
   - Provide a short, neutral `short_bio`.
   - Categorize `notability_type` (politics, military, arts, scholarship, business, religion, sport, other).
   - Avoid exaggeration or unverified claims.

4. If there are very few or no notable individuals, say so briefly in `notables_notes`.

**Never invent people or merge multiple individuals into one.**

---

## 10. `cultural_notes`

**Objective:**  

Capture cultural associations, if any.

**Steps:**

1. Look for:
   - Mentions in folklore, literature, film, or recurring occupational stereotypes.

2. Distinguish:
   - **Documented traditions** from marketing or modern stereotypes.

3. In `cultural_summary`, summarise:
   - Any real patterns (or explicitly state "no special cultural associations known").

**If nothing meaningful is found, don't pad: say that no notable cultural references emerged.**

---

## 11. `genealogy_resources`

**Objective:**  

Point to where serious researchers can go next.

**Steps:**

1. Identify:
   - Family societies, clan associations, one-name studies.
   - Published family histories.
   - Regions with especially rich records for the surname.

2. Add:
   - URLs where appropriate (if permitted). **If URLs are not permitted in sources, use descriptive identifiers instead** (e.g., 'FamilySearch surname page', 'ScotlandsPeople index').
   - Honest notes about scope and quality (e.g., "narrow line only", "heavily romanticised").

3. In `research_tips`, give practical hints:
   - Common spelling traps.
   - Whether multiple origins are likely.
   - Any special archive collections worth checking.

---

## Field-Specific Guidelines

### Metadata

- **`sources`**: Use short identifiers or URLs (if allowed). Be specific enough that sources can be verified.
- **`last_updated`**: Use YYYY-MM-DD format.
- **`research_confidence`**: Be honest. Use 'low' if only one source found, 'medium' if multiple sources agree, 'high' if well-documented and cross-checked.
- **`notes`**: Use for research quality issues, gaps, controversies, or methodology notes.

### Etymology

- **`origin_languages`**: Array of strings. Include all relevant languages (can be multiple).
- **`name_type`**: Single value. If multiple types possible, choose the most likely and explain alternatives in `etymology_summary`.
- **`root_words`**: Array of objects. Each should have `language`, `form`, and `meaning`.
- **`earliest_known_forms`**: Array of objects. Include `spelling`, `approx_date`, `region` (if known), `source_hint`.

### Early Records

- **`year`**: Use `null` for unknown, not `0`.
- **`approximate`**: `true` for estimated dates (e.g., "c. 1400"), `false` for specific dates.
- **`record_type`**: Examples: 'charter', 'poll tax', 'sasine', 'kirk session', 'parish register'.
- **`record_confidence`**: Reflects how certain you are about the record's authenticity and dating.

### Distribution

- **`relative_frequency`**: Use the exact enum values: `very_high`, `high`, `medium`, `low`, `very_low`, `unknown`.
- **`approx_rank`**: Integer or `null`. Only include if a specific ranking is stated in sources.
- **`trend`**: Use 'unknown' if no trend data available.

### Clan Association

- **`is_scottish_name`**: `true` if name has any Scottish association (clan, sept, territorial, or historical presence), even if originally from elsewhere.
- **`clan_sept_of`**: Array of clan names (e.g., ['Clan MacDonald']).
- **`official_status`**: 
  - `recognized_by_Lyon`: Formally recognized by Court of the Lord Lyon
  - `traditional_association`: Long-standing traditional link but not formally recognized
  - `marketing_only`: Commercial association without historical basis
  - `none`: No association
  - `unknown`: Association unclear

### Heraldry

- **`has_documented_arms`**: Set to `true` only if `arms` array has entries. Otherwise `false`.
- **`arms`**: Each entry must have `armiger_name` (individual, not surname).
- **`mottoes`**: Can be associated with arms or standalone.
- **`tartans`**: Include `status` (clan, family, fashion, corporate, other, unknown).

### Variants

- **`canonical_form`**: Should match database `name` field unless there's a specific reason to differ.
- **`variant_spellings`**: Simple array for orthographic variants.
- **`related_surnames`**: Array of objects for names needing relationship explanation.

### Migration

- **`phases`**: Array of objects. Each phase should have `period`, `from_regions`, `to_regions`, `drivers`, `evidence_hint`.
- **`uncertainty_flags`**: Use to note when evidence is generic or surname-specific evidence is lacking.

### Notables

- **`people`**: Array of objects. Each must have verifiable documentation.
- **`notability_type`**: Categorize each person (politics, military, arts, scholarship, business, religion, sport, other).
- **`birth_year`/`death_year`**: Use `null` for unknown, not `0`.
- **`approximate_dates`**: `true` if years are estimated.

### Cultural Notes

- **`stereotypes_legends`**: Record documented associations, or 'none known' if genuinely empty.
- **`literary_or_media_references`**: Distinguish `fictional` vs `real`.
- **`cultural_summary`**: Explicitly state if no special associations are known.

### Genealogy Resources

- **`family_societies`**: Include `url` if permitted, otherwise descriptive identifier.
- **`published_histories`**: Include `year` (use `null` if unknown, not `0`).
- **`record_rich_areas`**: Specify `record_types` array (parish_registers, kirk_session, sasines, tax_lists, census, other).
- **`research_tips`**: Practical, surname-specific advice.

---

## Final Instructions for LLM

For each surname:

1. **Start from the template JSON structure.** Only populate fields where evidence exists.

2. **Check the database first:**
   - Review existing `is_clan`, `is_canonical`, `has_history` flags.
   - Check `family_spellings`, `family_septs`, `family_aliases` for existing relationships.
   - Check `family_resources` for existing history texts.

3. **Fill the JSON fields** based on the best available evidence.

4. **Use `uncertainty_flags` and notes** to highlight weak spots or disputes.

5. **Prefer brevity, clarity, and honesty** over speculation.

6. **If in doubt, mark information as uncertain** rather than inventing detail.

7. **For very rare surnames with minimal documentation**, a brief entry with high uncertainty is preferable to speculation.

8. **If only one source is found**, note this in `metadata.research_confidence` and consider using 'low' confidence.

9. **Cross-reference with database relationships** - don't duplicate existing data, but verify and enhance it.

10. **Remember:** All fields are optional. It's better to leave a field empty or null than to fill it with speculation.

---

## Quality Checklist

Before finalizing a research entry, verify:

- [ ] No invented dates, people, or records
- [ ] All years use `null` for unknown (not `0`)
- [ ] `has_documented_arms` matches whether `arms` array has entries
- [ ] `is_scottish_name` reflects any Scottish association
- [ ] `variant_spellings` vs `related_surnames` distinction is clear
- [ ] `canonical_form` matches database `name` (unless reason to differ)
- [ ] Uncertainty flags used where evidence is weak
- [ ] Sources are cited (short identifiers or URLs if allowed)
- [ ] Cross-checked with database existing relationships
- [ ] Confidence levels are honest assessments
- [ ] No generic "family arms" claims
- [ ] Distinction between surname-specific and generic patterns is clear

---

## Example: Handling Uncertainty

**Good:**
```json
{
  "early_records": {
    "earliest_attestation": {
      "year": null,
      "approximate": true,
      "location": "possibly Aberdeenshire",
      "jurisdiction": "Scotland",
      "spelling": null,
      "record_type": null,
      "source_hint": null,
      "notes": "No specific early records found. Name may appear in 15th-century charters but exact date and location uncertain."
    },
    "record_confidence": "low",
    "record_notes": "Evidence is sparse. Name may be older than documented records suggest."
  }
}
```

**Bad:**
```json
{
  "early_records": {
    "earliest_attestation": {
      "year": 1450,
      "approximate": false,
      "location": "Aberdeenshire",
      "jurisdiction": "Scotland",
      "spelling": "MacDonald",
      "record_type": "charter",
      "source_hint": null,
      "notes": ""
    },
    "record_confidence": "high",
    "record_notes": ""
  }
}
```
*(This is bad because it invents a specific date and location without evidence)*

---

This guide should be used in conjunction with the JSON schema documentation in `docs/families_database.md`.

