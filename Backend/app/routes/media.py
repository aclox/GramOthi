"""
Media serving routes with bandwidth-aware compression
Optimized for low-bandwidth rural connectivity
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Slide, Recording
from ..routes.auth import get_current_user
from ..services.compression_service import CompressionService, BandwidthDetector
import os
import mimetypes
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media"])

# Media serving settings
UPLOAD_DIR = "uploads"
CHUNK_SIZE = 8192  # 8KB chunks for low-bandwidth delivery

@router.get("/slides/{slide_id}")
async def serve_slide(
    slide_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Serve slide with bandwidth-aware compression."""
    # Get slide from database
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slide not found"
        )
    
    # Check if user has access to the class
    if current_user.role == "student":
        # For students, check if they have access to the class
        # This could be enhanced with enrollment logic
        pass
    
    # Get file path
    file_path = os.path.join(UPLOAD_DIR, slide.file_url.lstrip("/"))
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Detect bandwidth profile
    user_agent = request.headers.get("user-agent", "")
    connection_type = request.headers.get("x-connection-type", "")
    bandwidth_profile = BandwidthDetector.detect_bandwidth_profile(user_agent, connection_type)
    
    # Check if we need to create a compressed version
    compressed_path = get_compressed_file_path(file_path, bandwidth_profile)
    
    if not os.path.exists(compressed_path):
        # Create compressed version
        success, compression_info = CompressionService.compress_file(
            file_path, compressed_path, bandwidth_profile
        )
        
        if not success:
            # If compression fails, serve original file
            compressed_path = file_path
            logger.warning(f"Compression failed for {file_path}, serving original")
        else:
            logger.info(f"Created compressed version: {compression_info}")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(compressed_path)
    if not content_type:
        content_type = "application/octet-stream"
    
    # Serve file with appropriate headers for low-bandwidth
    return FileResponse(
        compressed_path,
        media_type=content_type,
        filename=os.path.basename(compressed_path),
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "X-Bandwidth-Profile": bandwidth_profile,
            "X-Compression-Applied": "true" if compressed_path != file_path else "false"
        }
    )

@router.get("/recordings/{recording_id}/audio")
async def serve_audio_recording(
    recording_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Serve audio recording with bandwidth-aware compression (audio-first approach)."""
    # Get recording from database
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Get file path
    file_path = os.path.join(UPLOAD_DIR, recording.audio_url.lstrip("/"))
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    # Detect bandwidth profile
    user_agent = request.headers.get("user-agent", "")
    connection_type = request.headers.get("x-connection-type", "")
    bandwidth_profile = BandwidthDetector.detect_bandwidth_profile(user_agent, connection_type)
    
    # For audio, prioritize compression for low-bandwidth scenarios
    compressed_path = get_compressed_file_path(file_path, bandwidth_profile)
    
    if not os.path.exists(compressed_path):
        # Create compressed audio version
        success, compression_info = CompressionService.compress_file(
            file_path, compressed_path, bandwidth_profile
        )
        
        if not success:
            compressed_path = file_path
            logger.warning(f"Audio compression failed for {file_path}, serving original")
        else:
            logger.info(f"Created compressed audio: {compression_info}")
    
    # Serve audio with streaming for better low-bandwidth experience
    return FileResponse(
        compressed_path,
        media_type="audio/mpeg",
        filename=os.path.basename(compressed_path),
        headers={
            "Cache-Control": "public, max-age=7200",  # Cache audio for 2 hours
            "X-Bandwidth-Profile": bandwidth_profile,
            "X-Audio-Optimized": "true",
            "Accept-Ranges": "bytes"  # Support range requests for streaming
        }
    )

@router.get("/recordings/{recording_id}/bundle")
async def serve_bundle_recording(
    recording_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Serve bundle recording (slides + audio) with compression."""
    # Get recording from database
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    if not recording.bundle_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bundle recording not available"
        )
    
    # Get file path
    file_path = os.path.join(UPLOAD_DIR, recording.bundle_url.lstrip("/"))
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bundle file not found"
        )
    
    # Detect bandwidth profile
    user_agent = request.headers.get("user-agent", "")
    connection_type = request.headers.get("x-connection-type", "")
    bandwidth_profile = BandwidthDetector.detect_bandwidth_profile(user_agent, connection_type)
    
    # Create compressed version if needed
    compressed_path = get_compressed_file_path(file_path, bandwidth_profile)
    
    if not os.path.exists(compressed_path):
        success, compression_info = CompressionService.compress_file(
            file_path, compressed_path, bandwidth_profile
        )
        
        if not success:
            compressed_path = file_path
            logger.warning(f"Bundle compression failed for {file_path}, serving original")
        else:
            logger.info(f"Created compressed bundle: {compression_info}")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(compressed_path)
    if not content_type:
        content_type = "application/octet-stream"
    
    return FileResponse(
        compressed_path,
        media_type=content_type,
        filename=os.path.basename(compressed_path),
        headers={
            "Cache-Control": "public, max-age=3600",
            "X-Bandwidth-Profile": bandwidth_profile,
            "X-Bundle-Optimized": "true"
        }
    )

@router.get("/bandwidth-info")
async def get_bandwidth_info(request: Request):
    """Get bandwidth detection and compression recommendations."""
    user_agent = request.headers.get("user-agent", "")
    connection_type = request.headers.get("x-connection-type", "")
    
    bandwidth_profile = BandwidthDetector.detect_bandwidth_profile(user_agent, connection_type)
    recommendations = BandwidthDetector.get_compression_recommendations(bandwidth_profile)
    
    return {
        "detected_profile": bandwidth_profile,
        "user_agent": user_agent,
        "connection_type": connection_type,
        "recommendations": recommendations,
        "compression_profiles": CompressionService.BANDWIDTH_PROFILES
    }

@router.get("/stream/{file_path:path}")
async def stream_file(
    file_path: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Stream file in chunks for low-bandwidth scenarios."""
    full_path = os.path.join(UPLOAD_DIR, file_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Detect bandwidth profile
    user_agent = request.headers.get("user-agent", "")
    connection_type = request.headers.get("x-connection-type", "")
    bandwidth_profile = BandwidthDetector.detect_bandwidth_profile(user_agent, connection_type)
    
    # Adjust chunk size based on bandwidth
    chunk_size = get_chunk_size_for_bandwidth(bandwidth_profile)
    
    def generate_chunks():
        with open(full_path, "rb") as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(full_path)
    if not content_type:
        content_type = "application/octet-stream"
    
    return StreamingResponse(
        generate_chunks(),
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=3600",
            "X-Bandwidth-Profile": bandwidth_profile,
            "X-Chunk-Size": str(chunk_size),
            "Accept-Ranges": "bytes"
        }
    )

def get_compressed_file_path(original_path: str, bandwidth_profile: str) -> str:
    """Get path for compressed file based on bandwidth profile."""
    path_obj = Path(original_path)
    compressed_filename = f"{path_obj.stem}_{bandwidth_profile}{path_obj.suffix}"
    return str(path_obj.parent / compressed_filename)

def get_chunk_size_for_bandwidth(bandwidth_profile: str) -> int:
    """Get appropriate chunk size for bandwidth profile."""
    chunk_sizes = {
        "ultra_low": 4096,   # 4KB chunks
        "low": 8192,         # 8KB chunks
        "medium": 16384,     # 16KB chunks
        "high": 32768        # 32KB chunks
    }
    return chunk_sizes.get(bandwidth_profile, 8192)
