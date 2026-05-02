"""
Copilot Engine - Local Development Intelligence Server
"""
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config import settings
from database import db
from models import Workspace, ErrorLog, FixPattern, ContextSession
from file_watcher import watcher_manager, FileChange
from error_parser import error_parser, ParsedError
from context_builder import context_builder, BuiltContext
from git_analyzer import GitAnalyzer
from security_scanner import SecurityScanner
from sql_analyzer import SQLAnalyzer
from api_detector import APIDetector
from behavior_tracker import BehaviorTracker
from prompt_optimizer import PromptOptimizer
from cache import response_cache, project_cache, security_cache, make_key
from prisma_analyzer import PrismaAnalyzer
from contract_analyzer import ContractAnalyzer
from impact_analyzer import ImpactAnalyzer
from validation_pipeline import ValidationPipeline, StackDetector
from semantic_indexer import SemanticIndexer
from ast_security_scanner import ASTSecurityScanner
from dead_code_detector import DeadCodeDetector
from code_quality_analyzer import CodeQualityAnalyzer
from runtime_error_predictor import RuntimeErrorPredictor
from dependency_analyzer import DependencyAnalyzer
from copilot_style_detector import CopilotStyleDetector
from graph_engine import GraphEngine
from drift_detector import DriftDetector
from migration_monitor import MigrationMonitor
from risk_engine import RiskEngine
from background_worker import BackgroundWorker, ChangeEvent

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce SQLAlchemy logging verbosity (only show warnings and errors)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


def _normalize_ws_path(workspace_path: str) -> str:
    """Normalize workspace path from URL (forward slashes) to OS-native format."""
    return str(Path(workspace_path))


# ============== Pydantic Models ==============

class WorkspaceCreate(BaseModel):
    path: str
    name: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: int
    path: str
    name: Optional[str]
    language: Optional[str]
    framework: Optional[str]
    last_active: datetime


class ErrorInput(BaseModel):
    error_text: str
    workspace_path: Optional[str] = None
    file_path: Optional[str] = None


class ErrorResponse(BaseModel):
    error_type: str
    message: str
    file_path: Optional[str]
    line_number: Optional[int]
    suggestions: List[str]
    related_files: List[str]
    language: Optional[str]


class ContextRequest(BaseModel):
    workspace_path: str
    current_file: Optional[str] = None
    error_text: Optional[str] = None
    task: str = "Help me with this code"
    include_schema: bool = False


class ContextResponse(BaseModel):
    prompt: str
    token_estimate: int
    metadata: Dict[str, Any]


class FileChangeEvent(BaseModel):
    path: str
    event_type: str
    timestamp: datetime


class SessionUpdate(BaseModel):
    workspace_path: str
    current_file: Optional[str] = None
    terminal_output: Optional[str] = None
    git_branch: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    watched_workspaces: List[str]


# ============== WebSocket Connection Manager ==============

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}  # workspace -> connections
    
    async def connect(self, websocket: WebSocket, workspace: str):
        await websocket.accept()
        if workspace not in self.active_connections:
            self.active_connections[workspace] = []
        self.active_connections[workspace].append(websocket)
        logger.info(f"WebSocket connected for workspace: {workspace}")
    
    def disconnect(self, websocket: WebSocket, workspace: str):
        if workspace in self.active_connections:
            if websocket in self.active_connections[workspace]:
                self.active_connections[workspace].remove(websocket)
            if not self.active_connections[workspace]:
                del self.active_connections[workspace]
        logger.info(f"WebSocket disconnected for workspace: {workspace}")
    
    async def broadcast(self, workspace: str, message: dict):
        if workspace in self.active_connections:
            for connection in self.active_connections[workspace]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
    
    async def broadcast_all(self, message: dict):
        for workspace in self.active_connections:
            await self.broadcast(workspace, message)


manager = ConnectionManager()
start_time = datetime.now(timezone.utc)

# Module instances
git_analyzer = GitAnalyzer()
security_scanner = SecurityScanner()
sql_analyzer = SQLAnalyzer()
api_detector = APIDetector()
behavior_tracker = BehaviorTracker()
prompt_optimizer = PromptOptimizer()
prisma_analyzer = PrismaAnalyzer()
contract_analyzer = ContractAnalyzer()
impact_analyzer = ImpactAnalyzer()
validation_pipeline = ValidationPipeline()
stack_detector = StackDetector()

# Autonomous runtime modules
semantic_indexer = SemanticIndexer()
graph_engine = GraphEngine()
drift_detector = DriftDetector()
migration_monitor = MigrationMonitor()
risk_engine = RiskEngine()
background_worker = BackgroundWorker(
    db_factory=db.get_session,
    indexer=semantic_indexer,
    graph_engine=graph_engine,
    drift_detector=drift_detector,
    migration_monitor=migration_monitor,
    risk_engine=risk_engine,
    security_scanner=security_scanner,
    prisma_analyzer=prisma_analyzer,
    contract_analyzer=contract_analyzer,
)


# ============== App Lifecycle ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Starting Copilot Engine...")
    db.init_db()
    
    # Capture the main event loop for thread-safe callbacks
    main_loop = asyncio.get_running_loop()
    
    # Setup file watcher callback (runs in watchdog thread, NOT asyncio thread)
    def on_file_change(workspace_path: str, change: FileChange):
        try:
            # Schedule the async broadcast on the main event loop from this thread
            main_loop.call_soon_threadsafe(
                main_loop.create_task,
                manager.broadcast(workspace_path, {
                    "type": "file_change",
                    "data": {
                        "path": str(change.path),
                        "event_type": change.event_type,
                        "timestamp": change.timestamp.isoformat()
                    }
                })
            )
        except Exception:
            pass  # Silently ignore if loop is closed
    
    watcher_manager.add_callback(on_file_change)
    
    # ── Start autonomous background worker ──
    def ws_broadcast_sync(workspace_path: str, event_type: str, data: dict):
        """Bridge sync background worker → async WebSocket broadcast."""
        try:
            main_loop.call_soon_threadsafe(
                main_loop.create_task,
                manager.broadcast(workspace_path, {
                    "type": event_type,
                    "data": data,
                })
            )
        except Exception:
            pass  # Silently ignore if loop is closed

    background_worker._broadcast = ws_broadcast_sync
    background_worker.start()

    logger.info(f"Copilot Engine started on {settings.host}:{settings.port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Copilot Engine...")
    background_worker.stop()
    watcher_manager.stop_all()


# ============== FastAPI App ==============

app = FastAPI(
    title="Copilot Engine",
    description="Local Development Intelligence Layer",
    version="0.1.0",
    lifespan=lifespan
)

# CORS for VS Code extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # VS Code extension
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Performance Middleware ==============

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time as _time


class TimingMiddleware(BaseHTTPMiddleware):
    """Add X-Response-Time header to every response."""

    async def dispatch(self, request: Request, call_next):
        t0 = _time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((_time.perf_counter() - t0) * 1000, 2)
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
        if elapsed_ms > 200:
            logger.warning(f"Slow response: {request.url.path} took {elapsed_ms}ms")
        return response


app.add_middleware(TimingMiddleware)


# ============== Health & Status ==============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        uptime=(datetime.now(timezone.utc) - start_time).total_seconds(),
        watched_workspaces=watcher_manager.get_watched()
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Copilot Engine",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/cache/stats")
async def cache_stats():
    """Return hit/miss stats for all caches."""
    return {
        "response": response_cache.stats,
        "project": project_cache.stats,
        "security": security_cache.stats,
    }


@app.post("/cache/clear")
async def clear_caches():
    """Flush all in-memory caches."""
    response_cache.clear()
    project_cache.clear()
    security_cache.clear()
    return {"status": "cleared"}


# ============== Workspace Management ==============

@app.post("/workspace/register", response_model=WorkspaceResponse)
async def register_workspace(workspace: WorkspaceCreate):
    """Register a workspace for monitoring"""
    path = Path(workspace.path)
    
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid workspace path")
    
    # Detect project info
    project = context_builder.get_project_context(str(path))
    
    with db.get_session() as session:
        # Check if already exists
        existing = session.query(Workspace).filter(Workspace.path == str(path)).first()
        
        if existing:
            existing.last_active = datetime.now(timezone.utc)
            existing.language = project.language
            existing.framework = project.framework
            session.commit()
            ws = existing
        else:
            ws = Workspace(
                path=str(path),
                name=workspace.name or path.name,
                language=project.language,
                framework=project.framework
            )
            session.add(ws)
            session.commit()
            session.refresh(ws)
        
        # Start watching
        watcher_manager.watch(str(path))
        
        return WorkspaceResponse(
            id=ws.id,
            path=ws.path,
            name=ws.name,
            language=ws.language,
            framework=ws.framework,
            last_active=ws.last_active
        )


@app.delete("/workspace/{workspace_id}")
async def unregister_workspace(workspace_id: int):
    """Unregister a workspace"""
    with db.get_session() as session:
        ws = session.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        watcher_manager.unwatch(ws.path)
        session.delete(ws)
        
        return {"status": "removed", "path": ws.path}


@app.get("/workspaces", response_model=List[WorkspaceResponse])
async def list_workspaces():
    """List all registered workspaces"""
    with db.get_session() as session:
        workspaces = session.query(Workspace).all()
        return [
            WorkspaceResponse(
                id=ws.id,
                path=ws.path,
                name=ws.name,
                language=ws.language,
                framework=ws.framework,
                last_active=ws.last_active
            )
            for ws in workspaces
        ]


# ============== Error Analysis ==============

@app.post("/error/parse", response_model=ErrorResponse)
async def parse_error(error_input: ErrorInput, background_tasks: BackgroundTasks):
    """Parse and analyze an error"""
    parsed = error_parser.parse(error_input.error_text)
    
    # Log error in background
    if error_input.workspace_path:
        background_tasks.add_task(log_error, error_input.workspace_path, parsed)
    
    return ErrorResponse(
        error_type=parsed.error_type,
        message=parsed.message,
        file_path=parsed.file_path,
        line_number=parsed.line_number,
        suggestions=parsed.suggestions,
        related_files=parsed.related_files,
        language=parsed.language
    )


async def log_error(workspace_path: str, error: ParsedError):
    """Background task to log error"""
    try:
        with db.get_session() as session:
            ws = session.query(Workspace).filter(Workspace.path == workspace_path).first()
            if ws:
                error_log = ErrorLog(
                    workspace_id=ws.id,
                    error_type=error.error_type,
                    message=error.message,
                    stack_trace=error.raw_output,
                    file_path=error.file_path,
                    line_number=error.line_number
                )
                session.add(error_log)
    except Exception as e:
        logger.error(f"Failed to log error: {e}")


@app.post("/error/find-similar")
async def find_similar_errors(error_input: ErrorInput):
    """Find similar past errors and their fixes"""
    parsed = error_parser.parse(error_input.error_text)
    
    with db.get_session() as session:
        # Find similar fix patterns
        similar = session.query(FixPattern).filter(
            FixPattern.error_type == parsed.error_type
        ).order_by(FixPattern.success_count.desc()).limit(5).all()
        
        return {
            "current_error": {
                "type": parsed.error_type,
                "message": parsed.message
            },
            "similar_fixes": [
                {
                    "description": fix.description,
                    "fix": fix.fix_description,
                    "success_count": fix.success_count,
                    "last_used": fix.last_used.isoformat()
                }
                for fix in similar
            ]
        }


# ============== Context Building ==============

@app.post("/context/build", response_model=ContextResponse)
async def build_context(request: ContextRequest):
    """Build AI-ready context"""
    project = context_builder.get_project_context(request.workspace_path)
    
    current_file = None
    if request.current_file:
        current_file = context_builder.get_file_context(request.current_file,
                                                         workspace_path=request.workspace_path)
    
    error_ctx = None
    if request.error_text:
        parsed_error = error_parser.parse(request.error_text)
        error_ctx = context_builder.build_error_context(parsed_error, request.workspace_path)
    
    built = context_builder.build_prompt(
        task=request.task,
        current_file=current_file,
        project=project,
        error=error_ctx
    )
    
    return ContextResponse(
        prompt=built.prompt,
        token_estimate=built.token_estimate,
        metadata=built.metadata
    )


@app.post("/context/debug")
async def build_debug_context(error_input: ErrorInput):
    """Build context specifically for debugging"""
    if not error_input.workspace_path:
        raise HTTPException(status_code=400, detail="workspace_path required for debug context")
    
    parsed = error_parser.parse(error_input.error_text)
    built = context_builder.build_debug_prompt(parsed, error_input.workspace_path)
    
    return ContextResponse(
        prompt=built.prompt,
        token_estimate=built.token_estimate,
        metadata=built.metadata
    )


# ============== Session Management ==============

@app.post("/session/update")
async def update_session(update: SessionUpdate):
    """Update current coding session context"""
    with db.get_session() as session:
        ws = session.query(Workspace).filter(Workspace.path == update.workspace_path).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not registered")
        
        # Find or create session
        ctx_session = session.query(ContextSession).filter(
            ContextSession.workspace_id == ws.id
        ).first()
        
        if not ctx_session:
            ctx_session = ContextSession(workspace_id=ws.id)
            session.add(ctx_session)
        
        # Update fields
        if update.current_file:
            ctx_session.current_file = update.current_file
            # Add to recent files
            recent = ctx_session.recent_files or []
            if update.current_file not in recent:
                recent.insert(0, update.current_file)
                ctx_session.recent_files = recent[:10]
        
        if update.terminal_output:
            ctx_session.terminal_output = update.terminal_output
        
        if update.git_branch:
            ctx_session.git_branch = update.git_branch
        
        ctx_session.last_update = datetime.now(timezone.utc)
        ws.last_active = datetime.now(timezone.utc)
        
        return {"status": "updated"}


@app.get("/session/{workspace_path:path}")
async def get_session(workspace_path: str):
    """Get current session for workspace"""
    with db.get_session() as session:
        ws = session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        ctx_session = session.query(ContextSession).filter(
            ContextSession.workspace_id == ws.id
        ).first()
        
        if not ctx_session:
            return {"workspace": workspace_path, "session": None}
        
        return {
            "workspace": workspace_path,
            "session": {
                "current_file": ctx_session.current_file,
                "recent_files": ctx_session.recent_files,
                "git_branch": ctx_session.git_branch,
                "last_update": ctx_session.last_update.isoformat()
            }
        }


# ============== WebSocket ==============

@app.websocket("/ws/{workspace_path:path}")
async def websocket_endpoint(websocket: WebSocket, workspace_path: str):
    """WebSocket for real-time updates"""
    await manager.connect(websocket, workspace_path)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle different message types
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif data.get("type") == "file_opened":
                await update_session(SessionUpdate(
                    workspace_path=workspace_path,
                    current_file=data.get("file")
                ))
            
            elif data.get("type") == "error":
                parsed = error_parser.parse(data.get("error_text", ""))
                await websocket.send_json({
                    "type": "error_parsed",
                    "data": {
                        "error_type": parsed.error_type,
                        "message": parsed.message,
                        "suggestions": parsed.suggestions
                    }
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, workspace_path)


# ============== File Operations ==============

@app.get("/files/{workspace_path:path}")
async def list_files(workspace_path: str, extension: str = None):
    """List files in workspace"""
    workspace_path = _normalize_ws_path(workspace_path)
    path = Path(workspace_path)
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    files = []
    for file in path.rglob("*"):
        if file.is_file():
            # Skip ignored directories
            skip = False
            for ignored in settings.ignored_dirs:
                if ignored in str(file):
                    skip = True
                    break
            
            if skip:
                continue
            
            if extension and file.suffix != extension:
                continue
            
            files.append({
                "path": str(file),
                "relative": str(file.relative_to(path)),
                "extension": file.suffix,
                "size": file.stat().st_size
            })
    
    return {"workspace": workspace_path, "files": files[:500]}  # Limit to 500


@app.get("/file/content")
async def get_file_content(file_path: str, max_lines: int = 500):
    """Get file content"""
    path = Path(file_path)
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        lines = path.read_text().split('\n')[:max_lines]
        return {
            "path": file_path,
            "content": '\n'.join(lines),
            "truncated": len(lines) >= max_lines,
            "language": context_builder.detect_language(file_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Git Analysis ==============

class GitDiffRequest(BaseModel):
    workspace_path: str

class GitChangeRiskRequest(BaseModel):
    workspace_path: str
    file_path: str

class GitCorrelateRequest(BaseModel):
    workspace_path: str
    error_text: str

@app.post("/git/diff")
async def analyze_git_diff(request: GitDiffRequest):
    """Analyze current git diff for risk"""
    return git_analyzer.analyze_diff(request.workspace_path)

@app.get("/git/recent-commits/{workspace_path:path}")
async def get_recent_commits(workspace_path: str, limit: int = 20):
    """Get recent git commits"""
    commits = git_analyzer.get_recent_commits(workspace_path, limit)
    return {"workspace": workspace_path, "commits": commits}

@app.post("/git/analyze-change")
async def analyze_change_risk(request: GitChangeRiskRequest):
    """Analyze risk of a specific file change"""
    return git_analyzer.analyze_change_risk(request.workspace_path, request.file_path)

@app.post("/git/correlate")
async def correlate_error_with_git(request: GitCorrelateRequest):
    """Correlate an error with recent git changes (root cause analysis)"""
    return git_analyzer.correlate_error_with_changes(request.workspace_path, request.error_text)

@app.get("/git/branch/{workspace_path:path}")
async def get_current_branch(workspace_path: str):
    """Get current git branch"""
    branch = git_analyzer.get_current_branch(workspace_path)
    return {"workspace": workspace_path, "branch": branch}

@app.get("/git/changed-files/{workspace_path:path}")
async def get_changed_files(workspace_path: str):
    """Get list of changed files"""
    files = git_analyzer.get_changed_files(workspace_path)
    return {"workspace": workspace_path, "files": files}


# ============== Security Scanning ==============

class SecurityScanRequest(BaseModel):
    file_path: str

class SecurityWorkspaceScanRequest(BaseModel):
    workspace_path: str

@app.post("/security/scan")
async def scan_file_security(request: SecurityScanRequest):
    """Scan a single file for security issues"""
    cache_key = make_key("security_scan", request.file_path)
    cached = security_cache.get(cache_key)
    if cached is not None:
        return cached
    findings = security_scanner.scan_file(request.file_path)
    security_cache.set(cache_key, findings, ttl=120)
    return findings

@app.post("/security/scan-workspace")
async def scan_workspace_security(request: SecurityWorkspaceScanRequest):
    """Scan entire workspace for security issues"""
    cache_key = make_key("security_workspace", request.workspace_path)
    cached = security_cache.get(cache_key)
    if cached is not None:
        return cached
    result = security_scanner.scan_workspace(request.workspace_path)
    security_cache.set(cache_key, result, ttl=120)
    return result


# ============== SQL Analysis ==============

class SQLAnalyzeRequest(BaseModel):
    query: str
    workspace_path: Optional[str] = None

@app.post("/sql/analyze")
async def analyze_sql(request: SQLAnalyzeRequest):
    """Analyze SQL query for issues"""
    return sql_analyzer.analyze(request.query, request.workspace_path)

@app.post("/sql/validate")
async def validate_sql(request: SQLAnalyzeRequest):
    """Validate SQL query syntax"""
    return sql_analyzer.validate_query_syntax(request.query)


# ============== API Detection ==============

class APIDetectRequest(BaseModel):
    workspace_path: str

class APIValidateRequest(BaseModel):
    workspace_path: str
    method: str
    route: str

@app.post("/api/detect")
async def detect_api_endpoints(request: APIDetectRequest):
    """Detect API endpoints in workspace"""
    cache_key = make_key("api_detect", request.workspace_path)
    cached = response_cache.get(cache_key)
    if cached is not None:
        return cached
    result = api_detector.detect_endpoints(request.workspace_path)
    response_cache.set(cache_key, result, ttl=60)
    return result

@app.post("/api/validate")
async def validate_api_call(request: APIValidateRequest):
    """Validate if an API call matches defined endpoints"""
    return api_detector.validate_api_call(request.workspace_path, request.method, request.route)


# ============== Behavior Tracking ==============

class BehaviorTrackRequest(BaseModel):
    workspace_path: str
    event: str
    data: Dict[str, Any] = {}

@app.post("/behavior/track")
async def track_behavior(request: BehaviorTrackRequest):
    """Track a developer behavior event"""
    return behavior_tracker.track_event(request.workspace_path, request.event, request.data)

@app.get("/behavior/status/{workspace_path:path}")
async def get_behavior_status(workspace_path: str):
    """Get current behavior status"""
    return behavior_tracker.get_status(workspace_path)

@app.get("/behavior/report/{workspace_path:path}")
async def get_behavior_report(workspace_path: str):
    """Get detailed session behavior report"""
    return behavior_tracker.get_session_report(workspace_path)


# ============== Prompt Optimization ==============

class PromptOptimizeRequest(BaseModel):
    workspace_path: str
    task: str
    current_file: Optional[str] = None
    error_text: Optional[str] = None
    code_snippet: Optional[str] = None

@app.post("/prompt/optimize")
async def optimize_prompt(request: PromptOptimizeRequest):
    """Build an optimized AI prompt with full context"""
    result = prompt_optimizer.optimize(
        workspace_path=request.workspace_path,
        task=request.task,
        current_file=request.current_file,
        error_text=request.error_text,
        code_snippet=request.code_snippet,
    )
    return ContextResponse(
        prompt=result['prompt'],
        token_estimate=result['token_estimate'],
        metadata=result['metadata']
    )


# ============== Prisma / ORM Intelligence ==============

class PrismaAnalyzeRequest(BaseModel):
    workspace_path: str

class PrismaDTOValidateRequest(BaseModel):
    workspace_path: str
    dto_file: str

class PrismaIncludeCheckRequest(BaseModel):
    workspace_path: str
    file_path: str

@app.post("/prisma/analyze")
async def analyze_prisma(request: PrismaAnalyzeRequest):
    """Full Prisma schema analysis — relations, indexes, cascades, DTOs."""
    cache_key = make_key("prisma_analyze", request.workspace_path)
    cached = response_cache.get(cache_key)
    if cached is not None:
        return cached
    result = prisma_analyzer.analyze_workspace(request.workspace_path)
    response_cache.set(cache_key, result, ttl=60)
    return result

@app.post("/prisma/validate")
async def validate_prisma(request: PrismaAnalyzeRequest):
    """Validate Prisma schema for structural issues."""
    return prisma_analyzer.validate_schema(request.workspace_path)

@app.post("/prisma/schema")
async def get_prisma_schema(request: PrismaAnalyzeRequest):
    """Get parsed Prisma schema as structured JSON."""
    result = prisma_analyzer.get_schema(request.workspace_path)
    if result is None:
        raise HTTPException(status_code=404, detail="No schema.prisma found")
    return result

@app.post("/prisma/validate-dto")
async def validate_prisma_dto(request: PrismaDTOValidateRequest):
    """Validate a DTO file against Prisma models."""
    return prisma_analyzer.validate_dto(request.workspace_path, request.dto_file)

@app.post("/prisma/check-include")
async def check_prisma_include(request: PrismaIncludeCheckRequest):
    """Validate Prisma include/select usage in code file."""
    return prisma_analyzer.check_include_select(request.workspace_path, request.file_path)


# ============== API Contract Enforcement ==============

class ContractAnalyzeRequest(BaseModel):
    workspace_path: str

class ContractCheckRequest(BaseModel):
    workspace_path: str
    method: str
    path: str

@app.post("/contracts/analyze")
async def analyze_contracts(request: ContractAnalyzeRequest):
    """Full API contract analysis — endpoints, violations, auth coverage."""
    cache_key = make_key("contract_analyze", request.workspace_path)
    cached = response_cache.get(cache_key)
    if cached is not None:
        return cached
    result = contract_analyzer.analyze_workspace(request.workspace_path)
    response_cache.set(cache_key, result, ttl=60)
    return result

@app.post("/contracts/validate")
async def validate_contracts(request: ContractAnalyzeRequest):
    """Validate API contracts for discipline violations."""
    return contract_analyzer.validate_contracts(request.workspace_path)

@app.post("/contracts/check")
async def check_contract(request: ContractCheckRequest):
    """Check a specific endpoint against contracts."""
    return contract_analyzer.check_endpoint(request.workspace_path, request.method, request.path)

@app.post("/contracts/map")
async def get_contract_map(request: ContractAnalyzeRequest):
    """Get structured endpoint map."""
    return contract_analyzer.get_endpoint_map(request.workspace_path)


# ============== Change Impact Analysis ==============

class ImpactBuildRequest(BaseModel):
    workspace_path: str

class ImpactAnalyzeRequest(BaseModel):
    workspace_path: str
    changed_file: str
    old_content: str = ""
    new_content: str = ""

class ImpactMultiRequest(BaseModel):
    workspace_path: str
    files: List[str]

class ImpactFileRequest(BaseModel):
    workspace_path: str
    file_path: str

@app.post("/impact/build-graph")
async def build_impact_graph(request: ImpactBuildRequest):
    """Build dependency graph for workspace."""
    return impact_analyzer.build_graph(request.workspace_path)

@app.post("/impact/analyze")
async def analyze_impact(request: ImpactAnalyzeRequest):
    """Analyze impact of a file change."""
    return impact_analyzer.analyze_change(
        request.workspace_path, request.changed_file,
        request.old_content, request.new_content
    )

@app.post("/impact/analyze-multi")
async def analyze_multi_impact(request: ImpactMultiRequest):
    """Analyze combined impact of multiple file changes."""
    return impact_analyzer.analyze_multiple_changes(request.workspace_path, request.files)

@app.post("/impact/file-info")
async def get_file_impact_info(request: ImpactFileRequest):
    """Get dependency info for a specific file."""
    return impact_analyzer.get_file_info(request.workspace_path, request.file_path)

@app.post("/impact/dependency-map")
async def get_dependency_map(request: ImpactBuildRequest):
    """Get full dependency graph summary."""
    return impact_analyzer.get_dependency_map(request.workspace_path)


# ============== Unified Validation Pipeline ==============

class PipelineFullScanRequest(BaseModel):
    workspace_path: str

class PipelineFileChangeRequest(BaseModel):
    workspace_path: str
    file_path: str
    old_content: str = ""
    new_content: str = ""

class PipelinePreCommitRequest(BaseModel):
    workspace_path: str
    changed_files: List[str]

@app.post("/pipeline/full-scan")
async def pipeline_full_scan(request: PipelineFullScanRequest):
    """Run all enforcement checks on workspace (comprehensive)."""
    return validation_pipeline.full_scan(request.workspace_path)

@app.post("/pipeline/file-change")
async def pipeline_file_change(request: PipelineFileChangeRequest):
    """Run targeted checks when a file changes (incremental)."""
    return validation_pipeline.on_file_change(
        request.workspace_path, request.file_path,
        request.old_content, request.new_content
    )

@app.post("/pipeline/pre-commit")
async def pipeline_pre_commit(request: PipelinePreCommitRequest):
    """Pre-commit validation of changed files."""
    return validation_pipeline.validate_before_commit(
        request.workspace_path, request.changed_files
    )


# ============== Stack Detection ==============

class StackDetectRequest(BaseModel):
    workspace_path: str

@app.post("/stack/detect")
async def detect_stack(request: StackDetectRequest):
    """Detect project tech stack from config files."""
    cache_key = make_key("stack_detect", request.workspace_path)
    cached = project_cache.get(cache_key)
    if cached is not None:
        return cached
    result = stack_detector.detect(request.workspace_path)
    project_cache.set(cache_key, result, ttl=300)
    return result


# ============== Autonomous Runtime ==============

class AutonomousEventRequest(BaseModel):
    file_path: str
    workspace_path: str
    change_type: str = "saved"
    git_branch: str = ""

class AutonomousWorkspaceRequest(BaseModel):
    workspace_path: str

class AutonomousThresholdRequest(BaseModel):
    workspace_path: str
    idle_interval: int = 120         # seconds
    debounce_ms: int = 500           # milliseconds

@app.post("/autonomous/event")
async def autonomous_event(request: AutonomousEventRequest):
    """Submit a file change event to the autonomous worker."""
    event = ChangeEvent(
        file_path=request.file_path,
        change_type=request.change_type,
        workspace_path=request.workspace_path,
        git_branch=request.git_branch,
    )
    background_worker.submit_event(event)
    return {"queued": True, "file": request.file_path, "type": request.change_type}

@app.post("/autonomous/initialize")
async def autonomous_init(request: AutonomousWorkspaceRequest, bg: BackgroundTasks):
    """Initialize autonomous monitoring for a workspace (full index + graph build)."""
    result = background_worker.initialize_workspace(request.workspace_path)
    return result

@app.get("/autonomous/health/{workspace_path:path}")
async def autonomous_health(workspace_path: str):
    """Get full autonomous health report for a workspace."""
    workspace_path = _normalize_ws_path(workspace_path)
    return background_worker.get_health(workspace_path)

@app.get("/autonomous/status")
async def autonomous_status():
    """Get background worker status and stats."""
    return {
        "running": background_worker.is_running(),
        "stats": background_worker.get_stats(),
    }

@app.get("/autonomous/risk-trend/{workspace_path:path}")
async def autonomous_risk_trend(workspace_path: str, limit: int = 50):
    """Get risk score trend over time for trend graph."""
    workspace_path = _normalize_ws_path(workspace_path)
    return background_worker.get_risk_trend(workspace_path, limit)

@app.get("/autonomous/drifts/{workspace_path:path}")
async def autonomous_drifts(workspace_path: str):
    """Get unresolved structural drift events."""
    workspace_path = _normalize_ws_path(workspace_path)
    return background_worker.get_unresolved_drifts(workspace_path)

@app.get("/autonomous/circular-deps")
async def autonomous_circular_deps():
    """Get detected circular dependencies."""
    return background_worker.get_circular_deps()

@app.get("/autonomous/dead-code")
async def autonomous_dead_code():
    """Get dead code files (never imported)."""
    return background_worker.get_dead_code()

@app.post("/autonomous/configure")
async def autonomous_configure(request: AutonomousThresholdRequest):
    """Adjust autonomous worker thresholds."""
    background_worker._idle_interval = request.idle_interval
    background_worker._debounce_ms = request.debounce_ms
    return {
        "idle_interval": background_worker._idle_interval,
        "debounce_ms": background_worker._debounce_ms,
    }

@app.get("/autonomous/graph-stats")
async def autonomous_graph_stats():
    """Get dependency graph statistics."""
    try:
        return graph_engine.get_graph_stats()
    except Exception as e:
        return {"error": str(e)}

@app.get("/autonomous/entities/{workspace_path:path}")
async def autonomous_entities(workspace_path: str, entity_type: str = None):
    """Get indexed entities, optionally filtered by type."""
    workspace_path = _normalize_ws_path(workspace_path)
    try:
        with db.get_session() as session:
            return semantic_indexer.get_entities(workspace_path, entity_type=entity_type, db_session=session)
    except Exception as e:
        return {"error": str(e)}

@app.get("/autonomous/dashboard/{workspace_path:path}")
async def autonomous_dashboard(workspace_path: str):
    """
    Single endpoint for the monitoring dashboard.
    Returns all data needed for the dashboard in one call.
    """
    workspace_path = _normalize_ws_path(workspace_path)
    health = background_worker.get_health(workspace_path)
    trend = background_worker.get_risk_trend(workspace_path, 20)
    drifts = background_worker.get_unresolved_drifts(workspace_path)
    circular = background_worker.get_circular_deps()
    dead_code = background_worker.get_dead_code()

    return {
        "health": health,
        "risk_trend": trend,
        "unresolved_drifts": drifts,
        "circular_dependencies": circular,
        "dead_code_files": dead_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============== Advanced Analysis APIs ==============

# Initialize new analyzers
ast_security_scanner = ASTSecurityScanner()
dead_code_detector = DeadCodeDetector()
code_quality_analyzer = CodeQualityAnalyzer()
runtime_error_predictor = RuntimeErrorPredictor()
dependency_analyzer = DependencyAnalyzer()
copilot_style_detector = CopilotStyleDetector()


class AdvancedScanRequest(BaseModel):
    workspace_path: str
    max_files: int = 500


@app.post("/analysis/security-ast")
async def scan_security_ast(request: AdvancedScanRequest):
    """AST-based security scan with reduced false positives"""
    result = ast_security_scanner.scan_workspace(request.workspace_path, request.max_files)
    return result


@app.post("/analysis/dead-code")
async def analyze_dead_code(request: AdvancedScanRequest):
    """Detect unused imports, functions, and dead API endpoints"""
    result = dead_code_detector.analyze_workspace(request.workspace_path, request.max_files)
    return result


@app.post("/analysis/code-quality")
async def analyze_code_quality(request: AdvancedScanRequest):
    """Analyze code quality: complexity, nesting, function length, etc."""
    result = code_quality_analyzer.analyze_workspace(request.workspace_path, request.max_files)
    return result


@app.post("/analysis/runtime-errors")
async def predict_runtime_errors(request: AdvancedScanRequest):
    """Predict potential runtime errors: null access, division by zero, etc."""
    result = runtime_error_predictor.analyze_workspace(request.workspace_path, request.max_files)
    return result


@app.post("/analysis/dependencies")
async def analyze_dependencies(request: AdvancedScanRequest):
    """Analyze dependencies: vulnerabilities, circular imports, unused packages"""
    result = dependency_analyzer.analyze_workspace(request.workspace_path)
    return result


@app.post("/analysis/copilot-issues")
async def detect_copilot_issues(request: AdvancedScanRequest):
    """Detect copilot-style issues: TODOs, magic numbers, debug code, etc."""
    result = copilot_style_detector.analyze_workspace(request.workspace_path, request.max_files)
    return result


@app.post("/analysis/full")
async def run_full_analysis(request: AdvancedScanRequest):
    """Run ALL analyzers and return comprehensive results"""
    workspace = request.workspace_path
    max_files = request.max_files
    
    # Run all analyzers
    security = ast_security_scanner.scan_workspace(workspace, max_files)
    dead_code = dead_code_detector.analyze_workspace(workspace, max_files)
    quality = code_quality_analyzer.analyze_workspace(workspace, max_files)
    runtime = runtime_error_predictor.analyze_workspace(workspace, max_files)
    deps = dependency_analyzer.analyze_workspace(workspace)
    copilot = copilot_style_detector.analyze_workspace(workspace, max_files)
    
    # Combine all findings
    all_findings = []
    
    for f in security.get('findings', []):
        f['pillar'] = 'security'
        all_findings.append(f)
    
    for f in dead_code.get('findings', []):
        f['pillar'] = 'dead_code'
        all_findings.append(f)
    
    for f in quality.get('findings', []):
        f['pillar'] = 'quality'
        all_findings.append(f)
    
    for f in runtime.get('findings', []):
        f['pillar'] = 'runtime'
        all_findings.append(f)
    
    for f in deps.get('findings', []):
        f['pillar'] = 'dependencies'
        all_findings.append(f)
    
    for f in copilot.get('findings', []):
        f['pillar'] = 'copilot_style'
        all_findings.append(f)
    
    # Sort by severity
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
    all_findings.sort(key=lambda f: severity_order.get(f.get('severity', 'INFO'), 99))
    
    # Calculate summary
    summary = {
        'total_findings': len(all_findings),
        'by_severity': {
            'critical': sum(1 for f in all_findings if f.get('severity') == 'CRITICAL'),
            'high': sum(1 for f in all_findings if f.get('severity') == 'HIGH'),
            'medium': sum(1 for f in all_findings if f.get('severity') == 'MEDIUM'),
            'low': sum(1 for f in all_findings if f.get('severity') == 'LOW'),
            'info': sum(1 for f in all_findings if f.get('severity') == 'INFO'),
        },
        'by_pillar': {
            'security': security.get('total_findings', 0),
            'dead_code': dead_code.get('total_findings', 0),
            'quality': quality.get('total_findings', 0),
            'runtime': runtime.get('total_findings', 0),
            'dependencies': deps.get('total_findings', 0),
            'copilot_style': copilot.get('total_findings', 0),
        }
    }
    
    return {
        'workspace': workspace,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'summary': summary,
        'findings': all_findings[:200],  # Limit to 200 most important
        'detailed_results': {
            'security': security.get('summary', {}),
            'dead_code': dead_code.get('summary', {}),
            'quality': quality.get('summary', {}),
            'runtime': runtime.get('summary', {}),
            'dependencies': deps.get('summary', {}),
            'copilot_style': copilot.get('summary', {}),
        }
    }


# ============== Main ==============

def main():
    """Run the server"""
    uvicorn.run(
        "server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )


if __name__ == "__main__":
    main()
