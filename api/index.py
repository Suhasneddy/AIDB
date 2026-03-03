"""
Vercel Serverless Function — wraps FastAPI app for Vercel deployment.
This file is the entry point for Vercel's Python runtime.
"""

import sys
import os

# Add backend directory to Python path so imports work
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, backend_dir)

# Import the FastAPI app
from main import app

# Vercel expects the ASGI app to be named 'app' or 'handler'
# FastAPI is ASGI-native, so this works directly
