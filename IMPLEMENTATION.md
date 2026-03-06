# Implementation Details: OSINT NER & Network Viz Tool

> **Version:** 1.0.0  
> **Last Updated:** 2026-03-06  
> **Status:** Planning Phase

This document contains detailed implementation specifications for developers. For high-level architecture, see [README.md](README.md).

## Table of Contents

1. [Module Specifications](#1-module-specifications)
2. [Database Schema](#2-database-schema)
3. [API Endpoints](#3-api-endpoints)
4. [Configuration](#4-configuration)
5. [Performance Optimization](#5-performance-optimization)
6. [Security Implementation](#6-security-implementation)
7. [Deployment Configuration](#7-deployment-configuration)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Module Specifications

### 1.1 Search Module (`search.py`)

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

### 1.2 Scraping Module (`scraper.py`)

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

### 1.3 Embedding Module (`embeddings.py`)

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

### 1.4 NER Module (`ner_extractor.py`)

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

### 1.5 Entity Resolution Module (`entity_resolver.py`)

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

### 1.6 Relationship Extractor (`relationship_extractor.py`)

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

### 1.7 Database Module (`database.py`)

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

### 1.8 KSEI/IDX Data Downloader (`ksei_idx_downloader.py`)

```python
from pydantic import BaseModel
from typing import Optional
from datetime import date
import asyncio

class KSEIBalanceRecord(BaseModel):
    """KSEI Balancepos record - aggregate ownership by investor type"""
    report_date: date
    stock_code: str
    security_type: str
    total_shares: int
    local_institutional: int
    local_corporate: int
    local_pension_fund: int
    local_bank: int
    local_individual: int
    local_mutual_fund: int
    local_securities: int
    local_foundation: int
    local_other: int
    local_total: int
    foreign_institutional: int
    foreign_corporate: int
    foreign_pension_fund: int
    foreign_bank: int
    foreign_individual: int
    foreign_mutual_fund: int
    foreign_securities: int
    foreign_foundation: int
    foreign_other: int
    foreign_total: int

class KSEISecuritiesRecord(BaseModel):
    """KSEI StatisEfek record - company master data"""
    report_date: date
    stock_code: str
    company_name: str
    security_type: str
    isin_code: str
    issuer: str
    status: str
    local_percentage: float
    foreign_percentage: float
    total_percentage: float
    sector: str
    closing_price: float

class IDXShareholderRecord(BaseModel):
    """IDX bulk PDF record - entity-level shareholders >5%"""
    stock_code: str
    company_name: str
    securities_account_holder: str
    shareholder_name: str
    securities_account_name: str
    address: str
    address_continuation: Optional[str] = None
    nationality: str  # L=Local, F=Foreign
    domicile: str
    shares_change: int
    total_shares: int
    combined_shares_per_investor: int
    ownership_percentage: float
    report_date: date
    source_url: str
    pdf_url: str

class KSEIIDXDataDownloader:
    """Download and parse KSEI and IDX data at app startup
    
    Purpose:
        Automatically fetch and update stock ownership data from three sources:
        1. KSEI Balancepos - aggregate ownership by investor type (daily/weekly)
        2. KSEI StatisEfek - company master data with ownership % (daily/weekly)
        3. IDX Bulk PDF - entity-level shareholders >5% (daily)
    
    Update Strategy:
        - Check for updates at app startup
        - Download only if newer data available
        - Parse and store in database
        - Update ownership relationships in network graph
    
    Data Sources:
        - https://web.ksei.co.id/archive_download/holding_composition
        - https://web.ksei.co.id/archive_download/master_securities
        - https://www.idx.co.id/id/berita/pengumuman/
    """
    
    KSEI_BALANCEPOS_URL = "https://web.ksei.co.id/archive_download/holding_composition"
    KSEI_STATIS_EFEK_URL = "https://web.ksei.co.id/archive_download/master_securities"
    IDX_ANNOUNCEMENT_URL = "https://www.idx.co.id/id/berita/pengumuman/"
    IDX_SEARCH_KEYWORD = "Pemegang Saham di atas 5% (KSEI) [Semua Emiten Saham ]"
    
    def __init__(self, db_manager, cache_dir: str):
        self.db = db_manager
        self.cache_dir = cache_dir
        self.last_update_check = None
    
    async def check_and_update_all(self, force: bool = False) -> dict:
        """
        Check for updates from all three sources and download if needed.
        
        Called at app startup.
        
        Args:
            force: If True, re-download even if data appears current
            
        Returns:
            {
                'ksei_balancepos': {'updated': bool, 'records': int, 'date': date},
                'ksei_statiseff': {'updated': bool, 'records': int, 'date': date},
                'idx_bulk_pdf': {'updated': bool, 'records': int, 'date': date, 'url': str}
            }
        """
        results = {}
        
        # Check KSEI Balancepos
        results['ksei_balancepos'] = await self._update_ksei_balancepos(force)
        
        # Check KSEI StatisEfek
        results['ksei_statiseff'] = await self._update_ksei_statiseff(force)
        
        # Check IDX Bulk PDF
        results['idx_bulk_pdf'] = await self._update_idx_bulk_pdf(force)
        
        # Update ownership relationships if any data changed
        if any(r['updated'] for r in results.values()):
            await self._update_ownership_relationships(results)
        
        return results
    
    async def _update_ksei_balancepos(self, force: bool) -> dict:
        """
        Download and parse KSEI Balancepos data.
        
        Format: Pipe-separated TXT file
        """
        pass
    
    async def _update_ksei_statiseff(self, force: bool) -> dict:
        """
        Download and parse KSEI StatisEfek data.
        
        Format: Pipe-separated TXT file
        """
        pass
    
    async def _update_idx_bulk_pdf(self, force: bool) -> dict:
        """
        Download and parse IDX bulk PDF with all >5% shareholders.
        
        Uses Scrapling to bypass IDX anti-bot protections.
        """
        pass
    
    def _parse_ksei_txt(self, content: str, record_type: str) -> list:
        """
        Parse KSEI TXT files (Balancepos or StatisEfek).
        
        Format: Header row + data rows, pipe-separated
        """
        pass
    
    def _parse_idx_pdf(self, pdf_content: bytes) -> list[IDXShareholderRecord]:
        """
        Parse IDX bulk PDF with standardized table format.
        
        Expected columns:
        1. Kode Efek
        2. Nama Emiten
        3. Nama Pemegang Rekening Efek
        4. Nama Pemegang Saham
        5. Nama Rekening Efek
        6. Alamat
        7. Alamat (Lanjutan)
        8. Kebangsaan (L/F)
        9. Domisili
        10. Perubahan
        11. Jumlah Saham
        12. Saham Gabungan Per Investor
        13. Persentase Kepemilikan Per Investor (%)
        """
        pass
    
    async def _update_ownership_relationships(self, update_results: dict):
        """
        Update ownership relationships in the network graph.
        
        For each shareholder in IDX bulk PDF:
        1. Find or create shareholder entity
        2. Find or create company entity (from KSEI data)
        3. Create/update OWNS relationship with percentage
        4. Store historical data for change tracking
        """
        pass

class OwnershipDataIntegrator:
    """Integrate ownership data into entity network"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_ownership_from_idx(
        self,
        idx_records: list[IDXShareholderRecord]
    ) -> dict:
        """
        Create ownership relationships from IDX bulk data.
        
        For each record:
        1. Resolve shareholder entity (create if new)
        2. Resolve company entity (from KSEI data)
        3. Create OWNS relationship with metadata
        
        Returns:
            {
                'companies_updated': int,
                'relationships_created': int,
                'entities_created': int
            }
        """
        pass
    
    def enrich_with_ksei_data(
        self,
        company_code: str
    ) -> dict:
        """
        Enrich company entity with KSEI aggregate data.
        
        Adds:
        - Total local ownership percentage
        - Total foreign ownership percentage
        - Breakdown by investor type
        """
        pass
    
    def detect_ownership_changes(
        self,
        company_code: str,
        current_records: list[IDXShareholderRecord]
    ) -> dict:
        """
        Detect changes since last update.
        
        Returns:
            {
                'new_shareholders': [...],
                'exits': [...],
                'increased': [...],
                'decreased': [...]
            }
        """
        pass
```

**Usage Example:**

```python
# At app startup
async def on_app_startup():
    db_manager = DatabaseManager(db_path)
    downloader = KSEIIDXDataDownloader(db_manager, cache_dir)
    
    # Check for updates and download if available
    results = await downloader.check_and_update_all()
    
    # Results:
    # {
    #   'ksei_balancepos': {'updated': True, 'records': 778, 'date': '2026-03-06'},
    #   'ksei_statiseff': {'updated': True, 'records': 756, 'date': '2026-03-06'},
    #   'idx_bulk_pdf': {
    #       'updated': True, 
    #       'records': 1523, 
    #       'date': '2026-03-04',
    #       'url': 'https://www.idx.co.id/...'
    #   }
    # }
    
    # Network graph now has updated ownership data
    return results
```


## 2. Database Schema

### 2.1 Core Tables

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

### 2.2 Stock Ownership Tables

```sql
-- KSEI Balancepos - aggregate ownership by investor type
CREATE TABLE ksei_balancepos (
    id INTEGER PRIMARY KEY,
    report_date DATE NOT NULL,
    stock_code VARCHAR NOT NULL,
    security_type VARCHAR,
    total_shares BIGINT,
    local_institutional BIGINT,
    local_corporate BIGINT,
    local_pension_fund BIGINT,
    local_bank BIGINT,
    local_individual BIGINT,
    local_mutual_fund BIGINT,
    local_securities BIGINT,
    local_foundation BIGINT,
    local_other BIGINT,
    local_total BIGINT,
    foreign_institutional BIGINT,
    foreign_corporate BIGINT,
    foreign_pension_fund BIGINT,
    foreign_bank BIGINT,
    foreign_individual BIGINT,
    foreign_mutual_fund BIGINT,
    foreign_securities BIGINT,
    foreign_foundation BIGINT,
    foreign_other BIGINT,
    foreign_total BIGINT,
    UNIQUE(report_date, stock_code)
);

CREATE INDEX idx_ksei_balancepos_date ON ksei_balancepos(report_date);
CREATE INDEX idx_ksei_balancepos_code ON ksei_balancepos(stock_code);

-- KSEI StatisEfek - company master data with ownership percentages
CREATE TABLE ksei_statiseff (
    id INTEGER PRIMARY KEY,
    report_date DATE NOT NULL,
    stock_code VARCHAR NOT NULL,
    company_name VARCHAR NOT NULL,
    security_type VARCHAR,
    isin_code VARCHAR,
    issuer VARCHAR,
    status VARCHAR,
    local_percentage FLOAT,
    foreign_percentage FLOAT,
    total_percentage FLOAT,
    sector VARCHAR,
    closing_price FLOAT,
    UNIQUE(report_date, stock_code)
);

CREATE INDEX idx_ksei_statiseff_date ON ksei_statiseff(report_date);
CREATE INDEX idx_ksei_statiseff_code ON ksei_statiseff(stock_code);
CREATE INDEX idx_ksei_statiseff_sector ON ksei_statiseff(sector);

-- IDX Bulk Shareholders - entity-level ownership >5%
CREATE TABLE idx_shareholders (
    id INTEGER PRIMARY KEY,
    report_date DATE NOT NULL,
    stock_code VARCHAR NOT NULL,
    company_name VARCHAR NOT NULL,
    securities_account_holder VARCHAR,
    shareholder_name VARCHAR NOT NULL,
    securities_account_name VARCHAR,
    address TEXT,
    address_continuation TEXT,
    nationality VARCHAR(1),  -- L=Local, F=Foreign
    domicile VARCHAR,
    shares_change BIGINT,
    total_shares BIGINT,
    combined_shares_per_investor BIGINT,
    ownership_percentage FLOAT,
    source_url VARCHAR,
    pdf_url VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(report_date, stock_code, shareholder_name)
);

CREATE INDEX idx_shareholders_date ON idx_shareholders(report_date);
CREATE INDEX idx_shareholders_code ON idx_shareholders(stock_code);
CREATE INDEX idx_shareholders_name ON idx_shareholders(shareholder_name);
CREATE INDEX idx_shareholders_nationality ON idx_shareholders(nationality);

-- Entity-level ownership relationships (derived from idx_shareholders)
CREATE TABLE ownership_records (
    id INTEGER PRIMARY KEY,
    company_entity_id INTEGER REFERENCES entities(id),
    shareholder_entity_id INTEGER REFERENCES entities(id),
    shares_owned BIGINT,
    ownership_percentage FLOAT,
    report_date DATE,
    source_table VARCHAR,  -- 'idx_shareholders' or 'ksei_balancepos'
    source_id INTEGER,     -- Reference to source record
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_entity_id, shareholder_entity_id, report_date)
);

CREATE INDEX idx_ownership_company ON ownership_records(company_entity_id);
CREATE INDEX idx_ownership_shareholder ON ownership_records(shareholder_entity_id);
CREATE INDEX idx_ownership_date ON ownership_records(report_date);

-- Data source tracking
CREATE TABLE data_source_updates (
    id INTEGER PRIMARY KEY,
    source_name VARCHAR NOT NULL UNIQUE,  -- 'ksei_balancepos', 'ksei_statiseff', 'idx_bulk_pdf'
    last_check TIMESTAMP,
    last_update TIMESTAMP,
    records_count INTEGER,
    report_date DATE,
    source_url VARCHAR,
    status VARCHAR CHECK(status IN ('success', 'failed', 'no_update')),
    error_message TEXT
);

CREATE INDEX idx_data_source_name ON data_source_updates(source_name);
```

---

## 3. API Endpoints

### 3.1 Core Endpoints

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

### 3.2 Shareholder Data Endpoints

```python
@app.get("/api/companies/{stock_code}/shareholders")
async def get_shareholders(stock_code: str, latest: bool = True):
    """Get shareholder data for a public company"""
    pass

@app.post("/api/companies/{stock_code}/refresh-shareholders")
async def refresh_shareholder_data(stock_code: str):
    """Fetch latest shareholder data from IDX"""
    pass

@app.get("/api/companies/{stock_code}/ownership-history")
async def get_ownership_history(stock_code: str, months: int = 12):
    """Get ownership changes over time"""
    pass

@app.get("/api/shareholders/bulk/daily")
async def get_bulk_daily_shareholders(date: Optional[str] = None):
    """Get all shareholder data from latest bulk announcement"""
    pass

@app.post("/api/shareholders/bulk/refresh")
async def refresh_bulk_shareholders():
    """Fetch and process latest bulk announcement from IDX"""
    pass

@app.get("/api/companies/{stock_code}/ownership-alerts")
async def get_ownership_alerts(
    stock_code: str, 
    severity: Optional[str] = None,
    unacknowledged_only: bool = False
):
    """Get ownership change alerts for a company"""
    pass

@app.post("/api/companies/{stock_code}/ownership-alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """Mark an ownership alert as acknowledged"""
    pass

@app.get("/api/ownership-alerts")
async def list_all_alerts(
    severity: Optional[str] = None,
    limit: int = 100
):
    """List all ownership alerts across companies"""
    pass
```

---

## 4. Configuration

### 4.1 Application Configuration

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

### 4.2 Frontend State Management

```typescript
interface AppState {
  currentProject: Project | null;
  searchResults: SearchResult[];
  networkData: NetworkGraph | null;
  selectedNode: Entity | null;
  isLoading: boolean;
  loadingProgress: LoadingProgress;
}

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

## 5. Performance Optimization

### 5.1 Model Size Optimization

```bash
# Convert PyTorch to ONNX
python -m transformers.onnx --model=perplexity-ai/pplx-embed-v1-0.6b --feature=embedding

# Quantize ONNX model
python -m onnxruntime.quantization.quantize_dynamic \
  --model_input pplx-embed.onnx \
  --model_output pplx-embed-quantized.onnx \
  --weight_type=Int8
```

Expected reduction: 4x smaller, accuracy loss: < 2%

### 5.2 Lazy Loading Pattern

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

### 5.3 Memory Management

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

### 5.4 Concurrency Strategy

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

### 5.5 Caching Strategy

```python
@lru_cache(maxsize=100)
def get_cached_embedding(text_hash: str):
    """Cache embeddings for repeated texts"""
    pass
```

**LRU Cache for:**
- Search results (TTL: 1 hour)
- Scraped pages (TTL: 24 hours)
- Entity resolutions (persistent in DuckDB)

---

## 6. Security Implementation

### 6.1 Input Validation

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

### 6.2 Secure Communication

- **Localhost Only:** FastAPI binds to `127.0.0.1:8000` only
- **No External Access:** CORS configured for `tauri://localhost` only
- **Process Isolation:** Sidecar runs with minimal permissions

### 6.3 Data Sanitization

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

### 6.4 Privacy Safeguards

1. **No Telemetry:** Application sends no usage data
2. **Local Storage Only:** All data in `%APPDATA%/osint-tool/`
3. **User Consent:** Explicit opt-in for any network requests beyond search/scrape
4. **Data Export:** User can export all data as JSON/CSV
5. **Data Deletion:** User can delete all data with one click

---

## 7. Deployment Configuration

### 7.1 GitHub Actions Workflow

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

### 7.2 PyInstaller Spec File

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

### 7.3 Auto-Update Mechanism

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

### 7.4 Installation Flow

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

## 8. Testing Strategy

### 8.1 Unit Tests

- Test each module in isolation
- Mock external dependencies (web search, scraping)
- Target: 80% code coverage

### 8.2 Integration Tests

- Test full pipeline with sample data
- Test sidecar communication
- Test database operations

### 8.3 End-to-End Tests

- Test complete user workflows
- Test on real Windows machines
- Test with real Indonesian news sites

### 8.4 Performance Tests

- Memory profiling
- Load testing with 100+ URLs
- Long-running stability tests

---

## 9. Monitoring & Logging

### 9.1 Structured Logging

```python
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

### 9.2 Log Locations

- Sidecar logs: `%APPDATA%/osint-tool/logs/sidecar.log`
- App logs: `%APPDATA%/osint-tool/logs/app.log`
- Crash dumps: `%APPDATA%/osint-tool/crashes/`

---

## 10. Dependencies

### 10.1 Python (requirements.txt)

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

### 10.2 Frontend (package.json)

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

## 11. Data Sources

### 11.1 Indonesian Financial Data Sources

| Source | Type | Access | Data Provided | Update Frequency |
|--------|------|--------|---------------|------------------|
| **KSEI (Kustodian Sentral Efek Indonesia)** | Aggregate Ownership | Public download (ZIP/TXT) | Market-level ownership by investor type, local vs foreign distribution | Daily/Weekly |
| **IDX Shareholder Registry** | Entity-level Ownership | Public website (PDF) | Names of shareholders >5%, shares owned, percentages | Monthly |
| **IDX Bulk Announcements** | Market-wide Ownership | Public website (PDF) | All companies with >5% shareholders, daily updates | Daily |

---

## 12. Usage Examples

### 12.1 Per-Company Shareholder Query

```python
# Initialize scraper
scraper = IDXShareholderScraper()

# Get latest shareholders for BBCA
shareholders = await scraper.get_latest_shareholders("BBCA")

# Output (fixed schema):
# [
#   ShareholderRecord(
#     company_code="BBCA",
#     company_name="Bank Central Asia Tbk",
#     shareholder_name="PT Dwidana Sakti",
#     shares_owned=24500000000,
#     ownership_percentage=19.87,
#     report_date=date(2026, 2, 28),
#     report_type="Laporan Bulanan Registrasi Pemegang Efek",
#     source_url="https://www.idx.co.id/...",
#     pdf_url="https://www.idx.co.id/static/file/..."
#   ),
#   ...
# ]

# Integrate into network
integrator = ShareholderDataIntegrator(db_manager)
company_entity = db_manager.get_entity_by_name("Bank Central Asia")
integrator.create_ownership_relationships(shareholders, company_entity.id)
```

### 12.2 Bulk Daily Shareholder Update

```python
# Initialize scraper
scraper = IDXBulkAnnouncementScraper()

# Get latest bulk shareholder data
shareholders_by_company = await scraper.get_daily_shareholders()

# Output structure:
# {
#   "AADI": [
#     BulkShareholderRecord(
#       company_code="AADI",
#       company_name="ADARO ANDALAN INDONESIA Tbk, PT",
#       securities_account_holder="PT. STOCKBIT SEKURITAS DIGITAL",
#       shareholder_name="ADARO STRATEGIC INVESTMENTS",
#       securities_account_name="ADARO STRATEGIC INVESTMENTS",
#       address="BLOK.X-5 KAV.1-2 JAKARTA 12950",
#       nationality="L",
#       domicile="INDONESIA",
#       shares_change=0,
#       combined_shares_per_investor=986784234,
#       ownership_percentage=41.10,
#       report_date=date(2026, 3, 4),
#       source_url="https://www.idx.co.id/...",
#       pdf_url="https://www.idx.co.id/static/file/..."
#     ),
#     ...
#   ],
#   "BBCA": [...],
#   ...
# }

# Integrate into network
integrator = BulkShareholderIntegrator(db_manager)
stats = integrator.bulk_create_ownership_relationships(shareholders_by_company)

# Detect changes
current_shareholders = shareholders_by_company["BBCA"]
changes = integrator.detect_ownership_changes(current_shareholders, "BBCA")
alerts = integrator.generate_ownership_alerts(changes, "BBCA")

# Process alerts
for alert in alerts:
    if alert['severity'] in ['HIGH', 'CRITICAL']:
        notify_user(alert)
```

### 12.3 Scheduled Background Updates

```python
# Run daily to keep ownership data current
async def scheduled_ownership_update():
    scraper = IDXBulkAnnouncementScraper()
    integrator = BulkShareholderIntegrator(db_manager)
    
    # Fetch latest data
    shareholders = await scraper.get_daily_shareholders()
    
    # Update database
    stats = integrator.bulk_create_ownership_relationships(shareholders)
    
    # Generate alerts for monitored companies
    for stock_code in monitored_companies:
        changes = integrator.detect_ownership_changes(
            shareholders[stock_code], 
            stock_code
        )
        alerts = integrator.generate_ownership_alerts(changes, stock_code)
        store_alerts(alerts)
```

### 12.4 On-Demand Investigation

```python
# When user investigates a company
if entity.type == 'ORG' and entity.metadata.get('is_public_company'):
    stock_code = entity.metadata.get('stock_code')
    
    # Check if we have recent bulk data
    latest_data = db.get_latest_bulk_shareholders(stock_code, days=7)
    
    if latest_data:
        # Use existing bulk data
        shareholders = latest_data
    else:
        # Fall back to per-company scraper
        shareholders = await idx_scraper.get_latest_shareholders(stock_code)
    
    # Create ownership relationships
    integrator.create_ownership_relationships(shareholders, entity.id)
```

---

## 13. Comparison of Shareholder Data Approaches

| Aspect | Per-Company (1.8) | Bulk Announcement (1.9) |
|--------|------------------|------------------------|
| **Scope** | Single company | All listed companies |
| **Update Frequency** | Monthly reports | Daily announcements |
| **Data Detail** | High (monthly trends) | Medium (daily snapshot) |
| **Use Case** | Deep investigation | Market monitoring |
| **Performance** | 1 request per company | 1 request for all |
| **Best For** | Specific company research | Comprehensive coverage |
