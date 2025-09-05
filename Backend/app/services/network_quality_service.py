"""
Network Quality Detection Service for GramOthi
Advanced network quality detection and adaptive streaming optimization
"""

import asyncio
import time
import statistics
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import aiohttp
import json

logger = logging.getLogger(__name__)

class NetworkQualityService:
    """Service for detecting network quality and optimizing streaming parameters."""
    
    def __init__(self):
        self.quality_metrics = {}
        self.adaptive_profiles = {
            "emergency": {
                "audio_bitrate": "8k",
                "video_bitrate": "25k",
                "video_fps": 3,
                "video_resolution": "240x180",
                "buffer_size": 512,
                "chunk_size": 256,
                "retry_attempts": 5,
                "timeout": 30
            },
            "critical": {
                "audio_bitrate": "16k",
                "video_bitrate": "50k",
                "video_fps": 5,
                "video_resolution": "320x240",
                "buffer_size": 1024,
                "chunk_size": 512,
                "retry_attempts": 3,
                "timeout": 20
            },
            "poor": {
                "audio_bitrate": "32k",
                "video_bitrate": "100k",
                "video_fps": 10,
                "video_resolution": "480x360",
                "buffer_size": 2048,
                "chunk_size": 1024,
                "retry_attempts": 2,
                "timeout": 15
            },
            "fair": {
                "audio_bitrate": "64k",
                "video_bitrate": "200k",
                "video_fps": 15,
                "video_resolution": "640x480",
                "buffer_size": 4096,
                "chunk_size": 2048,
                "retry_attempts": 2,
                "timeout": 10
            },
            "good": {
                "audio_bitrate": "128k",
                "video_bitrate": "400k",
                "video_fps": 24,
                "video_resolution": "854x480",
                "buffer_size": 8192,
                "chunk_size": 4096,
                "retry_attempts": 1,
                "timeout": 8
            },
            "excellent": {
                "audio_bitrate": "192k",
                "video_bitrate": "800k",
                "video_fps": 30,
                "video_resolution": "1280x720",
                "buffer_size": 16384,
                "chunk_size": 8192,
                "retry_attempts": 1,
                "timeout": 5
            }
        }
    
    async def detect_network_quality(self, user_id: int, test_duration: int = 10) -> Dict[str, any]:
        """
        Perform comprehensive network quality detection.
        
        Args:
            user_id: User ID for tracking
            test_duration: Duration of network test in seconds
            
        Returns:
            Dictionary with network quality metrics and recommended profile
        """
        try:
            logger.info(f"Starting network quality detection for user {user_id}")
            
            # Perform multiple network tests
            latency_results = await self._test_latency()
            bandwidth_results = await self._test_bandwidth()
            packet_loss_results = await self._test_packet_loss()
            jitter_results = await self._test_jitter()
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(
                latency_results, bandwidth_results, packet_loss_results, jitter_results
            )
            
            # Determine recommended profile
            recommended_profile = self._get_recommended_profile(quality_score)
            
            # Store metrics
            self.quality_metrics[user_id] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "latency": latency_results,
                "bandwidth": bandwidth_results,
                "packet_loss": packet_loss_results,
                "jitter": jitter_results,
                "quality_score": quality_score,
                "recommended_profile": recommended_profile,
                "test_duration": test_duration
            }
            
            logger.info(f"Network quality detection completed for user {user_id}: {recommended_profile}")
            
            return {
                "user_id": user_id,
                "quality_score": quality_score,
                "recommended_profile": recommended_profile,
                "metrics": {
                    "latency_ms": latency_results["average"],
                    "bandwidth_kbps": bandwidth_results["download"],
                    "packet_loss_percent": packet_loss_results["loss_rate"],
                    "jitter_ms": jitter_results["average"]
                },
                "profile_config": self.adaptive_profiles[recommended_profile]
            }
            
        except Exception as e:
            logger.error(f"Network quality detection failed for user {user_id}: {str(e)}")
            return {
                "user_id": user_id,
                "quality_score": 0,
                "recommended_profile": "emergency",
                "error": str(e),
                "profile_config": self.adaptive_profiles["emergency"]
            }
    
    async def _test_latency(self) -> Dict[str, float]:
        """Test network latency to multiple servers."""
        test_servers = [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://httpbin.org/get"
        ]
        
        latencies = []
        
        for server in test_servers:
            try:
                start_time = time.time()
                async with aiohttp.ClientSession() as session:
                    async with session.get(server, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            latency = (time.time() - start_time) * 1000  # Convert to ms
                            latencies.append(latency)
            except Exception as e:
                logger.warning(f"Latency test failed for {server}: {str(e)}")
                continue
        
        if not latencies:
            return {"average": 1000, "min": 1000, "max": 1000, "samples": 0}
        
        return {
            "average": statistics.mean(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "samples": len(latencies)
        }
    
    async def _test_bandwidth(self) -> Dict[str, float]:
        """Test download and upload bandwidth."""
        try:
            # Test download bandwidth with a small file
            test_url = "https://httpbin.org/bytes/1024"  # 1KB test file
            
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.read()
                        download_time = time.time() - start_time
                        download_speed = (len(data) * 8) / (download_time * 1000)  # kbps
                        
                        return {
                            "download": download_speed,
                            "upload": download_speed * 0.8,  # Estimate upload as 80% of download
                            "test_size_bytes": len(data),
                            "test_duration": download_time
                        }
        except Exception as e:
            logger.warning(f"Bandwidth test failed: {str(e)}")
        
        return {"download": 64, "upload": 32, "test_size_bytes": 0, "test_duration": 0}
    
    async def _test_packet_loss(self) -> Dict[str, float]:
        """Test packet loss by sending multiple small requests."""
        test_url = "https://httpbin.org/get"
        total_requests = 10
        successful_requests = 0
        
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for _ in range(total_requests):
                    task = session.get(test_url, timeout=aiohttp.ClientTimeout(total=3))
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                for response in responses:
                    if not isinstance(response, Exception) and response.status == 200:
                        successful_requests += 1
                
                loss_rate = ((total_requests - successful_requests) / total_requests) * 100
                
                return {
                    "loss_rate": loss_rate,
                    "successful_requests": successful_requests,
                    "total_requests": total_requests
                }
        except Exception as e:
            logger.warning(f"Packet loss test failed: {str(e)}")
        
        return {"loss_rate": 0, "successful_requests": 0, "total_requests": 0}
    
    async def _test_jitter(self) -> Dict[str, float]:
        """Test network jitter by measuring latency variation."""
        test_url = "https://httpbin.org/get"
        latencies = []
        
        try:
            async with aiohttp.ClientSession() as session:
                for _ in range(10):
                    start_time = time.time()
                    async with session.get(test_url, timeout=aiohttp.ClientTimeout(total=3)) as response:
                        if response.status == 200:
                            latency = (time.time() - start_time) * 1000
                            latencies.append(latency)
                    await asyncio.sleep(0.1)  # Small delay between requests
            
            if len(latencies) < 2:
                return {"average": 0, "variance": 0, "samples": len(latencies)}
            
            # Calculate jitter as standard deviation of latencies
            mean_latency = statistics.mean(latencies)
            variance = statistics.variance(latencies, mean_latency)
            jitter = variance ** 0.5
            
            return {
                "average": mean_latency,
                "variance": variance,
                "jitter": jitter,
                "samples": len(latencies)
            }
        except Exception as e:
            logger.warning(f"Jitter test failed: {str(e)}")
        
        return {"average": 0, "variance": 0, "jitter": 0, "samples": 0}
    
    def _calculate_quality_score(self, latency: Dict, bandwidth: Dict, packet_loss: Dict, jitter: Dict) -> float:
        """Calculate overall network quality score (0-100)."""
        try:
            # Latency score (0-25 points)
            latency_score = max(0, 25 - (latency["average"] / 20))  # Penalty for high latency
            
            # Bandwidth score (0-35 points)
            bandwidth_score = min(35, (bandwidth["download"] / 10))  # Reward for high bandwidth
            
            # Packet loss score (0-25 points)
            packet_loss_score = max(0, 25 - (packet_loss["loss_rate"] * 2))  # Penalty for packet loss
            
            # Jitter score (0-15 points)
            jitter_score = max(0, 15 - (jitter.get("jitter", 0) / 5))  # Penalty for high jitter
            
            total_score = latency_score + bandwidth_score + packet_loss_score + jitter_score
            return min(100, max(0, total_score))
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {str(e)}")
            return 0
    
    def _get_recommended_profile(self, quality_score: float) -> str:
        """Get recommended streaming profile based on quality score."""
        if quality_score >= 90:
            return "excellent"
        elif quality_score >= 75:
            return "good"
        elif quality_score >= 60:
            return "fair"
        elif quality_score >= 40:
            return "poor"
        elif quality_score >= 20:
            return "critical"
        else:
            return "emergency"
    
    async def monitor_connection_quality(self, user_id: int, duration: int = 60) -> Dict[str, any]:
        """
        Continuously monitor connection quality during streaming.
        
        Args:
            user_id: User ID to monitor
            duration: Monitoring duration in seconds
            
        Returns:
            Real-time quality metrics and adaptive recommendations
        """
        try:
            logger.info(f"Starting connection quality monitoring for user {user_id}")
            
            start_time = time.time()
            quality_samples = []
            
            while time.time() - start_time < duration:
                # Quick quality check
                sample = await self._quick_quality_check()
                quality_samples.append(sample)
                
                # Analyze trend
                if len(quality_samples) >= 5:
                    trend = self._analyze_quality_trend(quality_samples[-5:])
                    
                    # Adjust profile if needed
                    current_profile = self.quality_metrics.get(user_id, {}).get("recommended_profile", "fair")
                    adjusted_profile = self._adjust_profile_for_trend(current_profile, trend)
                    
                    if adjusted_profile != current_profile:
                        logger.info(f"Profile adjusted for user {user_id}: {current_profile} -> {adjusted_profile}")
                        self.quality_metrics[user_id]["recommended_profile"] = adjusted_profile
                
                await asyncio.sleep(5)  # Check every 5 seconds
            
            return {
                "user_id": user_id,
                "monitoring_duration": duration,
                "samples_collected": len(quality_samples),
                "final_profile": self.quality_metrics.get(user_id, {}).get("recommended_profile", "fair"),
                "quality_trend": self._analyze_quality_trend(quality_samples)
            }
            
        except Exception as e:
            logger.error(f"Connection quality monitoring failed for user {user_id}: {str(e)}")
            return {"error": str(e)}
    
    async def _quick_quality_check(self) -> Dict[str, float]:
        """Perform a quick quality check for real-time monitoring."""
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get("https://httpbin.org/get", timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status == 200:
                        latency = (time.time() - start_time) * 1000
                        return {"latency": latency, "success": True}
        except Exception as e:
            logger.warning(f"Quick quality check failed: {str(e)}")
        
        return {"latency": 1000, "success": False}
    
    def _analyze_quality_trend(self, samples: List[Dict]) -> str:
        """Analyze quality trend from recent samples."""
        if len(samples) < 3:
            return "stable"
        
        recent_latencies = [s["latency"] for s in samples[-3:]]
        
        if all(recent_latencies[i] < recent_latencies[i-1] for i in range(1, len(recent_latencies))):
            return "improving"
        elif all(recent_latencies[i] > recent_latencies[i-1] for i in range(1, len(recent_latencies))):
            return "degrading"
        else:
            return "stable"
    
    def _adjust_profile_for_trend(self, current_profile: str, trend: str) -> str:
        """Adjust streaming profile based on quality trend."""
        profile_hierarchy = ["emergency", "critical", "poor", "fair", "good", "excellent"]
        
        try:
            current_index = profile_hierarchy.index(current_profile)
            
            if trend == "improving" and current_index < len(profile_hierarchy) - 1:
                return profile_hierarchy[current_index + 1]
            elif trend == "degrading" and current_index > 0:
                return profile_hierarchy[current_index - 1]
            else:
                return current_profile
        except ValueError:
            return "fair"
    
    def get_user_quality_metrics(self, user_id: int) -> Optional[Dict]:
        """Get stored quality metrics for a user."""
        return self.quality_metrics.get(user_id)
    
    def get_adaptive_profile_config(self, profile_name: str) -> Dict:
        """Get configuration for a specific adaptive profile."""
        return self.adaptive_profiles.get(profile_name, self.adaptive_profiles["fair"])

# Global instance
network_quality_service = NetworkQualityService()
