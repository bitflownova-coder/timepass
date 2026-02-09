# 🚀 Copilot Engine

**Deterministic Enforcement & Context Engine for AI-Assisted Development**

A background service that **constrains and validates** AI-generated code by providing deterministic enforcement of schemas, API contracts, dependency impact analysis, and structural integrity — acting as the discipline layer around probabilistic AI models like Claude/Copilot.

## Features

### Intelligence Layer (Original)
| Feature | Description |
|---------|-------------|
| 🔍 **Smart Error Parser** | Analyzes stack traces from Python, JavaScript, TypeScript, Java, Go, Rust |
| 📁 **File Watcher** | Real-time workspace monitoring with watchdog |
| 🧠 **Context Builder** | Generates rich, token-optimized AI prompts with project context |
| 💾 **Fix Pattern Memory** | Learns from past fixes and suggests known solutions |
| 🔌 **VS Code Extension** | Full extension with CodeLens, terminal capture, dashboard, security diagnostics |
| 🌿 **Git Analyzer** | Diff analysis, risk scoring, root cause correlation |
| 🔒 **Security Scanner** | 30+ vulnerability patterns across 7 categories |
| 📊 **SQL Analyzer** | Injection detection, performance anti-patterns, syntax validation |
| 🌐 **API Detector** | Endpoint discovery for Flask, FastAPI, Django, Express, NestJS, Go |
| 🎯 **Behavior Tracker** | Debugging loop detection, focus mode, session reporting |
| 📋 **Prompt Optimizer** | 5 structured templates (debug, analyze, improve, test, general) |
| ⚡ **Cache Layer** | LRU cache with TTL for response times <50ms |

### Enforcement Layer (New)
| Feature | Description |
|---------|-------------|
| 🗄️ **Prisma/ORM Intelligence** | Schema parsing, relation validation, DTO-to-model consistency, migration drift detection |
| 📜 **API Contract Enforcement** | Endpoint registry, HTTP discipline, naming conventions, auth guard consistency, response shape tracking |
| 💥 **Change Impact Analyzer** | Dependency graph, impact radius (BFS), risk scoring, breaking change detection |
| 🔗 **Validation Pipeline** | Unified orchestrator: full scan, incremental file-change scan, pre-commit validation |
| 🔎 **Stack Detector** | Auto-detect language, framework, ORM, auth, test runner, database from project files |

## Quick Start

### Backend Engine

```bash
cd copilot-engine

# Install dependencies
pip install -r requirements.txt

# Run server
python run.py
```

Server starts at `http://127.0.0.1:7779`  
Interactive docs at `http://127.0.0.1:7779/docs`

### VS Code Extension

```bash
cd copilot-engine/extension

# Install & build
npm install
npm run compile

# Package
npx vsce package --no-dependencies

# Install in VS Code
code --install-extension copilot-engine-0.1.0.vsix
```

Or use the one-click scripts:
- **Windows:** `start_engine.bat` (engine) / `build_extension.bat` (extension)

## Architecture

```
┌─────────────────────────┐     REST + WebSocket     ┌─────────────────────────┐
│   VS Code Extension     │ ←────── :7779 ──────→    │   Copilot Engine        │
│                         │                           │   (FastAPI + SQLite)    │
│  ├─ Terminal Capture    │                           │                         │
│  ├─ CodeLens Provider   │                           │  Intelligence Layer:    │
│  ├─ Security Diagnostics│                           │  ├─ Error Parser        │
│  ├─ Git Integration     │                           │  ├─ Context Builder     │
│  ├─ Behavior Tracker    │                           │  ├─ Git Analyzer        │
│  ├─ Prompt Injector     │                           │  ├─ Security Scanner    │
│  ├─ Dashboard Webview   │                           │  ├─ SQL Analyzer        │
│  └─ Status Bar          │                           │  ├─ API Detector        │
└─────────────────────────┘                           │  ├─ Behavior Tracker    │
                                                      │  ├─ Prompt Optimizer    │
                                                      │  └─ Cache Layer (LRU)  │
                                                      │                         │
                                                      │  Enforcement Layer:     │
                                                      │  ├─ Prisma Analyzer     │
                                                      │  ├─ Contract Analyzer   │
                                                      │  ├─ Impact Analyzer     │
                                                      │  └─ Validation Pipeline │
                                                      └─────────────────────────┘
```

## API Endpoints (54 routes)

### Health & Status
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Server info |
| `GET` | `/health` | Health check with uptime |
| `GET` | `/cache/stats` | Cache hit/miss statistics |
| `POST` | `/cache/clear` | Flush all caches |

### Workspace Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/workspace/register` | Register workspace for monitoring |
| `DELETE` | `/workspace/{id}` | Unregister workspace |
| `GET` | `/workspaces` | List all workspaces |

### Error Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/error/parse` | Parse and analyze error text |
| `POST` | `/error/find-similar` | Find similar past errors and fixes |

### Context Building
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/context/build` | Build AI-ready context prompt |
| `POST` | `/context/debug` | Build debug-specific context |

### Session
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/session/update` | Update coding session context |
| `GET` | `/session/{path}` | Get session info |

### Files
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/files/{path}` | List files in workspace |
| `GET` | `/file/content` | Get file content |

### Git Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/git/diff` | Analyze diff with risk scoring |
| `GET` | `/git/recent-commits/{ws}` | Recent commits |
| `POST` | `/git/analyze-change` | Per-file risk analysis |
| `POST` | `/git/correlate` | Error root cause correlation |
| `GET` | `/git/branch/{ws}` | Current branch |
| `GET` | `/git/changed-files/{ws}` | Changed file list |

### Security
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/security/scan` | Scan file (cached 120s) |
| `POST` | `/security/scan-workspace` | Scan workspace (cached 120s) |

### SQL
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/sql/analyze` | Analyze query for issues |
| `POST` | `/sql/validate` | Validate query syntax |

### API Detection
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/detect` | Detect endpoints (cached 60s) |
| `POST` | `/api/validate` | Validate API call |

### Behavior
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/behavior/track` | Track developer event |
| `GET` | `/behavior/status/{ws}` | Current status |
| `GET` | `/behavior/report/{ws}` | Session report |

### Prompt
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/prompt/optimize` | Build optimized AI prompt |

### WebSocket
| Method | Endpoint | Description |
|--------|----------|-------------|
| `WS` | `/ws/{workspace_path}` | Real-time updates |

### Prisma / ORM Intelligence
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/prisma/analyze` | Full Prisma schema analysis |
| `POST` | `/prisma/validate` | Validate schema against rules |
| `POST` | `/prisma/schema` | Parse schema into structured data |
| `POST` | `/prisma/validate-dto` | Check DTO-to-model consistency |
| `POST` | `/prisma/check-include` | Validate include/select usage |

### API Contract Enforcement
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/contracts/analyze` | Analyze workspace for API contracts |
| `POST` | `/contracts/validate` | Validate contracts against rules |
| `POST` | `/contracts/check` | Check specific contract compliance |
| `POST` | `/contracts/map` | Get endpoint contract map |

### Change Impact Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/impact/build-graph` | Build file dependency graph |
| `POST` | `/impact/analyze` | Analyze single file change impact |
| `POST` | `/impact/analyze-multi` | Analyze multi-file change impact |
| `POST` | `/impact/file-info` | Get file category and dependencies |
| `POST` | `/impact/dependency-map` | Get full dependency map |

### Validation Pipeline
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/pipeline/full-scan` | Comprehensive workspace audit |
| `POST` | `/pipeline/file-change` | Incremental file change validation |
| `POST` | `/pipeline/pre-commit` | Pre-commit validation check |
| `POST` | `/stack/detect` | Auto-detect project stack |

## Usage Examples

### Register a Workspace
```bash
curl -X POST http://127.0.0.1:7779/workspace/register \
  -H "Content-Type: application/json" \
  -d '{"path": "C:/Projects/my-app"}'
```

### Parse an Error
```bash
curl -X POST http://127.0.0.1:7779/error/parse \
  -H "Content-Type: application/json" \
  -d '{"error_text": "TypeError: Cannot read property x of undefined"}'
```

### Build Context for Copilot
```bash
curl -X POST http://127.0.0.1:7779/context/build \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_path": "C:/Projects/my-app",
    "current_file": "src/index.js",
    "task": "Fix the null reference error"
  }'
```

### Analyze Git Diff
```bash
curl -X POST http://127.0.0.1:7779/git/diff \
  -H "Content-Type: application/json" \
  -d '{"workspace_path": "C:/Projects/my-app"}'
```

### Security Scan
```bash
curl -X POST http://127.0.0.1:7779/security/scan \
  -H "Content-Type: application/json" \
  -d '{"file_path": "C:/Projects/my-app/src/auth.py"}'
```

### SQL Analysis
```bash
curl -X POST http://127.0.0.1:7779/sql/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM users WHERE id = 1"}'
```

## File Structure

```
copilot-engine/
├── server.py              # FastAPI server (54 routes)
├── config.py              # Pydantic settings
├── database.py            # SQLAlchemy session manager
├── models.py              # 6 SQLAlchemy models with indexes
├── cache.py               # LRU cache layer with TTL
├── file_watcher.py        # Watchdog workspace monitoring
├── error_parser.py        # Multi-language error parser
├── context_builder.py     # AI prompt context builder
├── git_analyzer.py        # Git diff/risk/correlation analysis
├── security_scanner.py    # Security vulnerability scanner
├── sql_analyzer.py        # SQL query analyzer/validator
├── api_detector.py        # API endpoint detector
├── behavior_tracker.py    # Developer behavior analyzer
├── prompt_optimizer.py    # Optimized prompt builder
├── prisma_analyzer.py     # Prisma/ORM intelligence layer
├── contract_analyzer.py   # API contract enforcement system
├── impact_analyzer.py     # Change impact analyzer
├── validation_pipeline.py # Unified validation pipeline
├── run.py                 # Entry point
├── requirements.txt       # Python dependencies
├── start_engine.bat       # One-click launcher (Windows)
├── build_extension.bat    # Extension build script
├── README.md              # This file
├── tests/                 # Test suites
│   ├── test_modules.py    # 53 unit tests
│   ├── test_api.py        # 34 integration tests
│   └── test_enforcement.py# 62 enforcement tests
└── extension/             # VS Code extension
    ├── package.json       # Extension manifest
    ├── tsconfig.json      # TypeScript config
    ├── webpack.config.js
    ├── src/               # 13 TypeScript modules
    ├── dist/              # Compiled bundle (105 KB)
    └── *.vsix             # Packaged extension
```

## Configuration

Environment variables (prefix `COPILOT_ENGINE_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Server host |
| `PORT` | `7779` | Server port |
| `DEBUG` | `true` | Debug mode |
| `MAX_PROMPT_TOKENS` | `4000` | Max tokens for context prompts |
| `MAX_STORED_FIXES` | `1000` | Max fix patterns in database |

## VS Code Extension

The extension provides:
- **Terminal Capture**: Auto-detect errors in terminal output (20+ patterns)
- **CodeLens**: Inline actions above functions (Analyze, Test, Security, Improve)
- **Security Diagnostics**: Real-time inline warnings with OWASP links
- **Git Integration**: Auto risk analysis on save, root cause correlation
- **Prompt Injection**: Structured context comments for Copilot
- **Behavior Tracking**: Debugging loop detection, focus mode
- **Dashboard**: Session metrics, workspace listing, action buttons

### Extension Commands
| Command | Shortcut | Description |
|---------|----------|-------------|
| Start Engine | — | Start backend server |
| Analyze Code | `Ctrl+Shift+A` | Analyze selection |
| Build Context | `Ctrl+Shift+C` | Build Copilot context |
| Inject Context | `Ctrl+Shift+I` | Insert context comment |
| Security Check | — | Scan current file |
| Show Dashboard | — | Open metrics panel |
| Toggle Focus | — | Enter/exit focus mode |

### Install Extension
```bash
code --install-extension copilot-engine-0.1.0.vsix
```

## License

MIT
