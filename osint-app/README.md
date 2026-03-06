# OSINT NER Desktop App

Tauri-based desktop application for OSINT (Open Source Intelligence) with Named Entity Recognition.

## Features

- **Search Panel**: Web search with DuckDuckGo integration
- **Entity Database**: Browse and filter extracted entities
- **Network Visualization**: Interactive D3.js graph of entity relationships
- **Document Management**: Upload and process documents

## Tech Stack

- **Frontend**: React + TypeScript + Vite
- **Backend**: Rust (Tauri)
- **Styling**: Tailwind CSS
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

### Development Server

```bash
# Run the frontend dev server
npm run dev

# Run the Tauri app (in another terminal)
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
│   │   ├── SearchPanel.tsx
│   │   ├── EntityList.tsx
│   │   ├── NetworkGraph.tsx
│   │   └── DocumentPanel.tsx
│   ├── App.tsx            # Main app component
│   ├── main.tsx           # Entry point
│   └── styles.css         # Global styles
├── src-tauri/             # Rust backend
│   ├── src/
│   │   └── main.rs        # Rust main file
│   ├── Cargo.toml         # Rust dependencies
│   └── tauri.conf.json    # Tauri configuration
├── package.json           # Node dependencies
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind configuration
└── tsconfig.json          # TypeScript configuration
```

## Next Steps

- [ ] Connect to Python backend via sidecar
- [ ] Implement real data fetching from DuckDB
- [ ] Add export functionality
- [ ] Implement relationship extraction
- [ ] Add settings panel with configuration options
