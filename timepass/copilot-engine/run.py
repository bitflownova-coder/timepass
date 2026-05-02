#!/usr/bin/env python3
"""
Quick start script for Copilot Engine
"""
import sys
import os

# Ensure we're in the correct directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║                     COPILOT ENGINE                           ║
║           Local Development Intelligence Layer               ║
╠══════════════════════════════════════════════════════════════╣
║  Server:    http://127.0.0.1:7779                           ║
║  API Docs:  http://127.0.0.1:7779/docs                      ║
║  Health:    http://127.0.0.1:7779/health                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    import uvicorn
    from config import settings
    
    uvicorn.run(
        "server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
