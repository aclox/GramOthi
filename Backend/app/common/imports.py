"""
Common imports for GramOthi backend
Consolidates all frequently used imports to eliminate duplication
"""

# Standard library imports
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Third-party imports
import requests
from PIL import Image
import ffmpeg

# SQLAlchemy imports
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Boolean, Text, Float, and_, or_, func
from sqlalchemy.orm import Session, sessionmaker, declarative_base

# FastAPI imports
from fastapi import (
    APIRouter, Depends, HTTPException, status, 
    Request, Response, UploadFile, File, WebSocket, WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Celery imports
from celery import Celery

# Common logger setup
logger = logging.getLogger(__name__)

# Common database and auth imports
from ..database import get_db
from ..routes.auth import get_current_user, get_current_teacher

# Common constants
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".jpg", ".jpeg", ".png", ".mp3", ".wav", ".m4a"}

# Common utility functions
def ensure_upload_dir():
    """Ensure upload directory exists."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def is_valid_file_extension(filename: str) -> bool:
    """Check if file has valid extension."""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

# Export commonly used imports
__all__ = [
    # Standard library
    "os", "json", "logging", "datetime", "timezone", "timedelta",
    "List", "Dict", "Any", "Optional", "Tuple", "Path",
    
    # Third-party
    "requests", "Image", "ffmpeg",
    
    # SQLAlchemy
    "Column", "Integer", "String", "ForeignKey", "DateTime", "JSON", 
    "Boolean", "Text", "Float", "and_", "or_", "func",
    "Session", "sessionmaker", "declarative_base",
    
    # FastAPI
    "APIRouter", "Depends", "HTTPException", "status", "Request", 
    "Response", "UploadFile", "File", "WebSocket", "WebSocketDisconnect",
    "CORSMiddleware", "StaticFiles", "FileResponse",
    
    # Celery
    "Celery",
    
    # Common
    "logger", "get_db", "get_current_user", "get_current_teacher",
    "UPLOAD_DIR", "ALLOWED_EXTENSIONS", "ensure_upload_dir", "is_valid_file_extension"
]
