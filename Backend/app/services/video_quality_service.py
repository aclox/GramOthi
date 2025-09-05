"""
Video Quality Management Service for GramOthi
Handles manual video quality adjustment and real-time quality switching
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from ..services.compression_service import CompressionService

logger = logging.getLogger(__name__)

class VideoQualityService:
    """Service for managing video quality settings and real-time adjustments."""
    
    def __init__(self):
        self.active_quality_settings: Dict[int, Dict] = {}  # user_id -> quality_settings
        self.quality_history: Dict[int, List[Dict]] = {}  # user_id -> quality_changes
        self.quality_presets = CompressionService.get_video_quality_presets()
    
    async def set_video_quality(
        self, 
        user_id: int, 
        quality_preset: str,
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Set video quality for a user.
        
        Args:
            user_id: User ID
            quality_preset: Quality preset name
            custom_settings: Custom quality settings
            
        Returns:
            Dictionary with quality settings and status
        """
        try:
            # Validate quality preset
            if quality_preset not in self.quality_presets and not custom_settings:
                raise ValueError(f"Invalid quality preset: {quality_preset}")
            
            # Get quality settings
            if custom_settings:
                settings = custom_settings
            else:
                settings = self.quality_presets[quality_preset].copy()
            
            # Store current settings
            self.active_quality_settings[user_id] = {
                "preset": quality_preset,
                "settings": settings,
                "applied_at": datetime.now(timezone.utc),
                "custom": custom_settings is not None
            }
            
            # Add to history
            if user_id not in self.quality_history:
                self.quality_history[user_id] = []
            
            self.quality_history[user_id].append({
                "preset": quality_preset,
                "settings": settings.copy(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "custom": custom_settings is not None
            })
            
            # Keep only last 10 quality changes
            if len(self.quality_history[user_id]) > 10:
                self.quality_history[user_id] = self.quality_history[user_id][-10:]
            
            logger.info(f"Video quality set for user {user_id}: {quality_preset}")
            
            return {
                "success": True,
                "user_id": user_id,
                "quality_preset": quality_preset,
                "settings": settings,
                "applied_at": self.active_quality_settings[user_id]["applied_at"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to set video quality for user {user_id}: {str(e)}")
            raise
    
    async def get_video_quality(self, user_id: int) -> Dict[str, Any]:
        """Get current video quality settings for a user."""
        if user_id not in self.active_quality_settings:
            # Return default medium quality
            default_settings = self.quality_presets["medium"]
            return {
                "user_id": user_id,
                "quality_preset": "medium",
                "settings": default_settings,
                "is_default": True
            }
        
        settings = self.active_quality_settings[user_id]
        return {
            "user_id": user_id,
            "quality_preset": settings["preset"],
            "settings": settings["settings"],
            "applied_at": settings["applied_at"].isoformat(),
            "is_custom": settings["custom"]
        }
    
    async def get_available_quality_presets(self) -> Dict[str, Any]:
        """Get all available video quality presets."""
        return {
            "presets": self.quality_presets,
            "default_preset": "medium",
            "total_presets": len(self.quality_presets)
        }
    
    async def get_quality_history(self, user_id: int) -> Dict[str, Any]:
        """Get video quality change history for a user."""
        history = self.quality_history.get(user_id, [])
        return {
            "user_id": user_id,
            "history": history,
            "total_changes": len(history)
        }
    
    async def create_custom_quality_settings(
        self,
        user_id: int,
        resolution: str,
        bitrate: str,
        fps: int,
        crf: int,
        preset: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create custom video quality settings.
        
        Args:
            user_id: User ID
            resolution: Video resolution (e.g., "1280x720")
            bitrate: Video bitrate (e.g., "500k")
            fps: Frames per second
            crf: Constant Rate Factor (18-51, lower = better quality)
            preset: Encoding preset (ultrafast, fast, medium, slow, slower)
        """
        try:
            # Validate parameters
            if not self._validate_resolution(resolution):
                raise ValueError(f"Invalid resolution format: {resolution}")
            
            if not self._validate_bitrate(bitrate):
                raise ValueError(f"Invalid bitrate format: {bitrate}")
            
            if not (1 <= fps <= 60):
                raise ValueError(f"FPS must be between 1 and 60: {fps}")
            
            if not (18 <= crf <= 51):
                raise ValueError(f"CRF must be between 18 and 51: {crf}")
            
            valid_presets = ["ultrafast", "fast", "medium", "slow", "slower", "veryslow"]
            if preset not in valid_presets:
                raise ValueError(f"Invalid preset: {preset}. Must be one of: {valid_presets}")
            
            # Create custom settings
            custom_settings = {
                "resolution": resolution,
                "bitrate": bitrate,
                "fps": fps,
                "crf": crf,
                "preset": preset,
                "description": f"Custom - {resolution} @ {fps}fps, {bitrate} bitrate"
            }
            
            # Apply custom settings
            result = await self.set_video_quality(
                user_id=user_id,
                quality_preset="custom",
                custom_settings=custom_settings
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create custom quality settings for user {user_id}: {str(e)}")
            raise
    
    async def adjust_quality_for_network(
        self,
        user_id: int,
        network_quality_score: float,
        current_bandwidth: str
    ) -> Dict[str, Any]:
        """
        Automatically adjust video quality based on network conditions.
        
        Args:
            user_id: User ID
            network_quality_score: Network quality score (0-100)
            current_bandwidth: Current bandwidth profile
        """
        try:
            # Determine appropriate quality preset based on network
            if network_quality_score >= 90:
                recommended_preset = "ultra_high"
            elif network_quality_score >= 75:
                recommended_preset = "very_high"
            elif network_quality_score >= 60:
                recommended_preset = "high"
            elif network_quality_score >= 40:
                recommended_preset = "medium"
            elif network_quality_score >= 20:
                recommended_preset = "low"
            else:
                recommended_preset = "ultra_low"
            
            # Get current quality
            current_quality = await self.get_video_quality(user_id)
            current_preset = current_quality["quality_preset"]
            
            # Only change if recommendation is different
            if recommended_preset != current_preset:
                result = await self.set_video_quality(user_id, recommended_preset)
                
                logger.info(f"Auto-adjusted video quality for user {user_id}: {current_preset} -> {recommended_preset}")
                
                return {
                    "success": True,
                    "auto_adjusted": True,
                    "old_preset": current_preset,
                    "new_preset": recommended_preset,
                    "reason": f"Network quality score: {network_quality_score}",
                    "settings": result["settings"]
                }
            else:
                return {
                    "success": True,
                    "auto_adjusted": False,
                    "current_preset": current_preset,
                    "reason": "Quality already optimal for network conditions"
                }
                
        except Exception as e:
            logger.error(f"Failed to adjust quality for network: {str(e)}")
            raise
    
    async def get_quality_recommendations(
        self,
        user_id: int,
        network_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get video quality recommendations based on network conditions.
        
        Args:
            user_id: User ID
            network_conditions: Dictionary with network metrics
        """
        try:
            latency = network_conditions.get("latency", 100)
            bandwidth = network_conditions.get("bandwidth", 100)
            packet_loss = network_conditions.get("packet_loss", 0)
            
            recommendations = []
            
            # Analyze each preset for suitability
            for preset_name, preset_settings in self.quality_presets.items():
                suitability_score = self._calculate_preset_suitability(
                    preset_settings, latency, bandwidth, packet_loss
                )
                
                recommendations.append({
                    "preset": preset_name,
                    "settings": preset_settings,
                    "suitability_score": suitability_score,
                    "recommended": suitability_score >= 80
                })
            
            # Sort by suitability score
            recommendations.sort(key=lambda x: x["suitability_score"], reverse=True)
            
            return {
                "user_id": user_id,
                "network_conditions": network_conditions,
                "recommendations": recommendations,
                "top_recommendation": recommendations[0] if recommendations else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get quality recommendations: {str(e)}")
            raise
    
    def _validate_resolution(self, resolution: str) -> bool:
        """Validate resolution format (e.g., '1280x720')."""
        try:
            parts = resolution.split('x')
            if len(parts) != 2:
                return False
            width, height = int(parts[0]), int(parts[1])
            return 160 <= width <= 3840 and 120 <= height <= 2160
        except (ValueError, IndexError):
            return False
    
    def _validate_bitrate(self, bitrate: str) -> bool:
        """Validate bitrate format (e.g., '500k', '1M')."""
        try:
            if bitrate.endswith('k'):
                value = int(bitrate[:-1])
                return 10 <= value <= 10000
            elif bitrate.endswith('M'):
                value = int(bitrate[:-1])
                return 1 <= value <= 50
            else:
                return False
        except (ValueError, IndexError):
            return False
    
    def _calculate_preset_suitability(
        self,
        preset_settings: Dict[str, Any],
        latency: float,
        bandwidth: float,
        packet_loss: float
    ) -> float:
        """Calculate how suitable a preset is for given network conditions."""
        try:
            # Extract preset parameters
            bitrate_str = preset_settings.get("bitrate", "400k")
            bitrate_value = int(bitrate_str.replace('k', '').replace('M', '000'))
            fps = preset_settings.get("fps", 24)
            resolution = preset_settings.get("resolution", "854x480")
            
            # Calculate resolution complexity
            width, height = map(int, resolution.split('x'))
            pixel_count = width * height
            
            # Calculate suitability score (0-100)
            score = 100
            
            # Penalty for high bitrate on low bandwidth
            if bandwidth < bitrate_value * 1.5:
                score -= 30
            
            # Penalty for high FPS on high latency
            if latency > 200 and fps > 20:
                score -= 20
            
            # Penalty for high resolution on poor network
            if packet_loss > 2 and pixel_count > 640 * 480:
                score -= 25
            
            # Bonus for appropriate settings
            if latency < 100 and fps >= 24:
                score += 10
            
            if packet_loss < 1 and pixel_count >= 1280 * 720:
                score += 15
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating preset suitability: {str(e)}")
            return 50  # Default moderate suitability

# Global instance
video_quality_service = VideoQualityService()
