
"""
Post-Disaster Rescue Decision Support System (PDRDSS)
=====================================================
FastAPI backend serving real-time disaster data from public APIs.

⚠ ACADEMIC PROTOTYPE — Not a certified emergency management tool.
"""

# Load .env file first so GROK_API_KEY etc. are available to config.py
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; fall back to system env vars

import math
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from routes import router as api_router
from database import engine, Base
import models  # Ensure all models are registered with Base

app = FastAPI(title="PDRDSS", version="2.0.0")

# ---------------------------------------------------------------------------
# Create DB tables on startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Allow CORS for development convenience (though serving static files from same origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
app.include_router(api_router)

# ---------------------------------------------------------------------------
# Frontend Routes
# ---------------------------------------------------------------------------

# Login page (entry point)
@app.get("/")
async def serve_login():
    return FileResponse("static/login.html")

# Disaster type selector
@app.get("/select")
async def serve_select():
    return FileResponse("static/select.html")

# Earthquake path
@app.get("/earthquake")
async def serve_earthquake():
    return FileResponse("static/earthquake.html")

@app.get("/earthquake/dashboard")
async def serve_earthquake_dashboard():
    return FileResponse("static/dashboard.html")

# Cyclone path
@app.get("/cyclone")
async def serve_cyclone():
    return FileResponse("static/cyclone.html")

@app.get("/cyclone/dashboard")
async def serve_cyclone_dashboard():
    return FileResponse("static/dashboard.html")

# Analysis history
@app.get("/history")
async def serve_history():
    return FileResponse("static/history.html")

# Analytics
@app.get("/analytics")
async def serve_analytics():
    return FileResponse("static/analytics.html")


if __name__ == "__main__":
    import uvicorn
    # In production/docker, we'd run: uvicorn main:app --host 0.0.0.0 --port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
