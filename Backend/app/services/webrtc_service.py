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
from .network_quality_service import network_quality_service
from .compression_service import CompressionService

logger = logging.getLogger(__name__)

class WebRTCStreamingService:
    """Service for managing WebRTC live streaming sessions."""
    
    def __init__(self):
        self.signaling_server_url = "http://localhost:3001"
        self.active_streams: Dict[int, Dict] = {}  # class_id -> stream_data
        self.peer_connections: Dict[int, Dict] = {}  # user_id -> connection_data
        self.quality_monitoring: Dict[int, Dict] = {}  # user_id -> monitoring_data
        self.adaptive_profiles: Dict[int, str] = {}  # user_id -> current_profile
    
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
            
            # Store adaptive profile
            self.adaptive_profiles[user_id] = bandwidth_profile
            
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

    async def detect_and_optimize_network_quality(
        self, 
        class_id: int, 
        user_id: int
    ) -> Dict[str, Any]:
        """Detect network quality and automatically optimize streaming parameters."""
        try:
            logger.info(f"Starting network quality detection for user {user_id}")
            
            # Perform comprehensive network quality detection
            quality_result = await network_quality_service.detect_network_quality(user_id)
            
            # Update user's profile based on detected quality
            recommended_profile = quality_result["recommended_profile"]
            await self.update_bandwidth_profile(class_id, user_id, recommended_profile)
            
            # Start continuous monitoring
            monitoring_task = asyncio.create_task(
                self._monitor_user_quality(user_id, class_id)
            )
            self.quality_monitoring[user_id] = {
                "task": monitoring_task,
                "started_at": datetime.now(timezone.utc),
                "quality_score": quality_result["quality_score"]
            }
            
            return {
                "success": True,
                "quality_detection": quality_result,
                "optimization_applied": True,
                "monitoring_started": True
            }
            
        except Exception as e:
            logger.error(f"Failed to detect and optimize network quality: {str(e)}")
            raise

    async def _monitor_user_quality(self, user_id: int, class_id: int):
        """Continuously monitor user's network quality and adapt streaming."""
        try:
            while user_id in self.quality_monitoring:
                # Quick quality check
                quality_result = await network_quality_service.monitor_connection_quality(
                    user_id, duration=30
                )
                
                # Check if profile needs adjustment
                current_profile = self.adaptive_profiles.get(user_id, "fair")
                new_profile = quality_result.get("final_profile", current_profile)
                
                if new_profile != current_profile:
                    logger.info(f"Adapting profile for user {user_id}: {current_profile} -> {new_profile}")
                    await self.update_bandwidth_profile(class_id, user_id, new_profile)
                    
                    # Notify user about quality change
                    await self._notify_signaling_server("quality-adaptation", {
                        "class_id": class_id,
                        "user_id": user_id,
                        "old_profile": current_profile,
                        "new_profile": new_profile,
                        "reason": "network_quality_change"
                    })
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except Exception as e:
            logger.error(f"Quality monitoring failed for user {user_id}: {str(e)}")
        finally:
            # Clean up monitoring
            if user_id in self.quality_monitoring:
                del self.quality_monitoring[user_id]

    async def get_optimized_streaming_config(
        self, 
        user_id: int, 
        content_type: str = "audio"
    ) -> Dict[str, Any]:
        """Get optimized streaming configuration for a user."""
        try:
            profile = self.adaptive_profiles.get(user_id, "fair")
            profile_config = network_quality_service.get_adaptive_profile_config(profile)
            
            # Get compression settings
            compression_profile = CompressionService.BANDWIDTH_PROFILES.get(profile, {})
            
            # Combine configurations
            streaming_config = {
                "profile": profile,
                "audio": {
                    "bitrate": profile_config["audio_bitrate"],
                    "sample_rate": compression_profile.get("audio_sample_rate", 44100),
                    "channels": compression_profile.get("audio_channels", 2),
                    "codec": compression_profile.get("audio_codec", "opus")
                },
                "video": {
                    "bitrate": profile_config["video_bitrate"],
                    "fps": profile_config["video_fps"],
                    "resolution": profile_config["video_resolution"],
                    "codec": "h264"
                },
                "network": {
                    "buffer_size": profile_config["buffer_size"],
                    "chunk_size": profile_config["chunk_size"],
                    "retry_attempts": profile_config["retry_attempts"],
                    "timeout": profile_config["timeout"]
                },
                "optimization": {
                    "adaptive_bitrate": True,
                    "error_recovery": True,
                    "buffering_strategy": "aggressive" if profile in ["emergency", "critical"] else "balanced"
                }
            }
            
            return streaming_config
            
        except Exception as e:
            logger.error(f"Failed to get optimized streaming config: {str(e)}")
            # Return emergency fallback
            return {
                "profile": "emergency",
                "audio": {"bitrate": "8k", "sample_rate": 16000, "channels": 1, "codec": "opus"},
                "video": {"bitrate": "25k", "fps": 3, "resolution": "240x180", "codec": "h264"},
                "network": {"buffer_size": 512, "chunk_size": 256, "retry_attempts": 5, "timeout": 30},
                "optimization": {"adaptive_bitrate": True, "error_recovery": True, "buffering_strategy": "aggressive"}
            }
    
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
