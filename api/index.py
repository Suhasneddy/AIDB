"""
Vercel Serverless Function — wraps FastAPI app for Vercel deployment.
This file is the entry point for Vercel's Python runtime.
"""

import sys
import os
import traceback

# Add backend directory to Python path so imports work
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, backend_dir)

try:
    # Import the FastAPI app
    from main import app
except Exception as e:
    # If import fails, create a minimal FastAPI app that reports the error
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
    print(f"❌ IMPORT ERROR:\n{error_msg}")

    @app.get("/{path:path}")
    @app.post("/{path:path}")
    async def error_handler(path: str = ""):
        return {
            "success": False,
            "error": "Backend failed to initialize",
            "details": error_msg,
            "python_version": sys.version,
            "path": path,
        }

# Vercel expects the ASGI app to be named 'app' or 'handler'
# FastAPI is ASGI-native, so this works directly
