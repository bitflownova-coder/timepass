# Copilot Engine - Dev Intelligence Layer

An invisible AI-powered development intelligence layer for VS Code that enhances your coding workflow with automatic error capture, smart context building, security scanning, and more.

## Features

### 🔍 Automatic Error Capture
Terminal errors are detected instantly across **Python, JavaScript, TypeScript, Java, Go, and Rust**. Get immediate suggestions without lifting a finger.

### 🧠 CodeLens Intelligence
Inline actions appear above every function:
- **Analyze** — Deep analysis with AI context
- **Test** — Generate test prompts
- **Security** — Scan for vulnerabilities
- **Improve** — Inject context for Copilot

### 🔒 Real-Time Security Scanning
30+ security patterns detected inline with red/yellow diagnostics:
- SQL injection, hardcoded secrets, eval() usage
- Weak crypto, JWT issues, CORS misconfigurations
- Path traversal, information disclosure

### 🌿 Git Awareness
Correlate errors with recent changes. When something breaks, the engine identifies which commit likely caused it, with risk scoring for every diff.

### 📋 Smart Context Building
Build structured, token-optimized prompts for GitHub Copilot Chat. One keystroke (`Ctrl+Shift+C`) injects rich project context at cursor position.

### 🎯 Focus Mode
Detects debugging loops (repeated errors, rapid file switching) and suggests entering Focus Mode for guided debugging.

### 📊 Dashboard
Real-time dashboard showing session metrics, registered workspaces, error counts, and focus mode status.

## Requirements

- **Copilot Engine** backend must be running (Python 3.10+)
- Install engine dependencies: `pip install -r requirements.txt`
- Start engine: `python run.py` (starts on `http://127.0.0.1:7779`)

## Quick Start

1. Install the extension
2. Start the backend engine: `python run.py` (from copilot-engine directory)
3. Open any project — workspace auto-registers
4. Code normally — errors captured, CodeLens appears, security scanning active

## Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| Start Engine | — | Start the backend server |
| Stop Engine | — | Stop the backend server |
| Analyze Code | `Ctrl+Shift+A` | Analyze selected code |
| Build Context | `Ctrl+Shift+C` | Build context for Copilot |
| Inject Context | `Ctrl+Shift+I` | Inject context comment |
| Security Check | — | Scan current file for vulnerabilities |
| Show Dashboard | — | Open the metrics dashboard |
| Toggle Focus Mode | — | Enter/exit focus mode |

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `copilotEngine.host` | `127.0.0.1` | Engine host |
| `copilotEngine.port` | `7779` | Engine port |
| `copilotEngine.autoStart` | `true` | Auto-start on launch |
| `copilotEngine.terminalCapture` | `true` | Capture terminal errors |
| `copilotEngine.codeLensEnabled` | `true` | Show CodeLens actions |
| `copilotEngine.securityWarnings` | `true` | Inline security diagnostics |
| `copilotEngine.notificationLevel` | `errors` | Notification verbosity |
| `copilotEngine.focusModeThreshold` | `5` | Errors before focus mode |

## Architecture

```
Extension (TypeScript)  ←→  Engine (FastAPI/Python)
  ├─ Terminal Capture          ├─ Error Parser (6 langs)
  ├─ CodeLens Provider         ├─ Context Builder
  ├─ Security Diagnostics      ├─ Git Analyzer
  ├─ Git Integration           ├─ Security Scanner
  ├─ Behavior Tracker          ├─ SQL Analyzer
  ├─ Prompt Injector           ├─ API Detector
  └─ Dashboard Webview         ├─ Behavior Tracker
                               ├─ Prompt Optimizer
                               └─ Cache Layer (LRU)
```

Communication: REST API + WebSocket on port 7779

## API Endpoints

The engine exposes 36 REST endpoints:

- **Health:** `/health`, `/cache/stats`
- **Workspaces:** register, list, delete
- **Errors:** parse, find-similar
- **Context:** build, debug
- **Git:** diff, commits, risk, correlate, branch, changed-files
- **Security:** scan file, scan workspace
- **SQL:** analyze, validate
- **API:** detect endpoints, validate calls
- **Behavior:** track, status, report
- **Prompt:** optimize

Full interactive docs at `http://127.0.0.1:7779/docs`

## License

MIT
