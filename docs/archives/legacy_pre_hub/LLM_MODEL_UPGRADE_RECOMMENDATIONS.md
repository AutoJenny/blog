# LLM Model Upgrade Recommendations
**Date:** 2025-11-11  
**Current Model:** Llama 3.2 (3.2B parameters, Q4_K_M quantization)  
**System:** macOS, Ollama local deployment

---

## Executive Summary

Based on your current setup and tasks, **Llama 3.1 8B** is the recommended upgrade. It offers significantly better accuracy for JSON parsing and structured output tasks while remaining efficient for local deployment. Llama 4 is available but may be overkill for your current needs.

---

## Current System Analysis

### Installed Models
- **llama3.2:latest** - 3.2B parameters, Q4_K_M quantization (~2GB)
- **mistral:latest** - 7.2B parameters, Q4_K_M quantization (~4.4GB)

### Current Usage Tasks
1. **Product Type Classification** - JSON parsing from product titles
2. **Heritage Research Synthesis** - Long-form narrative generation from Wikipedia sources
3. **Query Generation** - Generating Wikipedia search queries
4. **Category Analysis** - Structured JSON output for category heritage

### Performance Requirements
- **Accuracy**: Critical for JSON parsing (product classification)
- **Speed**: Important for bulk processing (1,157 products)
- **Context**: Moderate (Wikipedia articles, product descriptions)
- **Cost**: Must be free (local only, no API costs)

---

## Recommended Upgrades

### 🥇 **Primary Recommendation: Llama 3.1 8B**

**Why This Model:**
- **Significantly better JSON parsing** - 8B parameters vs 3.2B means much better structured output
- **Proven accuracy** - Better instruction following than 3.2
- **Efficient size** - ~4.7GB (Q4_K_M) or ~5.4GB (Q5_K_M), manageable for your system
- **Available now** - Fully supported in Ollama
- **Speed** - Still fast enough for bulk processing

**Installation:**
```bash
# Recommended quantization (best balance)
ollama pull llama3.1:8b

# Or for slightly better quality (larger file)
ollama pull llama3.1:8b-q5_k_m
```

**Expected Improvements:**
- ✅ Better JSON structure compliance (fewer parsing errors)
- ✅ More accurate product type classification
- ✅ Better heritage research synthesis quality
- ✅ Improved instruction following
- ⚠️ Slightly slower than 3.2 (but still very fast)

**Hardware Impact:**
- RAM: ~6-8GB recommended
- VRAM: Works on CPU, better with GPU
- Speed: ~2-3x slower than 3.2, but still fast enough

---

### 🥈 **Alternative: Llama 3.1 70B** (If you have powerful hardware)

**When to Consider:**
- You have 16GB+ RAM and/or powerful GPU
- You need maximum accuracy for critical tasks
- Speed is less important than quality

**Installation:**
```bash
ollama pull llama3.1:70b-q4_k_m  # ~40GB
```

**Trade-offs:**
- ✅ Best accuracy available locally
- ✅ Excellent JSON parsing
- ❌ Much slower (may impact bulk processing)
- ❌ Large file size (~40GB)
- ❌ Requires significant RAM/VRAM

---

### 🥉 **Future Consideration: Llama 4 Maverick** (When available in Ollama)

**Status:** Released April 2025, but availability in Ollama may vary

**Why Consider:**
- 17B active parameters (MoE architecture = efficient)
- Multimodal capabilities (text + images)
- 1M token context window
- 12 language support

**When to Upgrade:**
- When officially available in Ollama
- If you need multimodal features
- If you need very long context windows

**Installation (when available):**
```bash
ollama pull llama4:maverick
```

---

## Other Models to Consider

### **Mistral 7B** (You already have this!)

**Current Status:** Already installed (`mistral:latest`)

**Consideration:**
- You already have it installed
- 7.2B parameters (better than 3.2B)
- Good for general tasks
- **Test it first** - might be sufficient upgrade without downloading new models

**Test Command:**
```bash
# Test with a simple JSON parsing task
ollama run mistral "Parse this product title into JSON: 'Luxury Cashmere Jacobite Shirt'"
```

### **Qwen 2.5 7B** (Alternative option)

**Why Consider:**
- Excellent JSON parsing capabilities
- Strong instruction following
- Good multilingual support
- Efficient size (~4.5GB)

**Installation:**
```bash
ollama pull qwen2.5:7b
```

---

## Implementation Plan

### Phase 1: Test Current Upgrade (Immediate)
1. **Test Mistral 7B** (already installed) with your tasks
   - Run product type parsing on a sample
   - Compare JSON accuracy vs Llama 3.2
   - If good enough, use this (no download needed!)

### Phase 2: Upgrade to Llama 3.1 8B (Recommended)
1. **Download model:**
   ```bash
   ollama pull llama3.1:8b
   ```

2. **Update codebase** (if needed):
   - Current code uses `model='llama3.2'`
   - Change to `model='llama3.1:8b'` in:
     - `utils/product_type_parser.py`
     - `utils/heritage_research/research_synthesizer.py`
     - `utils/heritage_research/query_generator.py`
     - `utils/category_heritage_research.py`

3. **Test on sample tasks:**
   - Product type classification (10 products)
   - Heritage research synthesis (1 category)
   - Compare accuracy vs current model

4. **Full deployment:**
   - Update all model references
   - Monitor performance
   - Adjust if needed

### Phase 3: Monitor and Optimize
- Track JSON parsing error rates
- Monitor processing speed
- Consider Llama 4 when stable in Ollama

---

## Comparison Table

| Model | Size | Accuracy | Speed | JSON Parsing | Best For |
|-------|------|----------|-------|--------------|----------|
| **Llama 3.2** (current) | 2GB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Fast bulk processing |
| **Mistral 7B** (installed) | 4.4GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **Test this first!** |
| **Llama 3.1 8B** | 4.7GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Recommended upgrade** |
| **Llama 3.1 70B** | 40GB | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | Maximum accuracy |
| **Llama 4 Maverick** | ~10GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Future consideration |

---

## Specific Task Analysis

### Product Type Classification (JSON Parsing)
- **Current:** Llama 3.2 sometimes produces invalid JSON
- **Upgrade Impact:** Llama 3.1 8B should significantly reduce JSON errors
- **Recommendation:** ✅ Upgrade to 3.1 8B

### Heritage Research Synthesis
- **Current:** Llama 3.2 produces good narratives but sometimes misses details
- **Upgrade Impact:** Better synthesis of complex Wikipedia content
- **Recommendation:** ✅ Upgrade to 3.1 8B

### Query Generation
- **Current:** Llama 3.2 generates reasonable queries
- **Upgrade Impact:** More precise Wikipedia article title suggestions
- **Recommendation:** ⚠️ Current is fine, but upgrade helps

---

## Cost-Benefit Analysis

### Llama 3.1 8B Upgrade
- **Cost:** Free (local), ~4.7GB disk space
- **Benefit:** Significantly better accuracy, fewer errors, better output quality
- **Risk:** Minimal - can revert to 3.2 if needed
- **ROI:** High - better results with minimal overhead

### Llama 3.1 70B Upgrade
- **Cost:** Free (local), ~40GB disk space, slower processing
- **Benefit:** Maximum accuracy
- **Risk:** May slow down bulk processing significantly
- **ROI:** Medium - better quality but slower

---

## Recommendations Summary

1. **Immediate Action:** Test Mistral 7B (already installed) with your tasks
2. **Primary Upgrade:** Llama 3.1 8B - best balance of accuracy and speed
3. **Future:** Monitor Llama 4 availability in Ollama
4. **Avoid:** DeepSeek V3 (too large, requires specialized hardware)

---

## Next Steps

1. Test Mistral 7B on a sample task
2. If insufficient, download Llama 3.1 8B
3. Update codebase model references
4. Test on sample data
5. Deploy to production
6. Monitor performance

---

## Notes

- All models are free and open-source
- Ollama handles quantization automatically
- You can run multiple models and switch as needed
- Current Llama 3.2 can remain as fallback
- Model files are stored in `~/.ollama/models/`

