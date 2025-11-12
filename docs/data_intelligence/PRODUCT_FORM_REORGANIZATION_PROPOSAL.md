# Product Form Reorganization Proposal
**Date:** 2025-11-12  
**Status:** Proposal  
**Goal:** Reorganize product_form categories from a consumer perspective

---

## Current State Analysis

### Current Product Form Distribution
- **clothing**: 455 products (39.3%)
- **accessory**: 342 products (29.6%)
- **homeware**: 159 products (13.7%)
- **jewellery**: 150 products (13.0%)
- **artwork**: 39 products (3.4%)
- **stationery**: 4 products (0.3%)
- **bags**: 3 products (0.3%)
- **pets**: 2 products (0.2%)
- **haberdashery**: 1 product (0.1%)
- **toy**: 1 product (0.1%)
- **voucher**: 1 product (0.1%)

**Total: 1,157 products across 11 categories**

---

## Problems with Current Organization

### 1. **Accessory is Ambiguous**
- **342 products** labeled as "accessory"
- Could be:
  - Clothing accessories (ties, belts, scarves, sporrans)
  - Jewellery accessories (brooches, pins, charms)
  - General accessories (keyrings, wallets)
- From consumer perspective: "Is a kilt pin clothing or jewellery?"

### 2. **Bags Category is Tiny**
- Only **3 products** (gym bags)
- Could be merged with accessories or clothing
- Consumer perspective: "A bag is an accessory, not a separate category"

### 3. **Very Small Categories**
- **haberdashery** (1), **toy** (1), **voucher** (1), **pets** (2), **stationery** (4)
- Total: **9 products** across 5 categories
- Consumer perspective: "These are too small to be separate categories"

### 4. **Conceptual Overlap**
- Accessories vs Clothing vs Jewellery boundaries are unclear
- Stationery could be homeware or office supplies
- Artwork could be homeware (decorative items)

---

## Proposed Reorganization

### Option 1: Consumer-Focused Categories (Recommended)

**Core Principle:** Organize by how consumers think about products, not technical classification.

#### **1. WEARABLES** (797 products)
Everything worn on the body:
- **Clothing** (455): Garments, headwear, footwear
- **Jewellery** (150): Rings, necklaces, bracelets, earrings
- **Accessories** (192): Items worn with clothing/jewellery
  - Clothing accessories: ties, belts, scarves, sporrans, kilt pins
  - Jewellery accessories: brooches, charms, pendants
  - General: wallets, keyrings (if worn/carried)

**Rationale:** Consumer thinks "What can I wear?" - all wearable items together.

#### **2. HOME & LIFESTYLE** (203 products)
Items for home, office, or personal use:
- **Homeware** (159): Quaichs, home decor, kitchen items
- **Stationery** (4): Notebooks, writing supplies
- **Artwork** (39): Paintings, prints, decorative items
- **Bags** (3): Gym bags, totes (if not worn)

**Rationale:** Consumer thinks "What goes in my home/office?" - functional and decorative items.

#### **3. OTHER** (157 products)
Specialty or small categories:
- **Pets** (2): Pet accessories
- **Haberdashery** (1): Sewing supplies
- **Toy** (1): Toys
- **Voucher** (1): Gift vouchers
- **General Accessories** (150): Items that don't fit above (keyrings, wallets if not worn)

**Rationale:** Small categories that don't fit main consumer mental models.

---

### Option 2: Simplified 5-Category System

#### **1. CLOTHING & ACCESSORIES** (797 products)
- Clothing (455)
- Jewellery (150)
- Accessories (192)

#### **2. HOME & DECOR** (201 products)
- Homeware (159)
- Artwork (39)
- Stationery (4)

#### **3. BAGS & LUGGAGE** (3 products)
- Bags (3)

#### **4. SPECIALTY** (9 products)
- Pets (2)
- Haberdashery (1)
- Toy (1)
- Voucher (1)
- Other (4)

#### **5. GENERAL ACCESSORIES** (147 products)
- Non-worn accessories (keyrings, wallets, etc.)

---

### Option 3: Keep Current + Merge Small Categories

**Minimal Change Approach:**
- Keep: clothing, accessory, homeware, jewellery, artwork
- Merge small categories:
  - **bags** → **accessory** (3 products)
  - **stationery** → **homeware** (4 products)
  - **pets, haberdashery, toy, voucher** → **other** (5 products)

**Result:** 7 categories instead of 11

---

## Recommendation: Option 1 (Consumer-Focused)

### Proposed New Categories

1. **WEARABLES** (797 products)
   - Sub-categories: Clothing, Jewellery, Accessories
   - Consumer thinks: "What can I wear?"

2. **HOME & LIFESTYLE** (203 products)
   - Sub-categories: Homeware, Artwork, Stationery, Bags
   - Consumer thinks: "What goes in my home/office?"

3. **OTHER** (157 products)
   - Sub-categories: Pets, Haberdashery, Toy, Voucher, General Accessories
   - Consumer thinks: "Specialty items"

### Benefits
- **Consumer-friendly**: Matches how people shop
- **Logical grouping**: Wearables together, home items together
- **Reduces confusion**: Clear boundaries
- **Scalable**: New products fit into clear categories

### Implementation
- Reclassify products based on core_type and current product_form
- Update database constraint with new valid values
- Update Tag Browser to reflect new organization

---

## Core Type Analysis Context

### Accessory Core Types (Top 10)
1. **kilt_pin** - Clothing accessory (worn with kilt)
2. **sporran** - Clothing accessory (worn with kilt)
3. **tie** - Clothing accessory (worn with shirt)
4. **belt** - Clothing accessory (worn with trousers)
5. **brooch** - Jewellery accessory (worn on clothing)
6. **keyring** - General accessory (not worn)
7. **wallet** - General accessory (not worn)
8. **scarf** - Clothing accessory (worn)
9. **waistcoat** - Clothing (garment)
10. **cufflinks** - Clothing accessory (worn with shirt)

**Observation:** Most accessories are **worn** (clothing or jewellery accessories), not general accessories.

---

## Questions to Resolve

1. **Bags**: Are gym bags "wearables" (carried) or "home & lifestyle" (storage)?
2. **Keyrings/Wallets**: If not worn, are they "other" or "home & lifestyle"?
3. **Artwork**: Is it "home & lifestyle" (decorative) or separate category?
4. **Stationery**: Is it "home & lifestyle" (office supplies) or separate?

---

## Next Steps

1. **Review proposal** with user
2. **Decide on final categories**
3. **Create migration script** to reclassify products
4. **Update database constraint** with new valid values
5. **Update Tag Browser** to reflect new organization
6. **Test and verify** all products correctly classified

---

**Last Updated:** 2025-11-12

