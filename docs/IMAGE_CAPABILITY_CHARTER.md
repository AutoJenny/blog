# Image Capability Charter

**Status:** Normative / authoritative  
**Audience:** Coders, content engineers, reviewers  
**File:** `docs/IMAGE_CAPABILITY_CHARTER.md`

This document defines what images are allowed to be across the CLAN system. It is authoritative over channel-specific implementations. It does not define pipelines, tooling, or prompts.

---

## 1. Purpose and scope

- Define what images are allowed to be across the CLAN system.
- Apply to all channels (current and future).
- Do not define pipelines, tooling, or prompts.
- This document is authoritative over channel-specific implementations.

---

## 2. Core principles (non-negotiable)

- Images must support credibility, clarity, and trust.
- Images must not imply false historical or documentary accuracy.
- Preview must match publish for all channels.
- Image handling must be deterministic and auditable.
- Editorial intent must be clear from the image class alone.

---

## 3. Image classes (canonical)

Each image used by the system MUST belong to exactly one class.

### 3.1 product_photography

- **Source:** CLAN product catalogue only.
- **No generation.**
- **No modification** beyond resize/crop.
- **No price overlays.**
- **Attribution:** implicit (product data).

### 3.2 public_domain_historical

- **Source:** verified public-domain repositories.
- **Used for:** heritage, authority, depth content.
- **Must not** be cropped or edited in ways that change meaning.
- **Attribution required** (source + PD note).

### 3.3 generated_editorial_illustration

- **Purpose:** illustrative, atmospheric, symbolic.
- **MUST NOT:**
  - Depict named historical individuals.
  - Depict specific historical events as factual scenes.
  - Appear photographic.
- **Acceptable styles:**
  - Engraving / etching.
  - Pen-and-ink.
  - Watercolour wash.
  - Abstracted landscape.
- **Disclosure:** required (policy defined below).

### 3.4 typographic_card

- **Text-first visual.**
- **Used for:** reassurance, authority, language, emphasis.
- **No illustrative claims.**
- **No attribution required** beyond brand.

### 3.5 diagrammatic_or_abstract

- Maps, timelines, symbolic layouts.
- May be generated or hand-authored.
- Must not claim historical precision unless sourced.

---

## 4. Credibility and heritage safeguards

- Generated images are **editorial illustrations**, not evidence.
- Historical accuracy is carried by **text**, not imagery.
- **When in doubt:**
  - Prefer abstraction.
  - Prefer typography.
  - Prefer public-domain material.

These rules exist to protect:

- Heritage credibility.
- Reader trust.
- Legal and reputational risk.

---

## 5. Provenance, attribution, and disclosure

### 5.1 Content provenance

- Source of facts, language, or ideas.
- Already handled elsewhere.
- Not image-specific.

### 5.2 Image attribution

- **Required for:**
  - Public-domain historical images.
  - External images (where applicable).
- **Stored as metadata.**
- May or may not render visually depending on channel.

### 5.3 AI / generated disclosure

- **Required for** `generated_editorial_illustration`.
- **Must be:**
  - Non-prominent.
  - Consistent across channels.
- Exact rendering (text vs metadata vs caption note) is channel-specific.

---

## 6. Channel binding rules

**Channels may:**

- Render images differently.
- Place attribution differently.

**Channels must not:**

- Change image class semantics.
- Suppress required disclosure.
- Break preview/publish parity.

---

## 7. Failure and fallback policy

If an image is unavailable or invalid:

1. **Fallback to** `typographic_card`.
2. **Log** the failure.
3. **Do not** silently substitute another image class.

---

## 8. Relationship to other documents

This charter:

- **Governs** image use across:
  - Social
  - Blog
  - Newsletter
- **Is referenced by:**
  - Channel preview system
  - Channel executors
  - Future KB summaries

See also:

- [PREVIEW_FACEBOOK_MATCH_PUBLISH.md](PREVIEW_FACEBOOK_MATCH_PUBLISH.md) — Preview/publish parity (Facebook).
- [UNIFIED_CHANNEL_PREVIEW_SYSTEM.md](UNIFIED_CHANNEL_PREVIEW_SYSTEM.md) — Channel preview architecture.

---

## Appendix: Image Capability Checklist (New Channel)

This is what a coder must tick before adding a new channel. Derived directly from this charter; enforceable.

### A. Classification

- [ ] Every image used by the channel maps to a defined image class.
- [ ] No ad-hoc or undefined image types introduced.

### B. Credibility

- [ ] Generated images are illustrative, not documentary.
- [ ] No generated depictions of named historical individuals.
- [ ] No generated “fake history photography”.

### C. Attribution & disclosure

- [ ] Image attribution metadata supported where required.
- [ ] AI-generated disclosure implemented for generated illustrations.
- [ ] Disclosure is consistent between preview and publish.

### D. Preview / publish parity

- [ ] Preview renders the same image(s) and captions as publish.
- [ ] No preview-only or publish-only image substitutions.

### E. Determinism & auditability

- [ ] Image selection is deterministic.
- [ ] Failures are logged.
- [ ] Fallback behaviour is explicit and tested.

### F. Fallback safety

- [ ] Missing images fall back to typographic cards.
- [ ] No silent degradation to “whatever image exists”.

### G. Documentation

- [ ] Channel doc references IMAGE_CAPABILITY_CHARTER.
- [ ] Any deviations are explicitly justified in writing.

---

For implementation routing, see docs/IMAGE_CAPABILITIES_INDEX.md
