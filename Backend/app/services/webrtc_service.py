"""
WebRTC Streaming Service for GramOthi
Handles WebRTC peer connections, audio streaming, and slide synchronization
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import aiohttp
from sqlalchemy.orm import Session
from ..models import User, Class, LiveSession, Slide
from ..database import get_db

logger = logging.getLogger(__name__)

class WebRTCStreamingService:
    """Service for managing WebRTC live streaming sessions."""
    
    def __init__(self):
        self.signaling_server_url = "http://localhost:3001"
        self.active_streams: Dict[int, Dict] = {}  # class_id -> stream_data
        self.peer_connections: Dict[int, Dict] = {}  # user_id -> connection_data
    
    async def start_live_stream(
        self, 
        class_id: int, 
        teacher_id: int, 
        db: Session
    ) -> Dict[str, Any]:
        """Start a live streaming session for a class."""
        try:
            # Check if there's already an active stream
            if class_id in self.active_streams:
                raise ValueError(f"Live stream already active for class {class_id}")
            
            # Get class information
            class_info = db.query(Class).filter(Class.id == class_id).first()
            if not class_info:
                raise ValueError(f"Class {class_id} not found")
            
            # Get teacher information
            teacher = db.query(User).filter(User.id == teacher_id).first()
            if not teacher or teacher.role != "teacher":
                raise ValueError("Only teachers can start live streams")
            
            # Create stream session
            stream_data = {
                "class_id": class_id,
                "teacher_id": teacher_id,
                "started_at": datetime.now(timezone.utc),
                "participants": [],
                "current_slide": None,
                "audio_enabled": True,
                "slide_sync_enabled": True
            }
            
            self.active_streams[class_id] = stream_data
            
            # Notify signaling server
            await self._notify_signaling_server("stream-started", {
                "class_id": class_id,
                "teacher_id": teacher_id,
                "teacher_name": teacher.name
            })
            
            logger.info(f"Live stream started for class {class_id} by teacher {teacher.name}")
            
            return {
                "success": True,
                "stream_id": f"stream_{class_id}_{teacher_id}",
                "class_id": class_id,
                "teacher_id": teacher_id,
                "started_at": stream_data["started_at"].isoformat(),
                "signaling_server_url": self.signaling_server_url
            }
            
        except Exception as e:
            logger.error(f"Failed to start live stream: {str(e)}")
            raise
    
    async def stop_live_stream(self, class_id: int, teacher_id: int) -> Dict[str, Any]:
        """Stop a live streaming session."""
        try:
            if class_id not in self.active_streams:
                raise ValueError(f"No active stream found for class {class_id}")
            
            stream_data = self.active_streams[class_id]
            
            # Verify teacher permission
            if stream_data["teacher_id"] != teacher_id:
                raise ValueError("Only the stream owner can stop the stream")
            
            # Notify all participants
            await self._notify_signaling_server("stream-stopped", {
                "class_id": class_id,
                "teacher_id": teacher_id
            })
            
            # Remove from active streams
            del self.active_streams[class_id]
            
            logger.info(f"Live stream stopped for class {class_id}")
            
            return {
                "success": True,
                "message": "Live stream stopped successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to stop live stream: {str(e)}")
            raise
    
    async def join_stream(
        self, 
        class_id: int, 
        user_id: int, 
        user_role: str
    ) -> Dict[str, Any]:
        """Join a live streaming session."""
        try:
            if class_id not in self.active_streams:
                raise ValueError(f"No active stream found for class {class_id}")
            
            stream_data = self.active_streams[class_id]
            
            # Add participant
            participant = {
                "user_id": user_id,
                "user_role": user_role,
                "joined_at": datetime.now(timezone.utc),
                "audio_enabled": True,
                "bandwidth_profile": "medium"  # Default, will be updated
            }
            
            stream_data["participants"].append(participant)
            
            # Notify signaling server
            await self._notify_signaling_server("user-joined-stream", {
                "class_id": class_id,
                "user_id": user_id,
                "user_role": user_role
            })
            
            return {
                "success": True,
                "stream_info": {
                    "class_id": class_id,
                    "teacher_id": stream_data["teacher_id"],
                    "participants_count": len(stream_data["participants"]),
                    "current_slide": stream_data["current_slide"],
                    "audio_enabled": stream_data["audio_enabled"]
                },
                "ice_servers": await self._get_ice_servers()
            }
            
        except Exception as e:
            logger.error(f"Failed to join stream: {str(e)}")
            raise
    
    async def leave_stream(self, class_id: int, user_id: int) -> Dict[str, Any]:
        """Leave a live streaming session."""
        try:
            if class_id not in self.active_streams:
                return {"success": True, "message": "Stream not found"}
            
            stream_data = self.active_streams[class_id]
            
            # Remove participant
            stream_data["participants"] = [
                p for p in stream_data["participants"] 
                if p["user_id"] != user_id
            ]
            
            # Notify signaling server
            await self._notify_signaling_server("user-left-stream", {
                "class_id": class_id,
                "user_id": user_id
            })
            
            return {
                "success": True,
                "message": "Left stream successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to leave stream: {str(e)}")
            raise
    
    async def sync_slide(
        self, 
        class_id: int, 
        slide_id: int, 
        action: str,
        teacher_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Synchronize slide changes across all participants."""
        try:
            if class_id not in self.active_streams:
                raise ValueError(f"No active stream found for class {class_id}")
            
            stream_data = self.active_streams[class_id]
            
            # Verify teacher permission
            if stream_data["teacher_id"] != teacher_id:
                raise ValueError("Only the stream owner can control slides")
            
            # Get slide information
            slide = db.query(Slide).filter(Slide.id == slide_id).first()
            if not slide:
                raise ValueError(f"Slide {slide_id} not found")
            
            # Update current slide
            stream_data["current_slide"] = {
                "slide_id": slide_id,
                "file_url": slide.file_url,
                "order_no": slide.order_no,
                "action": action,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Notify signaling server for slide sync
            await self._notify_signaling_server("slide-sync", {
                "class_id": class_id,
                "slide_id": slide_id,
                "action": action,  # 'next', 'previous', 'goto'
                "slide_data": {
                    "file_url": slide.file_url,
                    "order_no": slide.order_no
                }
            })
            
            return {
                "success": True,
                "slide_synced": {
                    "slide_id": slide_id,
                    "action": action,
                    "timestamp": stream_data["current_slide"]["timestamp"]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to sync slide: {str(e)}")
            raise
    
    async def update_bandwidth_profile(
        self, 
        class_id: int, 
        user_id: int, 
        bandwidth_profile: str
    ) -> Dict[str, Any]:
        """Update user's bandwidth profile for optimization."""
        try:
            if class_id not in self.active_streams:
                raise ValueError(f"No active stream found for class {class_id}")
            
            stream_data = self.active_streams[class_id]
            
            # Update participant's bandwidth profile
            for participant in stream_data["participants"]:
                if participant["user_id"] == user_id:
                    participant["bandwidth_profile"] = bandwidth_profile
                    break
            
            # Notify signaling server
            await self._notify_signaling_server("bandwidth-update", {
                "class_id": class_id,
                "user_id": user_id,
                "bandwidth_profile": bandwidth_profile
            })
            
            return {
                "success": True,
                "bandwidth_profile": bandwidth_profile
            }
            
        except Exception as e:
            logger.error(f"Failed to update bandwidth profile: {str(e)}")
            raise
    
    async def get_stream_status(self, class_id: int) -> Dict[str, Any]:
        """Get current stream status."""
        if class_id not in self.active_streams:
            return {"active": False}
        
        stream_data = self.active_streams[class_id]
        
        return {
            "active": True,
            "class_id": class_id,
            "teacher_id": stream_data["teacher_id"],
            "started_at": stream_data["started_at"].isoformat(),
            "participants_count": len(stream_data["participants"]),
            "current_slide": stream_data["current_slide"],
            "audio_enabled": stream_data["audio_enabled"],
            "slide_sync_enabled": stream_data["slide_sync_enabled"]
        }
    
    async def _notify_signaling_server(self, event: str, data: Dict[str, Any]):
        """Send notification to signaling server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.signaling_server_url}/api/events",
                    json={"event": event, "data": data}
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to notify signaling server: {response.status}")
        except Exception as e:
            logger.error(f"Error notifying signaling server: {str(e)}")
    
    async def _get_ice_servers(self) -> List[Dict[str, Any]]:
        """Get ICE servers configuration."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.signaling_server_url}/config") as response:
                    if response.status == 200:
                        config = await response.json()
                        return config.get("iceServers", [])
        except Exception as e:
            logger.error(f"Error getting ICE servers: {str(e)}")
        
        # Fallback ICE servers
        return [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"}
        ]

# Global instance
webrtc_service = WebRTCStreamingService()
