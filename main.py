
"""
Post-Disaster Rescue Decision Support System (PDRDSS)
=====================================================
FastAPI backend serving real-time disaster data from public APIs.

⚠ ACADEMIC PROTOTYPE — Not a certified emergency management tool.
"""

import math
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from routes import router as api_router

app = FastAPI(title="PDRDSS", version="2.0.0")

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
@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse("static/dashboard.html")

@app.get("/login")
async def serve_login():
    return FileResponse("static/login.html")

@app.get("/history")
async def serve_history():
    return FileResponse("static/history.html")

@app.get("/analytics")
async def serve_analytics():
    return FileResponse("static/analytics.html")


if __name__ == "__main__":
    import uvicorn
    # In production/docker, we'd run: uvicorn main:app --host 0.0.0.0 --port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
