# OSINT NER Desktop App

Tauri-based desktop application for OSINT (Open Source Intelligence) with Named Entity Recognition.

## Features

- **Search Panel**: Web search with DuckDuckGo integration + Full pipeline processing
- **Entity Database**: Browse and filter extracted entities with real-time stats
- **Network Visualization**: Interactive D3.js graph of entity relationships
- **Document Management**: Upload and process documents

## Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend Bridge**: Rust (Tauri) with HTTP client
- **Python API**: FastAPI server for NER processing
- **Visualization**: D3.js
- **Icons**: Lucide React

## Development

### Prerequisites

- Node.js 18+
- Rust 1.70+
- Python 3.11+ (for the CLI backend)

### Installation

```bash
npm install
```

### Running the App

**Option 1: Use the startup script (Recommended)**
```bash
cd /home/ares/Documents/HARISWB/media-pipeline/osint
./start.sh
```

**Option 2: Manual startup**
```bash
# Terminal 1: Start Python API server
cd /home/ares/Documents/HARISWB/media-pipeline/osint/osint-cli
uv run python src/api_server.py

# Terminal 2: Start Tauri app
cd /home/ares/Documents/HARISWB/media-pipeline/osint/osint-app
npm run tauri:dev
```

### Build

```bash
npm run tauri:build
```

## Project Structure

```
osint-app/
├── src/                    # React frontend
│   ├── components/         # React components
│   │   ├── SearchPanel.tsx      # Web search + processing
│   │   ├── EntityList.tsx       # Entity browser
│   │   ├── NetworkGraph.tsx     # D3.js visualization
│   │   └── DocumentPanel.tsx    # File upload
│   ├── services/
│   │   └── api.ts               # API client for Tauri commands
│   ├── App.tsx                 # Main app component
│   ├── main.tsx                # Entry point
│   └── styles.css              # Global styles + Tailwind
├── src-tauri/             # Rust backend
│   ├── src/
│   │   └── main.rs        # Tauri commands + HTTP client
│   ├── Cargo.toml         # Rust dependencies
│   ├── tauri.conf.json    # Tauri configuration
│   └── icons/             # App icons
├── package.json           # Node dependencies
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind configuration
└── tsconfig.json          # TypeScript configuration
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Tauri Frontend                    │
│  ┌──────────────┬──────────────┬─────────────────┐  │
│  │ React + TS   │  Tailwind    │    D3.js        │  │
│  │ Components   │    CSS       │   Graph Viz     │  │
│  └──────────────┴──────────────┴─────────────────┘  │
│                      │                              │
│           Tauri Invoke Commands                      │
│                      │                              │
│  ┌───────────────────┴───────────────────────┐     │
│  │          Rust HTTP Client                  │     │
│  │   (reqwest + tauri-plugin-http)           │     │
│  └───────────────────┬───────────────────────┘     │
└──────────────────────┼──────────────────────────────┘
                       │ HTTP
                       ▼
┌─────────────────────────────────────────────────────┐
│              Python FastAPI Backend                 │
│  ┌──────────────┬──────────────┬─────────────────┐  │
│  │   Search     │    NER       │    DuckDB       │  │
│  │  (DuckDuckGo)│  (cahya-ner) │   Database      │  │
│  └──────────────┴──────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## API Endpoints

The Python backend exposes these REST endpoints:

- `GET /health` - Health check
- `GET /api/stats` - Database statistics
- `GET /api/entities` - List entities (with optional type filter)
- `POST /api/search` - Web search
- `POST /api/scrape` - Scrape URL
- `POST /api/extract` - Extract entities from text
- `POST /api/process` - Full pipeline (Search → Scrape → Extract → Store)
- `POST /api/upload` - Upload document

## Integration Status

✅ **Completed:**
- Tauri + React frontend with sidebar navigation
- FastAPI backend with all endpoints
- Rust HTTP client for backend communication
- Entity list with live data from DuckDB
- Search panel with full pipeline support
- Backend health monitoring
- Dynamic statistics in sidebar

🔄 **In Progress:**
- Network graph with real relationship data
- Document upload processing
- Entity detail modal

## Troubleshooting

**Backend not connected:**
- Make sure Python API server is running on port 8000
- Check that `uv run python src/api_server.py` started without errors

**Build errors:**
- Ensure all dependencies are installed: `npm install`
- Build frontend first: `npm run build`
- Check Rust is installed: `rustc --version`

**Icons missing:**
The build requires icon files in `src-tauri/icons/`. Run the startup script which creates placeholder icons automatically.
