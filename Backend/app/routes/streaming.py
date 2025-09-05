"""
WebRTC Streaming Routes for GramOthi
Handles live streaming, slide synchronization, and real-time communication
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import get_db
from ..models import User, Class, LiveSession, Slide
from ..schemas import (
    LiveSessionCreate, LiveSessionResponse, SlideResponse
)
from ..routes.auth import get_current_user, get_current_teacher
from ..services.webrtc_service import webrtc_service
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/streaming", tags=["webrtc-streaming"])

# WebSocket connection manager for streaming
class StreamingConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}  # class_id -> connections
    
    async def connect(self, websocket: WebSocket, class_id: int, user_id: int):
        await websocket.accept()
        if class_id not in self.active_connections:
            self.active_connections[class_id] = []
        
        self.active_connections[class_id].append({
            "websocket": websocket,
            "user_id": user_id,
            "connected_at": datetime.now()
        })
    
    def disconnect(self, websocket: WebSocket, class_id: int):
        if class_id in self.active_connections:
            self.active_connections[class_id] = [
                conn for conn in self.active_connections[class_id]
                if conn["websocket"] != websocket
            ]
    
    async def broadcast_to_class(self, message: Dict[str, Any], class_id: int, exclude_user_id: int = None):
        if class_id in self.active_connections:
            for connection in self.active_connections[class_id]:
                if connection["user_id"] != exclude_user_id:
                    try:
                        await connection["websocket"].send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(f"Error broadcasting message: {e}")

streaming_manager = StreamingConnectionManager()

# Live Streaming Management
@router.post("/start", response_model=Dict[str, Any])
async def start_live_stream(
    class_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Start a live streaming session for a class."""
    try:
        # Verify class exists and user is the teacher
        db_class = db.query(Class).filter(Class.id == class_id).first()
        if not db_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        
        if db_class.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the class teacher can start live streams"
            )
        
        # Start WebRTC stream
        stream_result = await webrtc_service.start_live_stream(
            class_id=class_id,
            teacher_id=current_user.id,
            db=db
        )
        
        return stream_result
        
    except Exception as e:
        logger.error(f"Failed to start live stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start live stream: {str(e)}"
        )

@router.post("/stop")
async def stop_live_stream(
    class_id: int,
    current_user: User = Depends(get_current_teacher)
):
    """Stop a live streaming session."""
    try:
        result = await webrtc_service.stop_live_stream(
            class_id=class_id,
            teacher_id=current_user.id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to stop live stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop live stream: {str(e)}"
        )

@router.post("/join")
async def join_live_stream(
    class_id: int,
    current_user: User = Depends(get_current_user)
):
    """Join a live streaming session."""
    try:
        result = await webrtc_service.join_stream(
            class_id=class_id,
            user_id=current_user.id,
            user_role=current_user.role
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to join live stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to join live stream: {str(e)}"
        )

@router.post("/leave")
async def leave_live_stream(
    class_id: int,
    current_user: User = Depends(get_current_user)
):
    """Leave a live streaming session."""
    try:
        result = await webrtc_service.leave_stream(
            class_id=class_id,
            user_id=current_user.id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to leave live stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to leave live stream: {str(e)}"
        )

# Slide Synchronization
@router.post("/sync-slide")
async def sync_slide(
    class_id: int,
    slide_id: int,
    action: str,  # 'next', 'previous', 'goto'
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Synchronize slide changes across all participants."""
    try:
        # Verify class exists and user is the teacher
        db_class = db.query(Class).filter(Class.id == class_id).first()
        if not db_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        
        if db_class.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the class teacher can control slides"
            )
        
        # Sync slide
        result = await webrtc_service.sync_slide(
            class_id=class_id,
            slide_id=slide_id,
            action=action,
            teacher_id=current_user.id,
            db=db
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to sync slide: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync slide: {str(e)}"
        )

@router.get("/slides/{class_id}", response_model=List[SlideResponse])
async def get_class_slides(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all slides for a class."""
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Get slides
    slides = db.query(Slide).filter(Slide.class_id == class_id).order_by(Slide.order_no).all()
    
    return slides

# Bandwidth Management
@router.post("/bandwidth-profile")
async def update_bandwidth_profile(
    class_id: int,
    bandwidth_profile: str,  # 'ultra_low', 'low', 'medium', 'high'
    current_user: User = Depends(get_current_user)
):
    """Update user's bandwidth profile for optimization."""
    try:
        valid_profiles = ['ultra_low', 'low', 'medium', 'high']
        if bandwidth_profile not in valid_profiles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid bandwidth profile. Must be one of: {valid_profiles}"
            )
        
        result = await webrtc_service.update_bandwidth_profile(
            class_id=class_id,
            user_id=current_user.id,
            bandwidth_profile=bandwidth_profile
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to update bandwidth profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update bandwidth profile: {str(e)}"
        )

# Stream Status
@router.get("/status/{class_id}")
async def get_stream_status(class_id: int):
    """Get current stream status."""
    try:
        status = await webrtc_service.get_stream_status(class_id)
        return status
        
    except Exception as e:
        logger.error(f"Failed to get stream status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stream status: {str(e)}"
        )

# WebSocket endpoint for real-time streaming communication
@router.websocket("/ws/{class_id}")
async def streaming_websocket_endpoint(
    websocket: WebSocket,
    class_id: int,
    token: str
):
    """WebSocket endpoint for real-time streaming communication."""
    # In a real implementation, you would validate the token here
    # For now, we'll accept any connection
    
    try:
        # Connect to streaming manager
        await streaming_manager.connect(websocket, class_id, user_id=0)  # user_id would come from token
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            message_type = message.get("type")
            
            if message_type == "slide-sync":
                # Broadcast slide sync to all participants
                await streaming_manager.broadcast_to_class({
                    "type": "slide-sync",
                    "data": message.get("data")
                }, class_id)
            
            elif message_type == "audio-control":
                # Broadcast audio control to all participants
                await streaming_manager.broadcast_to_class({
                    "type": "audio-control",
                    "data": message.get("data")
                }, class_id)
            
            elif message_type == "bandwidth-report":
                # Handle bandwidth reporting
                await streaming_manager.broadcast_to_class({
                    "type": "bandwidth-report",
                    "data": message.get("data")
                }, class_id)
            
            else:
                # Broadcast general message
                await streaming_manager.broadcast_to_class(message, class_id)
            
    except WebSocketDisconnect:
        streaming_manager.disconnect(websocket, class_id)
        logger.info(f"User disconnected from streaming session for class {class_id}")

# ICE Servers Configuration
@router.get("/ice-servers")
async def get_ice_servers():
    """Get ICE servers configuration for WebRTC."""
    try:
        ice_servers = await webrtc_service._get_ice_servers()
        return {
            "iceServers": ice_servers
        }
        
    except Exception as e:
        logger.error(f"Failed to get ICE servers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ICE servers: {str(e)}"
        )
