# Phase 2 Next Steps - Setup Instructions
**Date:** 2025-01-10  
**Status:** Implementation Complete, Setup Required

---

## Setup Checklist

### ✅ Completed
- [x] Phase 2 code implementation
- [x] All modules created and tested
- [x] API endpoints implemented
- [x] Prompt templates migration created
- [x] File size compliance verified

### ⏳ Required Setup Steps

#### 1. Install Python Dependencies

**Option A: User Installation (Recommended)**
```bash
python3 -m pip install --user sentence-transformers faiss-cpu
```

**Option B: Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install sentence-transformers faiss-cpu numpy
```

**Option C: System-wide (if you have permissions)**
```bash
pip install sentence-transformers faiss-cpu numpy
```

**Verify Installation:**
```bash
python3 -c "import sentence_transformers; import faiss; print('✅ Dependencies installed')"
```

---

#### 2. Run Prompt Templates Migration

**Using psql:**
```bash
psql -d your_database_name -f migrations/20250110_seed_content_generation_prompts.sql
```

**Or using Python:**
```python
from config.database import db_manager

with open('migrations/20250110_seed_content_generation_prompts.sql', 'r') as f:
    sql = f.read()

with db_manager.get_cursor() as cursor:
    cursor.execute(sql)
```

**Verify:**
```sql
SELECT name FROM llm_prompt 
WHERE name IN ('product_content_generation', 'category_content_generation', 'product_comparison_generation');
```

---

#### 3. Run Phase 1: Generate Embeddings

**First, ensure Phase 1 migration is run:**
```bash
psql -d your_database_name -f migrations/20250110_create_content_chunks_table.sql
```

**Then generate embeddings:**
```bash
python3 scripts/generate_embeddings.py --products --categories
```

**This will:**
- Create chunks from all products and categories
- Generate embeddings for each chunk
- Build FAISS index
- Save index to `data/vector_index/`

**Expected output:**
- Processed X products
- Processed Y categories
- Generated embeddings
- FAISS index created with Z vectors

---

#### 4. Test API Endpoints

**Start Flask app:**
```bash
python3 unified_app.py
```

**Test Preview Endpoint:**
```bash
curl -X POST http://localhost:5000/api/content/preview \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "product",
    "source_id": 1,
    "generation_type": "deep_dive"
  }'
```

**Test Generation Endpoint:**
```bash
curl -X POST http://localhost:5000/api/content/generate \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "product",
    "source_id": 1,
    "generation_type": "deep_dive"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "post_id": 123,
  "title": "Generated Headline",
  "standfirst": "Generated summary",
  "sections": [
    {
      "section_id": 1,
      "heading": "Section 1",
      "content": "Generated content..."
    }
  ]
}
```

---

## Troubleshooting

### Dependencies Not Installing

**Issue:** `pip` command not found or permission denied

**Solutions:**
1. Use `python3 -m pip` instead of `pip`
2. Use `--user` flag: `python3 -m pip install --user ...`
3. Use virtual environment (recommended)
4. Check if dependencies are in `requirements.txt` and install all: `pip install -r requirements.txt`

### Database Connection Issues

**Issue:** Cannot connect to database

**Check:**
1. Database credentials in `.env` or config
2. Database server is running
3. Network connectivity

### Embedding Generation Fails

**Issue:** Model download fails or timeout

**Solutions:**
1. Check internet connection (model downloads on first use)
2. Increase timeout in code if needed
3. Pre-download model: `python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/e5-large-v2')"`

### FAISS Index Issues

**Issue:** Index creation fails

**Check:**
1. `data/vector_index/` directory exists and is writable
2. Sufficient disk space
3. FAISS version compatibility

---

## Verification Steps

After setup, verify everything works:

1. **Check Dependencies:**
   ```bash
   python3 -c "import sentence_transformers; import faiss; import numpy; print('✅ All dependencies available')"
   ```

2. **Check Prompts:**
   ```sql
   SELECT COUNT(*) FROM llm_prompt WHERE name LIKE '%content_generation%';
   -- Should return 3
   ```

3. **Check Chunks:**
   ```sql
   SELECT COUNT(*) FROM content_chunks;
   -- Should return number of products + categories
   ```

4. **Check FAISS Index:**
   ```bash
   ls -lh data/vector_index/
   # Should see products_categories.faiss and products_categories_metadata.json
   ```

5. **Test API:**
   ```bash
   curl http://localhost:5000/api/content/search -X POST -H "Content-Type: application/json" -d '{"query": "test", "limit": 1}'
   ```

---

## Next Phase

Once Phase 2 is fully set up and tested:
- **Phase 3:** User Interface integration
- Add generation UI to calendar
- Create generation modal
- Add idea suggestion panel

---

**Status:** Ready for setup  
**Last Updated:** 2025-01-10

