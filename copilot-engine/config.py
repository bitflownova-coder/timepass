"""
Configuration for Copilot Engine
"""
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from pathlib import Path
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = ConfigDict(env_prefix="COPILOT_ENGINE_", env_file=".env")
    
    # Server
    host: str = "127.0.0.1"
    port: int = 7779
    debug: bool = False  # Set to True to see SQL queries in logs
    
    # Paths
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".copilot-engine")
    db_path: Optional[Path] = None
    
    # Workspace
    watched_extensions: List[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx", 
        ".java", ".go", ".rs", ".cpp", ".c",
        ".json", ".yaml", ".yml", ".toml",
        ".sql", ".md", ".env"
    ]
    ignored_dirs: List[str] = [
        "node_modules", "__pycache__", ".git", ".venv",
        "venv", "env", "dist", "build", ".next",
        "target", "bin", "obj", ".idea", ".vscode"
    ]
    
    # Error Parser
    max_context_lines: int = 10
    max_related_files: int = 5
    
    # Context Builder
    max_prompt_tokens: int = 4000
    include_imports: bool = True
    include_schema: bool = True
    
    # Memory Engine
    max_stored_fixes: int = 1000
    similarity_threshold: float = 0.75
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # Set default DB path
        if self.db_path is None:
            self.db_path = self.data_dir / "engine.db"


settings = Settings()
