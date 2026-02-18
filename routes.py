
from fastapi import APIRouter, Query, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

import services
from database import get_db
from models import User, AnalysisLog
from auth import (
    authenticate_user, 
    create_access_token, 
    get_current_active_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    timedelta
)

router = APIRouter()

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return {"username": current_user.username, "role": current_user.role}

@router.get("/api/live-feed")
async def live_feed():
    """
    Return recent earthquakes (USGS, last 24h, M2.5+) and active cyclones
    (NOAA NHC) as a unified time-sorted feed for the landing page.
    """
    return await services.get_live_feed_data()

@router.get("/api/geocode")
async def geocode(location: str = Query(..., description="Place name or 'lat,lon'")):
    """Resolve a place name to coordinates with confidence scoring."""
    result = await services.geocode_location(location)
    if not result:
        raise HTTPException(status_code=404, detail="Location not recognized. Try coordinates (lat, lon) or a larger region name.")
    return result

@router.get("/api/earthquake")
async def get_earthquake(
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float = Query(500),
    days: int = Query(30),
    min_mag: float = Query(2.5),
):
    """Fetch recent earthquakes near a location from USGS."""
    return await services.fetch_earthquakes(lat, lon, radius_km, days, min_mag)

@router.get("/api/cyclone")
async def get_cyclone(
    lat: float = Query(...),
    lon: float = Query(...),
):
    """Fetch active cyclone/hurricane data from NOAA NHC."""
    return await services.fetch_cyclones(lat, lon)

@router.get("/api/news")
async def get_news(
    query: str = Query(..., description="Search query e.g. 'earthquake Turkey'"),
    timespan: str = Query("24h"),
):
    """Fetch real-time disaster news from GDELT DOC 2.0 API."""
    return await services.fetch_news(query, timespan)

@router.get("/api/resources")
async def get_resources(
    lat: float = Query(...),
    lon: float = Query(...),
    radius_m: int = Query(15000, description="Search radius in meters"),
):
    """Fetch nearby hospitals, fire stations, police from OpenStreetMap."""
    return await services.fetch_resources(lat, lon, radius_m)

@router.get("/api/analyze")
async def analyze(
    lat: float = Query(...),
    lon: float = Query(...),
    disaster_type: str = Query(..., description="earthquake or cyclone"),
    location_name: str = Query("Unknown Location"),
    db: AsyncSession = Depends(get_db)
):
    """
    Aggregate all data sources and produce AI-assisted decision support.
    All outputs are derived from real data — nothing is fabricated.
    Logs each analysis to the database for history tracking.
    """
    result = await services.analyze_disaster_impact(lat, lon, disaster_type, location_name)
    
    # Log to DB
    new_log = AnalysisLog(
        location_name=location_name,
        disaster_type=disaster_type,
        priority_score=result["priority_score"],
        severity=result["severity"],
        timestamp=datetime.now(timezone.utc),
        user_id=None
    )
    db.add(new_log)
    await db.commit()
    
    return result

@router.get("/api/history")
async def get_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch past analysis logs for the current user."""
    # If admin, fetch all? For now, fetch all for user.
    result = await db.execute(select(AnalysisLog).where(AnalysisLog.user_id == current_user.id).order_by(AnalysisLog.timestamp.desc()))
    logs = result.scalars().all()
    return logs

@router.get("/api/stats")
async def get_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Aggregate stats for the analytics dashboard."""
    # Total Analysis Count
    result_total = await db.execute(select(func.count(AnalysisLog.id)).where(AnalysisLog.user_id == current_user.id))
    total_count = result_total.scalar() or 0
    
    # High Priority Count
    result_high = await db.execute(select(func.count(AnalysisLog.id)).where(AnalysisLog.user_id == current_user.id, AnalysisLog.priority_score >= 60))
    high_count = result_high.scalar() or 0
    
    # Severity Distribution
    result_severity = await db.execute(select(AnalysisLog.severity, func.count(AnalysisLog.id)).where(AnalysisLog.user_id == current_user.id).group_by(AnalysisLog.severity))
    severity_dist = {row[0]: row[1] for row in result_severity.all()}
    
    return {
        "total_analyses": total_count,
        "high_priority": high_count,
        "severity_distribution": severity_dist
    }
