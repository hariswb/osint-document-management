# Design Document: Local OSINT NER & Network Viz Tool

> **Version:** 1.0.0
> **Last Updated:** 2026-03-08
> **Status:** Phase 2 ✅ Complete (Desktop App with Project-Based OSINT Workflow)

**For detailed implementation specifications, see [IMPLEMENTATION.md](IMPLEMENTATION.md)**

## Table of Contents

1. [Project Context](#1-project-context)
2. [Core Constraints](#2-core-constraints)
3. [Technology Stack](#3-technology-stack)
4. [Architecture & Data Flow](#4-architecture--data-flow)
5. [Module Overview](#5-module-overview)
6. [Data Sources](#6-data-sources)
7. [Development Roadmap](#7-development-roadmap)

---

## 1. Project Context

### 1.1 Overview

Desktop application for investigative journalists to extract, catalog, and visualize networks of actors (people, companies, organizations) from Indonesian text.

**Key Capabilities:**
- Extract entities and relationships from web articles and local documents
- Analyze corporate ownership structures using Indonesian stock market data
- Track ownership changes and generate alerts for significant events
- Visualize complex networks of people, companies, and organizations

### 1.2 Primary Workflows

1. **Project-Based OSINT Workflow:**
   - Create/select a project as your workspace
   - Search the web for relevant documents
   - Select and add search results to your project (as pending documents)
   - Process documents to extract entities and relationships
   - Visualize network graphs filtered by project
   - All data (documents, entities, relationships) is scoped to the project

2. **Passive Mode:** Processing manually uploaded local documents (PDFs, HTML, TXT)
3. **Stock Ownership Analysis:** Download KSEI and IDX data → extract ownership structures → visualize networks

### 1.3 Privacy & Security Principles

- All AI inference and data storage on local machine
- Zero-trust cloud: external services only for fetching public data
- No telemetry or usage data sent externally
- User controls all data export and deletion

### 1.4 Target Users

- Investigative journalists (Indonesian sources)
- Researchers (corporate/political networks)
- NGOs (organizational relationships)
- Fact-checkers

---

## 2. Core Constraints

### 2.1 Deployment

**Cross-Platform Support:**
- **Windows:** Installer (`.exe` or `.msi`)
- **Linux:** AppImage, `.deb`, and `.rpm` packages
- **macOS:** `.dmg` and `.app` bundle

**Installation Requirements:**
- Zero-configuration installers for all platforms
- No Python/virtual environment management required
- Installation size < 2GB (including models)
- Installation time < 5 minutes on standard broadband

### 2.2 Network & Privacy

- Internet required only for search/scraping and data updates
- All processing and storage local
- Offline mode for previously processed data
- HTTP/HTTPS proxy support

### 2.3 Performance

**Target Hardware:**
- Minimum: 8GB RAM, dual-core CPU, 256GB storage
- Recommended: 16GB RAM, quad-core CPU, 512GB SSD

**Response Time Targets:**
- Web search: < 10 seconds for 10 URLs
- Document upload: < 5 seconds for 10MB file
- Network visualization: < 2 seconds for 1000 nodes

### 2.4 Usability

- UI in Bahasa Indonesia and English
- WCAG 2.1 Level AA accessibility
- Learning curve: productive within 30 minutes

---

## 3. Technology Stack

### 3.1 Application Shell
**Tauri (Rust + WebView2)**
- Smaller bundle than Electron (~10MB vs ~150MB)
- Native security from Rust
- **Cross-platform support:**
  - **Windows:** Edge WebView2
  - **Linux:** WebKitGTK
  - **macOS:** WKWebView
- Platform-native installers for each OS

### 3.2 Frontend
- **Framework:** React + TypeScript
- **Visualization:** D3.js + React Flow
- **UI Components:** Radix UI + Tailwind CSS

### 3.3 Backend API
**Python 3.11+ with FastAPI**
- Native async for concurrent scraping
- Automatic OpenAPI documentation
- Excellent type hints and testing

### 3.4 Web Search & Scraping
- **Search:** DuckDuckGo-Search (no API keys, privacy-focused)
- **Scraping:** Scrapling (anti-bot bypass, adaptive parsing)
- **Fallback:** Playwright (JS-heavy sites)

### 3.5 NLP Processing
- **NER Model:** `cahya/bert-base-indonesian-NER` (~450MB)
- **Runtime:** Hugging Face transformers + PyTorch
- **Optimization:** INT8 quantization (4x size reduction, <2% accuracy loss)
- **Entity Types:** PERSON, ORGANIZATION, LOCATION, EVENT, DATE

### 3.6 Databases
- **Relational Store:** DuckDB (columnar, analytical queries, FTS built-in)
- **Storage Locations:**
  - **Windows:** `%APPDATA%/osint-tool/data/`
  - **Linux:** `~/.local/share/osint-tool/data/` or `$XDG_DATA_HOME`
  - **macOS:** `~/Library/Application Support/osint-tool/data/`

### 3.7 Packaging
- **Python Bundler:** PyInstaller (`--onedir` mode)
- **Tauri Builder:** Built-in Windows installer
- **Auto-Update:** Tauri's built-in updater with signed releases

---

## 4. Architecture & Data Flow

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Tauri Application                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Frontend (React + TypeScript)                │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │ │
│  │  │ Project  │  │  Search  │  │  Documents/Entities │ │ │
│  │  │  Manager │  │  Panel   │  │  /Network Views     │ │ │
│  │  └──────────┘  └──────────┘  └──────────────────────┘ │ │
│  │                                                          │
│  │  - Project Selection as Workspace                      │ │
│  │  - All Data Filtered by Current Project                │ │
│  │  - Search → Pending Docs → Processing Flow             │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │ IPC                              │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            Rust Core (Tauri Runtime)                   │ │
│  │  - Sidecar process management                          │ │
│  │  - Project-scoped database queries                     │ │
│  │  - File system access                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ HTTP/WebSocket (localhost)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Python Sidecar (FastAPI Server)                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Web Search & Scraping Pipeline                        │ │
│  │  - DuckDuckGo Search (Region: Indonesia/International) │ │
│  │  - Scrapling (HTML extraction)                         │ │
│  │  - Document Status: pending → processing → completed   │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  NLP Pipeline                                          │ │
│  │  - cahya-ner (entity extraction)                       │ │
│  │  - Pattern-based relationship extraction               │ │
│  │  - Confidence scoring                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Data Layer                                            │ │
│  │  - Project-based data isolation                        │ │
│  │  - Entity resolution & deduplication                   │ │
│  │  - Relationship extraction                             │ │
│  │  - DuckDB storage with project scoping                 │ │
│  │  - Cascade delete (document → entities)                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 OSINT Search Workflow (Project-Based)

1. **Project Selection** → User selects or creates a project as current workspace
2. **Query Initiation** → User types query with region configuration (Indonesia/International)
3. **Web Search** → DuckDuckGo search returns max 10 results
4. **Result Selection** → All results initially checked; user can uncheck unwanted items
5. **Add to Project** → Selected results become "pending" documents in project
6. **Document Processing** → User clicks "Process" to scrape and extract entities
7. **Entity Extraction** → NER processing with project-scoped storage
8. **Visualization** → Network graph shows only entities from current project

### 4.3 Stock Ownership Workflow

**App Startup:**
1. Check for KSEI data updates (Balancepos & StatisEfek TXT files)
2. Check for IDX bulk PDF updates (Pemegang Saham di atas 5%)
3. Download and parse if updates available
4. Update database with latest ownership data

**Data Processing:**
1. Parse Balancepos → aggregate ownership by investor type
2. Parse StatisEfek → company details and ownership percentages
3. Parse IDX PDF → extract shareholders >5% for all companies
4. Create ownership relationships in network graph

---

## 5. Module Overview

### 5.1 Core Modules

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| **Search** (`search.py`) | Web search with DuckDuckGo | `SearchEngine` |
| **Scraping** (`scraper.py`) | Adaptive web scraping | `AdaptiveScraper` |
| **NER** (`ner_extractor.py`) | Indonesian entity extraction | `IndonesianNERExtractor` |
| **Entity Resolution** (`entity_resolver.py`) | Deduplication and canonical naming | `EntityResolver` |
| **Relationship Extraction** (`relationship_extractor.py`) | Extract entity relationships | `RelationshipExtractor` |
| **Database** (`database.py`) | DuckDB management | `DatabaseManager` |

### 5.2 Stock Ownership Module

| Module | Purpose | Update Frequency |
|--------|---------|------------------|
| **KSEI Data Downloader** (`ksei_downloader.py`) | Download Balancepos & StatisEfek | Daily/Weekly |
| **IDX Bulk Scraper** (`idx_bulk_scraper.py`) | Scrape daily bulk PDF from IDX | Daily |

**Data Flow:**
```
KSEI/IDX Websites → Scrapling/HTTP → TXT/PDF Parser → Database → Network Graph
```

**Integration Points:**
- App startup → trigger data update check
- NER detects public company → link to ownership data from database
- User requests company investigation → fetch ownership from database

---

## 6. Data Sources

### 6.1 KSEI Data

| Source | Type | Access | Data Provided | Update Frequency |
|--------|------|--------|---------------|------------------|
| **Balancepos** | Aggregate Ownership | Public download (TXT) | Market-level ownership by investor type | Daily/Weekly |
| **StatisEfek** | Securities Master | Public download (TXT) | Company details, ownership percentages | Daily/Weekly |

**Download URLs:**
- Balancepos: `https://web.ksei.co.id/archive_download/holding_composition`
- StatisEfek: `https://web.ksei.co.id/archive_download/master_securities`

**Format:** Pipe-separated text files (`|` delimiter)

### 6.2 IDX Bulk Shareholder Data

| Source | Type | Access | Data Provided | Update Frequency |
|--------|------|--------|---------------|------------------|
| **Bulk Announcements** | Entity-level Ownership | Public website (PDF) | All companies with >5% shareholders, daily updates | Daily |

**Access Method:**
1. Navigate to `https://www.idx.co.id/id/berita/pengumuman/`
2. Search for keyword: `"Pemegang Saham di atas 5% (KSEI) [Semua Emiten Saham ]"`
3. Download latest PDF

**Format:** PDF with standardized table (13+ columns)

**Data Fields:**
- Kode Efek (Stock Code)
- Nama Emiten (Company Name)
- Nama Pemegang Rekening Efek (Securities Account Holder)
- Nama Pemegang Saham (Shareholder Name)
- Nama Rekening Efek (Securities Account Name)
- Alamat (Address)
- Kebangsaan (Nationality: L=Local, F=Foreign)
- Domisili (Domicile)
- Perubahan (Change in shares)
- Jumlah Saham (Number of Shares)
- Saham Gabungan Per Investor (Combined Shares Per Investor)
- Persentase Kepemilikan Per Investor (%) (Ownership Percentage)

### 6.3 Data Comparison

| Aspect | KSEI Data | IDX Bulk PDF |
|--------|-----------|--------------|
| **Scope** | All listed companies | All listed companies |
| **Detail Level** | Aggregate by investor type | Individual shareholder names |
| **Update Frequency** | Daily/Weekly | Daily |
| **Entity Names** | ❌ No | ✅ Yes |
| **Ownership %** | ✅ By investor type | ✅ By individual shareholder |
| **Address Info** | ❌ No | ✅ Yes |

---

## 7. Development Roadmap

### Phase 1: Foundation ✅ COMPLETE

- [x] Setup DuckDB database with schema migrations
- [x] Configure development environment (hot reload, debugging)
- [x] Integrate DuckDuckGo search
- [x] Implement Scrapling-based scraper
- [x] Download and integrate `cahya/bert-base-indonesian-NER`
- [x] Implement text cleaning and article ranking
- [x] Basic entity extraction and storage
- [ ] Initialize Tauri project with React frontend *(Phase 2)*
- [ ] Setup FastAPI sidecar with basic endpoints *(Phase 2)*
- [ ] Implement sidecar communication layer *(Phase 2)*

**Deliverable:** CLI prototype (search, scrape, extract entities) - **COMPLETE** ✅

**Usage:**
```bash
cd osint-cli

# Full pipeline: Search → Scrape → Extract → Store
uv run python src/main.py process "Prabowo Subianto" --max-results 5

# Individual commands
uv run python src/main.py search "query" --max-results 10
uv run python src/main.py scrape "https://example.com" --extract-entities
uv run python src/main.py ner "text to analyze" --store
uv run python src/main.py entities --limit 50
```

### Phase 2: Core Features ✅ COMPLETE

- [x] Initialize project structure with FastAPI backend
- [x] Setup Python development environment with UV
- [x] Create database models (entities, relationships, documents, ksei_balancepos)
- [x] Setup Tauri desktop shell with React + TypeScript
- [x] Implement search interface component with region selection (Indonesia/International)
- [x] Implement project-based workflow: Project → Search → Documents → Entities → Network
- [x] Project selection as current workspace with data isolation
- [x] Search result selection with checkboxes (all checked by default)
- [x] "Add to Project" flow creating pending documents
- [x] Document status management: pending → processing → completed → error
- [x] Cascade delete: removing document deletes associated entities
- [x] Duplicate detection based on URL when adding search results
- [x] Implement entity list component with filtering by current project
- [x] Integrate D3.js for network visualization with project filtering
- [x] Implement document upload panel with status tracking
- [x] Connect frontend to Python backend via Tauri commands
- [x] Create FastAPI server for backend API
- [x] Implement entity detail panels with tabs for overview, relationships, aliases, and documents
- [x] Implement project management UI for creating, editing, and organizing projects
- [x] Implement fuzzy matching for entity deduplication using sequence matching
- [x] Build entity alias management with canonical name suggestion
- [x] Implement co-occurrence relationship extraction from text
- [x] Add pattern-based relationship extraction (employment, affiliation, family, ownership, location)
- [x] Build relationship confidence scoring with multi-evidence boosting
- [x] Modern UI redesign: slate color palette, compact buttons, less rounded corners

**Deliverable:** Functional desktop app with project-based OSINT workflow - **COMPLETE ✅**

**Workflow:**
```
1. Create/Select Project → 2. Search Web → 3. Select Results → 4. Add to Project
→ 5. Process Documents → 6. View Entities/Network
```

**Current Status:**
```bash
# Quick Start - Run both backend and frontend
./start.sh

# Or run manually:

# Terminal 1: Start Python backend
cd osint-cli
uv run python src/api_server.py

# Terminal 2: Start Tauri frontend
cd osint-app
npm run tauri:dev
```

### Phase 3: Stock Ownership Integration

- [ ] Implement KSEI data downloader (Balancepos & StatisEfek)
- [ ] Implement IDX bulk announcement scraper using Scrapling
- [ ] Build TXT parser for KSEI data
- [ ] Build PDF parser for IDX bulk reports
- [ ] Create fixed output schemas (KSEIRecord, BulkShareholderRecord)
- [ ] Add ownership relationship creation
- [ ] Build ownership history tracking
- [ ] Implement ownership change detection
- [ ] Create alert system for significant changes
- [ ] Add startup data update check

**Deliverable:** Complete ownership network visualization

### Phase 4: Optimization & Polish

- [ ] Quantize NER model to INT8
- [ ] Implement lazy model loading
- [ ] Add memory management and cleanup
- [ ] Implement caching layer
- [ ] Optimize scraping concurrency
- [ ] Add progress indicators and cancellation
- [ ] Comprehensive error handling
- [ ] User-friendly error messages (ID/EN)
- [ ] Add loading states and progress tracking
- [ ] Implement graceful degradation
- [ ] Add offline mode support
- [ ] User testing with journalists (3-5 users)
- [ ] Iterate based on feedback

**Deliverable:** Beta-ready application

### Phase 5: Deployment & Documentation

- [ ] Configure PyInstaller bundling
- [ ] Setup Tauri build pipeline
- [ ] Create Windows installer
- [ ] Implement auto-update mechanism
- [ ] Test on multiple Windows versions
- [ ] Code signing (if budget allows)
- [ ] Write user documentation (Bahasa Indonesia)
- [ ] Create video tutorials
- [ ] Write developer documentation
- [ ] Setup project website
- [ ] Prepare launch materials
- [ ] Beta release to wider group

**Deliverable:** v1.0 release candidate

### Future Enhancements (Post-v1.0)

- [ ] Multi-language support (English, other SE Asian languages)
- [ ] Export formats: GEXF (Gephi), GraphML, JSON-LD
- [ ] Multi-user project sharing
- [ ] Custom entity types and user-trained models
- [ ] Timeline visualization
- [ ] Source credibility scoring
- [ ] Programmatic API access
- [ ] macOS/Linux support
- [ ] Beneficial ownership registry integration
- [ ] Parent-subsidiary relationship mapping
- [ ] Advanced ownership analytics:
  - [ ] Ownership network clustering analysis
  - [ ] Ultimate beneficial owner (UBO) identification
  - [ ] Cross-shareholding detection (circular ownership)
- [ ] Real-time monitoring:
  - [ ] WebSocket-based live ownership alerts
  - [ ] Custom alert rules and thresholds
  - [ ] Alert notification system (email, push)
- [ ] Historical analysis:
  - [ ] Ownership timeline visualization
  - [ ] Historical ownership network reconstruction
  - [ ] Pattern detection in ownership changes

---

## Database Architecture

### Current Approach: Raw SQL with DuckDB

The application currently uses **raw SQL queries** with DuckDB for database operations:

**Advantages:**
- Direct control over queries and performance
- No ORM overhead or abstraction complexity
- DuckDB-specific optimizations (analytical queries, columnar storage)
- Smaller dependency footprint
- Easier to debug and optimize specific queries

**Current Implementation:**
```python
# Example from database.py
def insert_document(self, filename, file_path, ...):
    self.conn.execute(
        """
        INSERT INTO documents (filename, file_path, ...)
        VALUES (?, ?, ...)
        """,
        (filename, file_path, ...),
    )
```

### ORM Migration Consideration

**Issue Raised:** Consider using an ORM (like SQLAlchemy) for better query management.

**Pros of ORM:**
- Type safety and IDE autocomplete
- Easier schema migrations
- Database abstraction (could switch from DuckDB to PostgreSQL/SQLite)
- Relationship handling (less manual JOIN writing)
- Query builder for dynamic queries

**Cons of ORM:**
- Additional dependency and learning curve
- Potential performance overhead for analytical queries
- DuckDB has limited ORM support (SQLAlchemy dialect exists but is less mature)
- Current raw SQL works well for the current scope

**Recommendation:** 
- **Current Phase:** Keep raw SQL - it provides the performance and control needed
- **Future Phase:** Consider SQLAlchemy + Alembic if:
  - Database complexity grows significantly
  - Need to support multiple database backends
  - Team size increases and type safety becomes critical
  - Complex migrations become frequent

**Current Tables:**
- `entities` - Named entities (PERSON, ORGANIZATION, etc.)
- `documents` - Document metadata with status tracking
- `relationships` - Entity relationships
- `projects` - Investigation projects
- `project_documents` - Many-to-many junction
- `entity_aliases` - Alternative names for entities
- `entity_mentions` - Context where entities appear

---

## Quick Reference

### Key Technologies
- **Frontend:** React + TypeScript + D3.js + Radix UI + Tailwind
- **Backend:** Python 3.11+ + FastAPI
- **ML:** Transformers + PyTorch (cahya-ner)
- **Search:** DuckDuckGo-Search + Google Search (with Indonesia/International region support)
- **Scraping:** Scrapling + Playwright
- **Database:** DuckDB with project-based data isolation
- **Packaging:** Tauri + PyInstaller

### Data Sources
- **KSEI Balancepos:** Aggregate ownership by investor type (daily/weekly)
- **KSEI StatisEfek:** Company details and ownership percentages (daily/weekly)
- **IDX Bulk PDF:** Market-wide >5% shareholders (daily)
- **Web Documents:** URLs added from DuckDuckGo search results

### Project-Based OSINT Workflow
1. **Projects** → Create/select a project as your workspace
2. **Search** → Search web (DuckDuckGo/Google, Indonesia/International regions) with max 10 results
3. **Select** → All results checked by default; uncheck unwanted items
4. **Add** → Selected results become "pending" documents in your project
5. **Process** → Click "Process" or enable "Auto-process" to scrape and extract entities
6. **View** → Entities and network graph scoped to current project only

### Key Metrics
- Bundle size: <2GB (with model)
- Memory: 4-8GB RAM
- Response time: <10s search, <5s upload, <2s viz
- Installation: <5 minutes
- Max search results: 10 (default)

### Documentation
- **High-level Architecture:** This file (README.md)
- **Implementation Details:** [IMPLEMENTATION.md](IMPLEMENTATION.md)
