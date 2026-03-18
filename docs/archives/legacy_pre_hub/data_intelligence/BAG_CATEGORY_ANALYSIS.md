# Bag Category Analysis
**Date:** 2025-11-12  
**Status:** Analysis Complete  
**Finding:** 48 bag-related products scattered across 7 product_form categories

---

## Summary

**Total bag-related products: 48** (not 3 as initially thought)

### Distribution by Current Product Form

| Product Form | Count | Types |
|-------------|-------|-------|
| **accessory** | 20 | Backpacks (5), purses (4), pencil cases (2), bags (4), purse mirrors (3), charms (2) |
| **artwork** | 12 | Tote bags (9), shopping bags (3) |
| **homeware** | 6 | Flasks (2), wallets (1), treat bags (2), oddments bag (1) |
| **clothing** | 3 | Duffle bags (2), backpack (1) |
| **bags** | 3 | Gym bags (2), clutch bag (1) |
| **jewellery** | 3 | Drawstring bags (3) - **misclassified** |
| **stationery** | 1 | Pencil case (1) |

---

## Bag Types Found

### Functional Bags (Carried/Worn)
- **Backpacks**: 6 products (accessory: 5, clothing: 1)
- **Duffle bags**: 2 products (clothing)
- **Gym bags**: 2 products (bags)
- **Crossbody bags**: 3 products (accessory)
- **Bum bags**: 1 product (accessory)
- **Clutch bags**: 1 product (bags)

### Storage/Container Bags
- **Tote bags**: 9 products (artwork)
- **Shopping bags**: 3 products (artwork)
- **Drawstring bags**: 3 products (jewellery) - **misclassified**
- **Pencil cases**: 3 products (accessory: 2, stationery: 1)
- **Oddments bag**: 1 product (homeware)

### Small Personal Items
- **Purses**: 4 products (accessory)
- **Purse mirrors**: 3 products (accessory)
- **Wallets**: 1 product (homeware)
- **Treat bags**: 2 products (homeware)

### Questionable Classifications
- **Charms** (2): "Bagpiper Charm", "Bagpipes Charm" - not actual bags
- **Drawstring bags** (3): Currently in jewellery, should be bags/accessories
- **Purse flasks** (2): Flasks, not bags (homeware correct)

---

## Issues Identified

### 1. **Inconsistent Classification**
- Same bag type in different categories:
  - Backpacks: accessory (5) + clothing (1)
  - Pencil cases: accessory (2) + stationery (1)
  - Drawstring bags: jewellery (3) - **wrong category**

### 2. **Misclassification**
- **Drawstring bags** (3) in jewellery - these are storage bags, not jewellery
- **Tote bags** (9) in artwork - these are functional bags, not artwork
- **Shopping bags** (3) in artwork - these are functional bags, not artwork

### 3. **Category Confusion**
- **Artwork** contains 12 functional bags (tote bags, shopping bags)
- **Jewellery** contains 3 storage bags (drawstring bags)
- **Homeware** contains some bags (treat bags, oddments bag) - may be correct

---

## Recommendations

### Option 1: Create Dedicated "BAGS" Category (Recommended)

**Consolidate all bag types into single "bags" category:**
- Backpacks, duffle bags, gym bags, crossbody bags, bum bags, clutch bags
- Tote bags, shopping bags, drawstring bags
- Pencil cases (if considered bags)
- **Total: ~35-40 products**

**Keep separate:**
- Purses, wallets (small personal items - could be accessory)
- Purse mirrors (not bags)
- Treat bags (pet-specific - could stay in pets/homeware)
- Oddments bag (fabric storage - could stay in homeware)

### Option 2: Split by Function

**Carried Bags** (accessory):
- Backpacks, duffle bags, gym bags, crossbody bags, bum bags, clutch bags
- **~15 products**

**Storage Bags** (homeware or new category):
- Tote bags, shopping bags, drawstring bags, pencil cases
- **~15 products**

**Small Personal Items** (accessory):
- Purses, wallets
- **~5 products**

### Option 3: Consumer Perspective

**Functional Bags** (new "bags" category):
- All bags that are carried or used for storage
- Backpacks, duffle bags, gym bags, tote bags, shopping bags, drawstring bags, pencil cases
- **~30 products**

**Small Accessories** (accessory):
- Purses, wallets, purse mirrors
- **~8 products**

---

## Impact on Reorganization Proposal

This finding significantly changes the reorganization:

### Revised Numbers
- **Current "bags" category**: 3 products (incomplete!)
- **Actual bag-related products**: 48 products
- **Should be consolidated**: ~35-40 products into dedicated "bags" category

### Updated Proposal Considerations

1. **Bags are substantial**: 48 products (4.1% of catalog) - deserves own category
2. **Current classification is broken**: Bags scattered across 7 categories
3. **Consumer perspective**: "Bags" is a clear, understandable category
4. **Consolidation needed**: Reclassify 35-40 products from other categories

---

## Next Steps

1. **Decide on bag definition**: What counts as a "bag"?
   - Include pencil cases? (storage containers)
   - Include purses/wallets? (small personal items)
   - Include treat bags? (pet-specific)

2. **Create reclassification script**: Move bag products to "bags" category

3. **Update database constraint**: Add "bags" to valid product_form values (if not already)

4. **Update reorganization proposal**: Reflect actual bag count (48, not 3)

---

**Last Updated:** 2025-11-12

