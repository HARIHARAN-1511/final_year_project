
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")  # "admin" or "user"
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class DisasterCache(Base):
    __tablename__ = "disaster_cache"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, index=True) # e.g. "us6000jllz"
    type = Column(String) # "earthquake" or "cyclone"
    lat = Column(Float)
    lon = Column(Float)
    data_json = Column(JSON) # Store full raw API response
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))

class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String)
    disaster_type = Column(String)
    priority_score = Column(Float)
    severity = Column(String)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationship to user if logged in
    user = relationship("User")

class ResourceCache(Base):
    __tablename__ = "resource_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    lat = Column(Float)
    lon = Column(Float)
    radius_m = Column(Integer)
    data_json = Column(JSON)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
