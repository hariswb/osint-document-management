# Design Document: Local OSINT NER & Network Viz Tool

> **Version:** 1.0.0  
> **Last Updated:** 2026-03-06  
> **Status:** Planning Phase

## Table of Contents

1. [Project Context](#1-project-context)
2. [Core Constraints](#2-core-constraints)
3. [Technology Stack](#3-technology-stack)
4. [Architecture & Data Flow](#4-architecture--data-flow)
5. [Module Specifications](#5-module-specifications)
6. [Error Handling & Resilience](#6-error-handling--resilience)
7. [Performance Optimization](#7-performance-optimization)
8. [Security Considerations](#8-security-considerations)
9. [Deployment Strategy](#9-deployment-strategy)
10. [Development Roadmap](#10-development-roadmap)
11. [Appendix](#11-appendix)

---

## 1. Project Context

### 1.1 Overview

This project is an open-source desktop application designed for investigative journalists to extract, catalog, and visualize networks of actors (people, companies, organizations) from Indonesian text.

### 1.2 Primary Workflows

The application supports two primary workflows:

1. **Passive Mode:** Processing manually uploaded local documents (PDFs, HTML, TXT).
2. **Active Mode (OSINT):** Accepting a user prompt, searching the live web for relevant articles, intelligently scraping the content, and extracting the relevant actors.

### 1.3 Privacy & Security Principles

Despite having active web-search capabilities, all AI inference (Embedding and NER) and data storage still occur entirely on the user's local machine to ensure privacy and security. The application follows a "zero-trust cloud" principle where external services are used only for fetching public data.

### 1.4 Target Users

- Investigative journalists working with Indonesian sources
- Researchers analyzing corporate/political networks
- NGOs tracking organizational relationships
- Fact-checkers verifying claims across multiple sources

## 2. Core Constraints

### 2.1 Deployment Constraints

- **Zero-Configuration Deployment:** The app must be delivered as a standard Windows installer (`.exe` or `.msi`). The user must not need to manage Python, virtual environments, or complex dependencies.
- **Installation Size:** Target total installation size < 2GB (including models)
- **Installation Time:** Complete installation should take < 5 minutes on standard broadband

### 2.2 Network & Privacy Constraints

- **Network Requirements:** The application requires internet access *only* for fetching search engine results and scraping target URLs.
- **Data Sovereignty:** No user data, scraped text, or model telemetry is sent to external servers for processing.
- **Offline Capability:** Previously processed data and local document analysis must work without internet connection.
- **Proxy Support:** Must support HTTP/HTTPS proxies for users in restricted network environments.

### 2.3 Performance Constraints

- **Efficient Memory Management:** Because we are now running *two* ML models simultaneously (`pplx-embed` and `cahyaBert`), the Python sidecar must manage memory aggressively.
- **Target Hardware:** Must run smoothly on standard journalist laptops:
  - Minimum: 8GB RAM, dual-core CPU, 256GB storage
  - Recommended: 16GB RAM, quad-core CPU, 512GB SSD
- **Response Time:**
  - Web search: < 10 seconds for 10 URLs
  - Document upload: < 5 seconds for 10MB file
  - Network visualization: < 2 seconds for 1000 nodes

### 2.4 Usability Constraints

- **Language Support:** Primary UI in Bahasa Indonesia and English
- **Accessibility:** Must follow WCAG 2.1 Level AA guidelines
- **Learning Curve:** New users should be productive within 30 minutes

## 3. Technology Stack

This architecture uses the Tauri Sidecar pattern to bind a modern web interface to a heavy, localized Python processing pipeline.

### 3.1 Application Shell

**Technology:** Tauri (Rust + Edge WebView2 on Windows)  
**Rationale:** 
- Smaller bundle size than Electron (~10MB vs ~150MB)
- Native security features from Rust
- Better resource management
- Single-codebase for future macOS/Linux support

### 3.2 Frontend UI & Visualization

**Framework:** **React** with TypeScript  
**Rationale:**
- Largest ecosystem and community support
- Excellent TypeScript integration
- Rich component libraries available

**Visualization:** **D3.js** + **React Flow**  
**Rationale:**
- D3.js for custom interactive network graphs
- React Flow for simpler relationship diagrams
- Both support large datasets with virtualization

**UI Components:** **Radix UI** + **Tailwind CSS**  
**Rationale:**
- Accessible by default
- Unstyled components allow full customization
- Smaller bundle size than Material-UI

### 3.3 Backend API (Sidecar)

**Framework:** **Python 3.11+** with **FastAPI**  
**Rationale:**
- Native async support for concurrent scraping
- Automatic OpenAPI documentation
- Excellent type hints support
- Easy testing with pytest

### 3.4 Web Search & Scraping Engine

**Search:** **DuckDuckGo-Search (`duckduckgo-search`)**  
**Rationale:**
- No API keys required
- Lightweight and fast
- Respects user privacy
- Fallback to Google Custom Search API (optional, user-provided key)

**Scraping:** **Scrapling (`D4Vinci/Scrapling`)**  
**Rationale:**
- Bypasses basic anti-bot protections
- Adaptive to different page structures
- Clean text extraction
- Handles dynamic content

**Alternative/Fallback:** **Playwright** for JavaScript-heavy sites  
**Usage:** Only when Scrapling fails (increases bundle size)

### 3.5 NLP & Semantic Processing

**Embedding Model:** `perplexity-ai/pplx-embed-v1-0.6b`  
**Runtime:** Hugging Face `transformers` with PyTorch  
**Model Size:** ~1.2GB  
**Rationale:**
- State-of-the-art performance for semantic search
- Fast inference even on CPU
- Optimized for retrieval tasks
- Alternative: Export to ONNX for 30% faster inference

**NER Model:** `cahya/bert-base-indonesian-NER`  
**Runtime:** Hugging Face `transformers` with PyTorch  
**Model Size:** ~450MB  
**Entity Types:** PERSON, ORGANIZATION, LOCATION, EVENT, DATE  
**Rationale:**
- Specifically trained on Indonesian text
- Good balance of accuracy and speed
- Active maintenance and community

**Model Optimization Strategy:**
1. Load models lazily (only when needed)
2. Share transformer backbone between models where possible
3. Quantize models to INT8 (reduces size by 4x, minimal accuracy loss)
4. Use model caching to avoid reloading

### 3.6 Databases

**Vector Store:** **FAISS** (in-memory with optional disk persistence)  
**Rationale:**
- Fastest similarity search for dense vectors
- Minimal dependencies
- Works well in-memory for temporary search
- No external service required

**Alternative:** **ChromaDB** (if persistent vector store needed)

**Relational Store:** **DuckDB**  
**Storage Location:** `%APPDATA%/osint-tool/data/projects/`  
**Rationale:**
- Analytical queries are faster than SQLite for complex aggregations
- Built-in full-text search (no external extension needed)
- Better compression for large datasets
- Column-oriented storage ideal for entity/relationship analysis
- Native JSON support for storing aliases and metadata
- SQL compatibility with PostgreSQL syntax

**Schema:**
```sql
-- Core tables
CREATE TABLE entities (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,
    type VARCHAR CHECK(type IN ('PERSON', 'ORG', 'LOCATION', 'EVENT')),
    aliases JSON, -- Array of alternative names
    first_seen TIMESTAMP,
    last_updated TIMESTAMP,
    frequency INTEGER DEFAULT 1,
    metadata JSON -- Additional entity metadata
);

CREATE TABLE relationships (
    id INTEGER PRIMARY KEY,
    source_id INTEGER REFERENCES entities(id),
    target_id INTEGER REFERENCES entities(id),
    type VARCHAR,
    confidence FLOAT,
    source_url VARCHAR,
    extracted_date TIMESTAMP,
    evidence_text VARCHAR -- Context where relationship was found
);

CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    url VARCHAR UNIQUE,
    title VARCHAR,
    domain VARCHAR, -- Extracted domain for filtering
    scraped_date TIMESTAMP,
    processed BOOLEAN DEFAULT false,
    scrape_success BOOLEAN,
    error_message VARCHAR,
    content_hash VARCHAR(64) -- SHA-256 for deduplication
);

-- Full-text search index
CREATE INDEX idx_entities_name_fts ON entities USING GIN (name);
CREATE INDEX idx_sources_title_fts ON sources USING GIN (title);

-- Performance indexes
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_relationships_source ON relationships(source_id);
CREATE INDEX idx_relationships_target ON relationships(target_id);
CREATE INDEX idx_sources_domain ON sources(domain);
```

### 3.7 Packaging & Distribution

**Python Bundler:** **PyInstaller** with `--onedir` mode  
**Tauri Builder:** Built-in Windows installer generator  
**Auto-Update:** **Tauri's built-in updater** with signed releases

**Bundle Structure:**
```
osint-tool/
├── osint-tool.exe (Tauri app)
├── resources/
│   └── sidecar/
│       ├── python-sidecar.exe
│       ├── models/
│       │   ├── pplx-embed-quantized.onnx (~300MB)
│       │   └── cahya-ner-quantized.onnx (~120MB)
│       └── python311.dll + dependencies
└── data/
    └── projects/
```

### 3.8 Development Tools

- **Testing:** pytest + pytest-asyncio (backend), Vitest + Testing Library (frontend)
- **Linting:** Ruff (Python), ESLint + Prettier (TypeScript)
- **Type Checking:** mypy (Python), TypeScript strict mode
- **Documentation:** MkDocs (user docs), TypeDoc (API docs)
- **CI/CD:** GitHub Actions

## 4. Architecture & Data Flow

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Tauri Application                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Frontend (React + TypeScript)                │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │ │
│  │  │   Query  │  │  Document│  │  Network Graph      │ │ │
│  │  │    UI    │  │  Upload  │  │  Visualization      │ │ │
│  │  └──────────┘  └──────────┘  └──────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │ IPC                              │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            Rust Core (Tauri Runtime)                   │ │
│  │  - Sidecar process management                          │ │
│  │  - File system access                                  │ │
│  │  - Database queries (DuckDB)                            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/WebSocket (localhost)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Python Sidecar (FastAPI Server)                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Web Search & Scraping Pipeline                        │ │
│  │  - DuckDuckGo Search                                   │ │
│  │  - Scrapling (HTML extraction)                         │ │
│  │  - Text chunking                                       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  NLP Pipeline                                          │ │
│  │  - pplx-embed (semantic search)                        │ │
│  │  - cahya-ner (entity extraction)                       │ │
│  │  - FAISS (vector indexing)                             │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Data Layer                                            │ │
│  │  - Entity resolution & deduplication                   │ │
│  │  - Relationship extraction                             │ │
│  │  - DuckDB storage                                      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 OSINT Search Workflow (Detailed)

#### Phase 1: Query Initiation
1. **User Prompt:** User types query in frontend (e.g., "Korupsi tambang nikel Kalimantan")
2. **Query Validation:** Frontend validates query length (min 10 chars, max 500 chars)
3. **Request Dispatch:** Frontend sends HTTP POST to `http://localhost:8000/api/search`

#### Phase 2: Web Search
4. **Search Execution:** Sidecar receives prompt, calls `duckduckgo-search` with:
   - Max results: 10 URLs (configurable)
   - Region: `id-ID` (Indonesia)
   - Timeout: 30 seconds total
5. **Result Filtering:** 
   - Remove duplicate URLs
   - Filter out social media (configurable)
   - Prioritize news domains
6. **Progress Update:** WebSocket sends progress to frontend: `{"stage": "search", "found": 10}`

#### Phase 3: Parallel Scraping
7. **Scraping Pipeline:** For each URL (executed concurrently with `asyncio.gather`):
   - Check robots.txt compliance
   - Add random delay (1-3 seconds) to avoid rate limiting
   - Attempt Scrapling extraction
   - Fallback to Playwright if Scraping fails (tracked separately)
   - Extract: title, publish date, main text, metadata
8. **Text Cleaning:**
   - Remove boilerplate (ads, navigation, footers)
   - Normalize whitespace
   - Extract Indonesian text only (optional)
9. **Progress Update:** WebSocket sends: `{"stage": "scraping", "completed": 5, "total": 10}`

#### Phase 4: Semantic Processing
10. **Chunking Strategy:**
    - Split text into 500-word chunks with 50-word overlap
    - Preserve sentence boundaries
    - Track chunk metadata (source URL, position)
11. **Embedding Generation:**
    - Load `pplx-embed-v1-0.6b` (lazy load on first use)
    - Batch process chunks (batch_size=8 for efficiency)
    - Generate 768-dimensional vectors
12. **Vector Indexing:**
    - Create in-memory FAISS index
    - Store chunk ID → embedding mapping
    - Store chunk ID → source URL mapping
13. **Semantic Retrieval:**
    - Embed user's original query
    - FAISS search for top-k=10 most similar chunks
    - Re-rank by combining similarity score + source authority
    - Return top 5 chunks for NER processing
14. **Progress Update:** WebSocket sends: `{"stage": "embedding", "relevant_chunks": 5}`

#### Phase 5: Entity Extraction
15. **NER Processing:**
    - Load `cahya/bert-base-indonesian-NER` (lazy load)
    - Process each relevant chunk
    - Extract: PERSON, ORGANIZATION, LOCATION, EVENT
    - Include confidence scores and context
16. **Entity Resolution:**
    - Deduplicate entities using fuzzy matching (Levenshtein distance)
    - Merge aliases (e.g., "PT. Freeport" = "Freeport Indonesia")
    - Assign canonical names
17. **Relationship Extraction:**
    - Co-occurrence: entities in same chunk → potential relationship
    - Pattern matching: regex for "X adalah Y", "X milik Y", etc.
    - Confidence scoring based on distance and frequency
18. **Progress Update:** WebSocket sends: `{"stage": "extraction", "entities": 42, "relationships": 18}`

#### Phase 6: Storage & Visualization
19. **Database Persistence:**
    - Insert entities into `entities` table (upsert to avoid duplicates)
    - Insert relationships into `relationships` table
    - Store source URLs in `sources` table
    - Create full-text search index
20. **Response Payload:**
    ```json
    {
      "success": true,
      "stats": {
        "urls_scraped": 10,
        "chunks_processed": 234,
        "entities_found": 42,
        "relationships_found": 18
      },
      "network": {
        "nodes": [...],
        "edges": [...]
      },
      "sources": [...]
    }
    ```
21. **Frontend Rendering:**
    - D3.js force-directed graph
    - Node size = entity frequency
    - Edge thickness = relationship confidence
    - Click node → show details panel with sources

### 4.3 Local Document Workflow

1. **File Upload:** User drags & drops PDF/HTML/TXT into frontend
2. **File Processing:**
   - PDF: Use `PyMuPDF` for text extraction
   - HTML: Use `BeautifulSoup` for text extraction
   - TXT: Direct read
3. **Skip Web Search:** Jump directly to Phase 4 (Semantic Processing)
4. **Continue:** Same as OSINT workflow from step 10 onward

### 4.4 State Management

**Frontend State (Zustand):**
```typescript
interface AppState {
  currentProject: Project | null;
  searchResults: SearchResult[];
  networkData: NetworkGraph | null;
  selectedNode: Entity | null;
  isLoading: boolean;
  loadingProgress: LoadingProgress;
}
```

**Backend State (DuckDB):**
- Project metadata
- Entity cache (for deduplication across sessions)
- User preferences
- Scraping history (to avoid re-scraping)

## 5. Module Specifications

### 5.1 Search Module (`search.py`)

```python
class SearchEngine:
    """Handles web search with DuckDuckGo"""
    
    async def search(
        self, 
        query: str, 
        max_results: int = 10,
        region: str = "id-ID"
    ) -> list[SearchResult]:
        """
        Returns list of URLs with metadata.
        Handles rate limiting and retries.
        """
        pass
    
    def filter_results(
        self, 
        results: list[SearchResult],
        exclude_social: bool = True,
        prefer_news: bool = True
    ) -> list[SearchResult]:
        """Filter and prioritize results"""
        pass
```

### 5.2 Scraping Module (`scraper.py`)

```python
class AdaptiveScraper:
    """Web scraping with fallback mechanisms"""
    
    async def scrape_batch(
        self, 
        urls: list[str],
        max_concurrent: int = 3
    ) -> list[ScrapedPage]:
        """
        Scrape multiple URLs concurrently.
        Returns structured data with metadata.
        """
        pass
    
    async def scrape_single(
        self, 
        url: str,
        use_playwright_fallback: bool = True
    ) -> ScrapedPage:
        """
        Try Scrapling first, fallback to Playwright.
        Implements retry logic with exponential backoff.
        """
        pass
```

### 5.3 Embedding Module (`embeddings.py`)

```python
class SemanticSearchEngine:
    """FAISS-based semantic search"""
    
    def __init__(self, model_path: str, use_onnx: bool = True):
        """Load quantized model for efficiency"""
        pass
    
    def index_chunks(
        self, 
        chunks: list[TextChunk]
    ) -> FAISSIndex:
        """Create in-memory FAISS index"""
        pass
    
    def search(
        self, 
        query: str, 
        k: int = 10
    ) -> list[SearchResult]:
        """Return top-k most relevant chunks"""
        pass
    
    def clear_index(self):
        """Free memory after processing"""
        pass
```

### 5.4 NER Module (`ner_extractor.py`)

```python
class IndonesianNERExtractor:
    """Entity extraction for Indonesian text"""
    
    def extract_entities(
        self, 
        text: str,
        min_confidence: float = 0.7
    ) -> list[Entity]:
        """
        Extract entities with confidence scores.
        Returns: Entity(name, type, confidence, context)
        """
        pass
    
    def batch_extract(
        self, 
        texts: list[str],
        batch_size: int = 8
    ) -> list[list[Entity]]:
        """Process multiple texts efficiently"""
        pass
```

### 5.5 Entity Resolution Module (`entity_resolver.py`)

```python
class EntityResolver:
    """Deduplication and canonical naming"""
    
    def __init__(self, db_path: str):
        """Load existing entity cache from DuckDB"""
        pass
    
    def resolve(
        self, 
        entities: list[Entity]
    ) -> list[ResolvedEntity]:
        """
        Merge duplicates using fuzzy matching.
        Assign canonical names.
        Update entity cache.
        """
        pass
    
    def merge_aliases(
        self, 
        entity1: Entity, 
        entity2: Entity
    ) -> ResolvedEntity:
        """Merge two entities into one canonical form"""
        pass
```

### 5.6 Relationship Extractor (`relationship_extractor.py`)

```python
class RelationshipExtractor:
    """Extract relationships between entities"""
    
    def extract_from_cooccurrence(
        self, 
        entities: list[Entity], 
        chunks: list[TextChunk],
        window_size: int = 3
    ) -> list[Relationship]:
        """
        Entities appearing in same chunk → relationship.
        Score based on distance and frequency.
        """
        pass
    
    def extract_from_patterns(
        self, 
        text: str, 
        entities: list[Entity]
    ) -> list[Relationship]:
        """
        Use regex patterns to find explicit relationships.
        Patterns: "X adalah Y", "X milik Y", "X membeli Y"
        """
        pass
```

### 5.7 Database Module (`database.py`)

```python
import duckdb

class DatabaseManager:
    """DuckDB connection and query management"""
    
    def __init__(self, db_path: str):
        """Initialize DuckDB connection with optimal settings"""
        self.conn = duckdb.connect(db_path)
        self._setup_extensions()
        self._create_tables()
    
    def _setup_extensions(self):
        """Load DuckDB extensions for full-text search and JSON"""
        self.conn.execute("INSTALL fts;")
        self.conn.execute("LOAD fts;")
        self.conn.execute("INSTALL json;")
        self.conn.execute("LOAD json;")
    
    def _create_tables(self):
        """Create tables if not exist"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL,
                type VARCHAR,
                aliases JSON,
                first_seen TIMESTAMP,
                last_updated TIMESTAMP,
                frequency INTEGER DEFAULT 1,
                metadata JSON
            )
        """)
        # ... other tables
    
    def insert_entities(
        self, 
        entities: list[Entity]
    ) -> list[int]:
        """
        Batch insert entities with upsert logic.
        Returns list of entity IDs.
        """
        pass
    
    def search_entities(
        self, 
        query: str, 
        entity_type: str = None,
        limit: int = 100
    ) -> list[Entity]:
        """
        Full-text search on entity names.
        Uses DuckDB's built-in FTS index.
        """
        pass
    
    def get_network_data(
        self, 
        project_id: str,
        min_confidence: float = 0.5
    ) -> dict:
        """
        Analytical query to get nodes and edges.
        Optimized for DuckDB columnar storage.
        """
        pass
    
    def get_entity_statistics(self) -> dict:
        """
        Get aggregate statistics using DuckDB's analytical capabilities.
        Returns: entity counts by type, relationship counts, etc.
        """
        pass
    
    def export_to_json(self, project_id: str) -> str:
        """Export all project data as JSON"""
        pass
    
    def close(self):
        """Close connection and free resources"""
        self.conn.close()
```

---

## 6. Error Handling & Resilience

### 6.1 Error Categories

| Error Type | Example | Handling Strategy |
|------------|---------|-------------------|
| **Network Errors** | Connection timeout, DNS failure | Retry 3x with exponential backoff, then mark URL as failed |
| **Scraping Errors** | Bot detection, CAPTCHA | Log warning, skip URL, continue with other URLs |
| **Model Errors** | Out of memory, model not found | Show user-friendly error, suggest restart or smaller batch |
| **Parsing Errors** | Malformed HTML, encoding issues | Use fallback parser, extract partial text if possible |
| **Database Errors** | DuckDB lock, disk full | Queue operations, retry, alert user |

### 6.2 Graceful Degradation

1. **Partial Results:** If 8/10 URLs succeed, process and show results from 8 URLs
2. **Fallback Scrapers:** Scrapling → Playwright → Simple requests
3. **Reduced Accuracy:** If memory low, process fewer chunks or use smaller batch size
4. **Offline Mode:** Show cached results, allow local document processing

### 6.3 User Feedback

```typescript
interface LoadingProgress {
  stage: 'search' | 'scraping' | 'embedding' | 'extraction' | 'complete';
  progress: number; // 0-100
  message: string; // User-friendly status
  errors: ErrorInfo[]; // Non-fatal errors
}

interface ErrorInfo {
  url?: string;
  error: string;
  timestamp: Date;
  recoverable: boolean;
}
```

---

## 7. Performance Optimization

### 7.1 Model Size Optimization

**Problem:** Two transformer models = ~1.65GB original size  
**Target:** < 500MB total after optimization

**Solutions:**

1. **Quantization to INT8:**
   ```bash
   # Convert PyTorch to ONNX
   python -m transformers.onnx --model=perplexity-ai/pplx-embed-v1-0.6b --feature=embedding
   
   # Quantize ONNX model
   python -m onnxruntime.quantization.quantize_dynamic \
     --model_input pplx-embed.onnx \
     --model_output pplx-embed-quantized.onnx \
     --weight_type=Int8
   ```
   - Expected reduction: 4x smaller
   - Accuracy loss: < 2%

2. **Model Sharing:**
   - Both models use BERT-base architecture
   - Share embedding layer (saves ~100MB)
   - Only load task-specific heads

3. **Lazy Loading:**
   ```python
   class ModelManager:
       _embed_model = None
       _ner_model = None
       
       @property
       def embed_model(self):
           if self._embed_model is None:
               self._embed_model = load_model("pplx-embed")
           return self._embed_model
       
       def unload_all(self):
           """Called after processing complete"""
           self._embed_model = None
           self._ner_model = None
           gc.collect()
   ```

### 7.2 Memory Management

```python
# Maximum memory limits
MAX_RAM_USAGE = 4 * 1024 * 1024 * 1024  # 4GB
MAX_SCRAPED_TEXT_SIZE = 10 * 1024 * 1024  # 10MB total text
MAX_CHUNKS_IN_MEMORY = 1000

# Streaming approach for large texts
async def process_large_text(text: str):
    for chunk in chunk_generator(text, chunk_size=500):
        embedding = await generate_embedding(chunk)
        yield embedding
        # Immediately index, don't accumulate
```

### 7.3 Concurrency Strategy

```python
# Concurrent scraping with rate limiting
class RateLimitedScraper:
    def __init__(self, max_concurrent: int = 3, delay_range: tuple = (1, 3)):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.delay_range = delay_range
    
    async def scrape_with_rate_limit(self, url: str):
        async with self.semaphore:
            await asyncio.sleep(random.uniform(*self.delay_range))
            return await self.scrape(url)

# Usage
scraper = RateLimitedScraper(max_concurrent=3)
results = await asyncio.gather(*[
    scraper.scrape_with_rate_limit(url) 
    for url in urls
])
```

### 7.4 Caching Strategy

**LRU Cache for:**
- Search results (TTL: 1 hour)
- Scraped pages (TTL: 24 hours)
- Entity resolutions (persistent in DuckDB)

```python
@lru_cache(maxsize=100)
def get_cached_embedding(text_hash: str):
    """Cache embeddings for repeated texts"""
    pass
```

---

## 8. Security Considerations

### 8.1 Input Validation

```python
from pydantic import BaseModel, validator, HttpUrl

class SearchRequest(BaseModel):
    query: str
    max_results: int = 10
    
    @validator('query')
    def validate_query(cls, v):
        if len(v) < 10 or len(v) > 500:
            raise ValueError('Query must be 10-500 characters')
        # Prevent injection attacks
        if any(char in v for char in ['<', '>', '{', '}']):
            raise ValueError('Invalid characters in query')
        return v.strip()
    
    @validator('max_results')
    def validate_max_results(cls, v):
        if v < 1 or v > 50:
            raise ValueError('max_results must be 1-50')
        return v
```

### 8.2 Secure Communication

- **Localhost Only:** FastAPI binds to `127.0.0.1:8000` only
- **No External Access:** CORS configured for `tauri://localhost` only
- **Process Isolation:** Sidecar runs with minimal permissions

### 8.3 Data Sanitization

```python
def sanitize_scraped_text(text: str) -> str:
    """Remove potentially dangerous content"""
    # Remove script tags
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
    # Remove excessive whitespace
    text = ' '.join(text.split())
    # Limit size
    if len(text) > 1_000_000:  # 1MB
        text = text[:1_000_000]
    return text
```

### 8.4 Privacy Safeguards

1. **No Telemetry:** Application sends no usage data
2. **Local Storage Only:** All data in `%APPDATA%/osint-tool/`
3. **User Consent:** Explicit opt-in for any network requests beyond search/scrape
4. **Data Export:** User can export all data as JSON/CSV
5. **Data Deletion:** User can delete all data with one click

---

## 9. Deployment Strategy

### 9.1 Build Process

```yaml
# .github/workflows/release.yml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Build Python Sidecar
        run: |
          pip install -r requirements.txt
          pyinstaller sidecar.spec --noconfirm
      
      - name: Download Models
        run: python scripts/download_models.py
      
      - name: Quantize Models
        run: python scripts/quantize_models.py
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Build Frontend
        run: |
          cd frontend
          npm ci
          npm run build
      
      - name: Build Tauri App
        uses: tauri-apps/tauri-action@v0
        with:
          tagName: ${{ github.ref_name }}
          releaseName: 'OSINT Tool ${{ github.ref_name }}'
          releaseBody: 'See CHANGELOG.md for details'
          releaseDraft: true
          prerelease: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 9.2 PyInstaller Spec File

```python
# sidecar.spec
a = Analysis(
    ['sidecar/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models/pplx-embed-quantized.onnx', 'models'),
        ('models/cahya-ner-quantized.onnx', 'models'),
    ],
    hiddenimports=[
        'transformers',
        'torch',
        'faiss',
        'fastapi',
        'uvicorn',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'PIL'],  # Reduce size
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='python-sidecar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

### 9.3 Auto-Update Mechanism

```typescript
// Tauri updater configuration
import { checkUpdate, installUpdate } from '@tauri-apps/api/updater';

async function checkForUpdates() {
  try {
    const { shouldUpdate, manifest } = await checkUpdate();
    
    if (shouldUpdate) {
      const consent = await askUser(
        `Update to version ${manifest.version} available. Install now?`
      );
      
      if (consent) {
        await installUpdate();
        await relaunch();
      }
    }
  } catch (error) {
    console.error('Update check failed:', error);
  }
}
```

### 9.4 Installation Flow

1. User downloads `osint-tool-setup-{version}.exe`
2. Installer checks for:
   - Windows 10/11 (minimum requirement)
   - 8GB RAM minimum
   - 2GB free disk space
3. User selects installation directory
4. Installer extracts files (~1.5GB total)
5. First launch:
   - Prompts for language (ID/EN)
   - Shows quick tutorial
   - Creates default project

---

## 10. Development Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Week 1-2: Core Infrastructure**
- [ ] Initialize Tauri project with React frontend
- [ ] Setup FastAPI sidecar with basic endpoints
- [ ] Implement sidecar communication layer
- [ ] Setup DuckDB database with schema migrations
- [ ] Configure development environment (hot reload, debugging)

**Week 3-4: Basic NLP Pipeline**
- [ ] Integrate `duckduckgo-search` for web search
- [ ] Implement Scrapling-based scraper
- [ ] Download and integrate `pplx-embed-v1-0.6b`
- [ ] Download and integrate `cahya/bert-base-indonesian-NER`
- [ ] Implement text chunking and embedding pipeline
- [ ] Basic entity extraction and storage

**Deliverable:** Working prototype that can search, scrape, and extract entities (CLI only)

### Phase 2: Core Features (Weeks 5-8)

**Week 5-6: Visualization & UI**
- [ ] Design UI mockups (Figma)
- [ ] Implement search interface
- [ ] Implement document upload interface
- [ ] Integrate D3.js for network visualization
- [ ] Add entity detail panels
- [ ] Implement project management UI

**Week 7-8: Entity Resolution & Relationships**
- [ ] Implement fuzzy matching for entity deduplication
- [ ] Build entity alias management
- [ ] Implement co-occurrence relationship extraction
- [ ] Add pattern-based relationship extraction
- [ ] Build relationship confidence scoring

**Deliverable:** Functional desktop app with visualization

### Phase 3: Optimization & Polish (Weeks 9-12)

**Week 9-10: Performance Optimization**
- [ ] Quantize models to INT8 (reduce size)
- [ ] Implement lazy model loading
- [ ] Add memory management and cleanup
- [ ] Implement caching layer
- [ ] Optimize scraping concurrency
- [ ] Add progress indicators and cancellation

**Week 11-12: Error Handling & UX**
- [ ] Comprehensive error handling
- [ ] User-friendly error messages (Bahasa Indonesia + English)
- [ ] Add loading states and progress tracking
- [ ] Implement graceful degradation
- [ ] Add offline mode support
- [ ] User testing with journalists (3-5 users)
- [ ] Iterate based on feedback

**Deliverable:** Beta-ready application

### Phase 4: Deployment & Documentation (Weeks 13-16)

**Week 13-14: Packaging & Distribution**
- [ ] Configure PyInstaller bundling
- [ ] Setup Tauri build pipeline
- [ ] Create Windows installer
- [ ] Implement auto-update mechanism
- [ ] Test on multiple Windows versions
- [ ] Code signing (if budget allows)

**Week 15-16: Documentation & Launch**
- [ ] Write user documentation (Bahasa Indonesia)
- [ ] Create video tutorials
- [ ] Write developer documentation
- [ ] Setup project website
- [ ] Prepare launch materials
- [ ] Beta release to wider group

**Deliverable:** v1.0 release candidate

### Future Enhancements (Post-v1.0)

- [ ] **Multi-language Support:** Add English, other SE Asian languages
- [ ] **Export Formats:** GEXF (Gephi), GraphML, JSON-LD
- [ ] **Collaboration:** Multi-user project sharing
- [ ] **Advanced NER:** Custom entity types, user-trained models
- [ ] **Timeline Visualization:** Show entity relationships over time
- [ ] **Source Credibility:** Score sources by reliability
- [ ] **API Mode:** Allow programmatic access
- [ ] **macOS/Linux Support:** Cross-platform release

---

## 11. Appendix

### 11.1 API Endpoints

```python
# FastAPI endpoints

@app.post("/api/search")
async def search_web(request: SearchRequest):
    """Execute OSINT search workflow"""
    pass

@app.post("/api/upload")
async def upload_document(file: UploadFile):
    """Process uploaded document"""
    pass

@app.get("/api/projects")
async def list_projects():
    """List all projects"""
    pass

@app.get("/api/projects/{project_id}/entities")
async def get_entities(project_id: str):
    """Get all entities in project"""
    pass

@app.get("/api/projects/{project_id}/network")
async def get_network(project_id: str):
    """Get network graph data"""
    pass

@app.websocket("/ws/progress")
async def progress_websocket(websocket: WebSocket):
    """Real-time progress updates"""
    pass
```

### 11.2 Configuration File

```json
{
  "version": "1.0",
  "language": "id",
  "search": {
    "max_results": 10,
    "region": "id-ID",
    "exclude_social_media": true
  },
  "scraping": {
    "max_concurrent": 3,
    "delay_range": [1, 3],
    "timeout": 30,
    "use_playwright_fallback": true
  },
  "models": {
    "use_onnx": true,
    "use_quantized": true,
    "max_ram_gb": 4
  },
  "storage": {
    "database_path": "%APPDATA%/osint-tool/data/osint.duckdb",
    "cache_enabled": true,
    "cache_ttl_hours": 24
  }
}
```

### 11.3 Testing Strategy

**Unit Tests:**
- Test each module in isolation
- Mock external dependencies (web search, scraping)
- Target: 80% code coverage

**Integration Tests:**
- Test full pipeline with sample data
- Test sidecar communication
- Test database operations

**End-to-End Tests:**
- Test complete user workflows
- Test on real Windows machines
- Test with real Indonesian news sites

**Performance Tests:**
- Memory profiling
- Load testing with 100+ URLs
- Long-running stability tests

### 11.4 Monitoring & Logging

```python
# Structured logging
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
            "extra": getattr(record, 'extra', {})
        }
        return json.dumps(log_obj)

# Usage
logger = logging.getLogger(__name__)
logger.info("Search completed", extra={
    "query": "korupsi nikel",
    "results": 10,
    "duration_ms": 2340
})
```

**Log Locations:**
- Sidecar logs: `%APPDATA%/osint-tool/logs/sidecar.log`
- App logs: `%APPDATA%/osint-tool/logs/app.log`
- Crash dumps: `%APPDATA%/osint-tool/crashes/`

### 11.5 Dependencies

**Python (requirements.txt):**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
duckduckgo-search==4.1.1
scrapling==0.2.5
transformers==4.37.0
torch==2.2.0
faiss-cpu==1.7.4
duckdb==0.10.0
pydantic==2.5.0
PyMuPDF==1.23.21
beautifulsoup4==4.12.3
python-Levenshtein==0.23.0
```

**Frontend (package.json):**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "d3": "^7.8.5",
    "@reactflow/core": "^11.10.0",
    "zustand": "^4.5.0",
    "@radix-ui/react-dialog": "^1.0.5",
    "tailwindcss": "^3.4.0"
  },
  "devDependencies": {
    "@tauri-apps/api": "^1.5.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vitest": "^1.2.0"
  }
}
```

---

## Decision Log

| Date | Decision | Rationale | Alternatives Considered |
|------|----------|-----------|------------------------|
| 2026-03-06 | Use Tauri over Electron | Smaller bundle, better performance | Electron (larger), Neutralino (less mature) |
| 2026-03-06 | React over Vue/Svelte | Larger ecosystem, team familiarity | Vue (smaller), Svelte (less ecosystem) |
| 2026-03-06 | FAISS over ChromaDB | Simpler, in-memory, faster | ChromaDB (more features, but heavier) |
| 2026-03-06 | DuckDB over SQLite | Faster analytical queries, built-in full-text search, better compression | SQLite (simpler, but slower for analytics) |
| 2026-03-06 | DuckDuckGo over Google | No API key, privacy-focused | Google CSE (better results, but requires key) |
| 2026-03-06 | Quantized ONNX models | 4x smaller, minimal accuracy loss | Full PyTorch (larger, slower) |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Model size too large | Medium | High | Quantization, lazy loading, model sharing |
| Scraping blocked by anti-bot | High | Medium | Multiple scrapers, rate limiting, fallback mechanisms |
| Memory exhaustion on low-end laptops | Medium | High | Aggressive memory management, streaming, chunking |
| Indonesian NER model accuracy insufficient | Low | High | Test thoroughly, consider fine-tuning, add post-processing rules |
| PyInstaller bundling issues | Medium | Medium | Test on multiple Windows versions, document workarounds |
| User adoption challenges | Medium | Medium | User testing, tutorials, Bahasa Indonesia documentation |

---

## Next Steps & Questions

1. **Should we prioritize PyInstaller optimization or feature development first?**
   - Recommendation: Build features first, optimize at Phase 3

2. **Do we need to support proxy configuration in v1.0?**
   - Recommendation: Yes, critical for journalists in restricted environments

3. **Should we use ONNX or stick with PyTorch for model inference?**
   - Recommendation: ONNX with quantization for production, PyTorch for development

4. **What's the minimum viable visualization for v1.0?**
   - Recommendation: D3.js force-directed graph with basic interactivity

5. **Should we include Playwright fallback in the initial bundle or as an optional download?**
   - Recommendation: Optional download to keep initial bundle small (~100MB savings)