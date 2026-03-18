# ClanGuide — AI Front-End Assistant Planning Document
**Date:** 2025-11-10
**Project:** CLAN.com AI Customer & Knowledge Assistant  
**Working Name:** ClanGuide

---

## 1. Overview
ClanGuide is the unified AI assistant for CLAN.com. It serves as an intelligent front-end interface for customers and visitors, providing contextual responses using the CLAN knowledge base, product catalogue, and curated service data. It is designed to reflect CLAN’s tone of voice—professional, Scottish, and authentic—while maintaining data accuracy, security, and efficiency.

ClanGuide supports three operational modes:
1. **Customer Service Mode:** Handles questions related to orders, returns, bespoke measurements, and shipping by referencing the `/help` dataset.  
2. **Knowledge Mode:** Provides cultural, product, and heritage information using the `/knowledge` dataset.  
3. **Companion Mode:** Offers conversational assistance, cross-linking to relevant services and learning materials.

---

## 2. Front-End Functionality

### 2.1 Interface Features
- Persistent chat widget (“Ask ClanGuide”) on all pages.  
- Modal and full-page chat views.  
- Context detection: identifies the page context (e.g., product, family, help) to bias answers.  
- Inline link cards for internal services (returns, measuring, contact).  
- Tiered responses:  
  - Tier 1: Authoritative CLAN sources (Help & Knowledge Base)  
  - Tier 2: Curated external sources (if no CLAN match)  
- Embedded reference links (“From CLAN Help: Measuring Kilts”).  
- Escalation option: “Contact our team” → directs to support form or chat escalation.

### 2.2 Personalisation & Tone
- LoRA-tuned model on historical service emails to maintain CLAN tone (warm, succinct, professional Scottish hospitality).  
- Uses style tags (`<voice:clan>`, `<topic:measure>` etc.) for consistent phrasing.  
- Multi-turn memory limited to current session (privacy by design).

### 2.3 Accessibility
- Keyboard-navigable and screen-reader compatible.  
- Localisation-ready (English first; future Gaelic layer possible).

---

## 3. Back-End Architecture

### 3.1 Core Components
| Component | Description |
|------------|--------------|
| **LLM Gateway** | Connects user queries to orchestration layer controlling retrieval and synthesis. |
| **Retriever Tier A** | CLAN’s local FAISS/HNSW index built from Help, Knowledge, and Product exports. |
| **Retriever Tier B** | Curated general corpus (Wikipedia snapshot, textiles standards, etc.) for fallback context. |
| **Re-Ranker** | Cross-encoder model ensures top-5 CLAN documents most relevant. |
| **Coverage Gate** | Confidence metric controlling when to include Tier B fallback. |
| **Response Composer** | Assembles final answer with citations and service link resolver. |

### 3.2 Data Sources
| Source | Description | Update Cycle |
|---------|--------------|---------------|
| `/help` | Customer service articles | Weekly incremental |
| `/knowledge` | Product and cultural information | Weekly incremental |
| `Products DB` | Catalogue of product names, descriptions, attributes, media | Daily |
| `Directory Map` | Site structure and URLs for contextual navigation | Weekly |
| `Customer Service Email Archive` | Redacted corpus for tone fine-tuning | Quarterly |

### 3.3 Local Indexes
- `articles.jsonl`, `products.jsonl`, and `chunks.jsonl` used for retrieval.  
- Indexed with metadata: `type`, `intent`, `path`, `url`, `tags`, `last_reviewed`.  
- Embeddings: E5-large or bge-large.  
- Vector store: FAISS/HNSW (local; SQLite metadata).

---

## 4. Data Preparation & Normalisation

### 4.1 Cleansing Process
1. **Extraction:** Raw SQL or spidered HTML → exported via `export_corpus.py`.  
2. **Conversion:** HTML → Markdown; Markdown → JSONL with YAML front-matter.  
3. **Deduplication:** Canonical URLs retained; 301s mapped in redirects.csv.  
4. **Redaction:** Remove PII (emails, addresses, order refs, phone numbers).  
5. **Field Normalisation:** Convert tags, media, attributes to JSON arrays.  
6. **Chunking:** 800–1200 tokens per section with overlap of 300 characters.

### 4.2 Efficiency Optimisation
- Pre-compute embeddings for each chunk.  
- Cache popular retrieval results in Redis.  
- Compress indexes using product-level partitioning (help vs knowledge vs product).

### 4.3 Security
- Access to LLM indexes restricted to internal network.  
- Fine-tuning corpus stripped of all personal identifiers.  
- Logs stored separately with hashed session IDs only.

---

## 5. Update & Maintenance Protocols

### 5.1 Scheduled Automation
| Task | Frequency | Method |
|------|------------|--------|
| Extract latest content from DB | Daily | Cron + `export_corpus.py` |
| Rebuild vector indexes | Weekly | Automated FAISS rebuild job |
| Fine-tune style model | Quarterly | LoRA refresh using new redacted emails |
| Validate broken links | Weekly | Automated link checker |
| Backup and archive indexes | Daily | rsync to internal backup node |

### 5.2 Quality Assurance
- **Coverage tests:** 200–500 gold QA pairs checked per release.  
- **Tone QA:** 5% random samples audited manually for brand alignment.  
- **Security QA:** automatic PII scan on each export.

---

## 6. Integration with CLAN Infrastructure

### 6.1 APIs
- REST endpoint `/api/clanguide/query` for front-end widget.  
- Internal API `/api/clanguide/update` triggered by scheduled export job.  
- Admin dashboard for monitoring usage, top queries, and missed intents.

### 6.2 Monitoring
- Metrics: retrieval latency, CLAN vs. global coverage ratio, user satisfaction.  
- Dashboards in Grafana/Prometheus.

### 6.3 Escalation Path
If confidence < threshold or user requests human help → forward to customer service inbox with chat transcript.

---

## 7. Future Extensions
- Voice interface for spoken Q&A.  
- Multimodal search (upload tartan photo → identify pattern).  
- Real-time translation for Gaelic or EU languages.  
- Generative summary mode for newsletters or articles derived from Knowledge Base.

---

## 8. Governance & Compliance
- Follows GDPR and UK Data Protection Act.  
- Redacted datasets stored under secure internal license.  
- Opt-out for customers included in any training dataset.  
- Regular Data Protection Impact Assessments (DPIA) logged.

---

## 9. Summary
ClanGuide merges CLAN’s distinctive heritage voice with modern AI capabilities. By prioritising internal knowledge and linking to CLAN services first, it offers users authoritative, trustworthy, and distinctly Scottish guidance—scalable, maintainable, and aligned with brand values.
