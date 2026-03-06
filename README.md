# Design Document: Local OSINT NER & Network Viz Tool

> **Version:** 1.0.0
> **Last Updated:** 2026-03-06
> **Status:** Phase 1 ✅ Complete (CLI Prototype Working)

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

1. **Passive Mode:** Processing manually uploaded local documents (PDFs, HTML, TXT)
2. **Active Mode (OSINT):** Web search → intelligent scraping → entity extraction
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
│  │  - Database queries (DuckDB)                           │ │
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
│  │  - Text cleaning                                       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  NLP Pipeline                                          │ │
│  │  - cahya-ner (entity extraction)                       │ │
│  │  - Keyword-based article ranking                       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Data Layer                                            │ │
│  │  - Entity resolution & deduplication                   │ │
│  │  - Relationship extraction                             │ │
│  │  - DuckDB storage                                      │ │
│  │  - KSEI/IDX data integration                           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 OSINT Search Workflow

1. **Query Initiation** → User types query, frontend validates and dispatches
2. **Web Search** → DuckDuckGo search, filter and prioritize results
3. **Parallel Scraping** → Scrapling extraction with rate limiting
4. **Article Ranking** → Keyword matching and TF-IDF scoring
5. **Entity Extraction** → NER processing → deduplication → relationship extraction
6. **Storage & Visualization** → Database persistence → network graph rendering

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

### Phase 2: Core Features 🔄 IN PROGRESS

- [x] Initialize project structure with FastAPI backend
- [x] Setup Python development environment with UV
- [x] Create database models (entities, relationships, documents, ksei_balancepos)
- [x] Setup Tauri desktop shell with React + TypeScript
- [x] Implement search interface component
- [x] Implement entity list component with filtering
- [x] Integrate D3.js for network visualization
- [x] Implement document upload panel
- [x] Connect frontend to Python backend via Tauri commands
- [x] Create FastAPI server for backend API
- [ ] Implement entity detail panels
- [ ] Implement project management UI
- [ ] Implement fuzzy matching for entity deduplication
- [ ] Build entity alias management
- [ ] Implement co-occurrence relationship extraction
- [ ] Add pattern-based relationship extraction
- [ ] Build relationship confidence scoring

**Deliverable:** Functional desktop app with visualization - **IN PROGRESS**

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

## Quick Reference

### Key Technologies
- **Frontend:** React + TypeScript + D3.js + Radix UI + Tailwind
- **Backend:** Python 3.11+ + FastAPI
- **ML:** Transformers + PyTorch (cahya-ner)
- **Search:** DuckDuckGo-Search
- **Scraping:** Scrapling + Playwright
- **Database:** DuckDB
- **Packaging:** Tauri + PyInstaller

### Data Sources
- **KSEI Balancepos:** Aggregate ownership by investor type (daily/weekly)
- **KSEI StatisEfek:** Company details and ownership percentages (daily/weekly)
- **IDX Bulk PDF:** Market-wide >5% shareholders (daily)

### Key Metrics
- Bundle size: <2GB (with model)
- Memory: 4-8GB RAM
- Response time: <10s search, <5s upload, <2s viz
- Installation: <5 minutes

### Documentation
- **High-level Architecture:** This file (README.md)
- **Implementation Details:** [IMPLEMENTATION.md](IMPLEMENTATION.md)
