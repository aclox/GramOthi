"""
Compression service for low-bandwidth optimization
Handles audio, image, and document compression for rural connectivity
"""

import os
import subprocess
import tempfile
from typing import Optional, Tuple
from PIL import Image
import ffmpeg
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CompressionService:
    """Service for compressing files to optimize for low-bandwidth scenarios."""
    
    # Enhanced compression quality settings for poor networks
    BANDWIDTH_PROFILES = {
        "ultra_low": {  # < 32kbps - Emergency mode
            "audio_bitrate": "16k",
            "audio_sample_rate": "16000",
            "audio_channels": 1,  # Mono for ultra low bandwidth
            "audio_codec": "opus",
            "video_bitrate": "50k",
            "video_fps": 5,
            "video_resolution": "320x240",
            "image_quality": 20,
            "image_max_width": 640,
            "image_max_height": 480,
            "compression_level": 9,  # Maximum compression
            "buffer_size": 1024,
            "chunk_size": 512
        },
        "very_low": {  # 32-64kbps
            "audio_bitrate": "32k",
            "audio_sample_rate": "22050",
            "audio_channels": 1,
            "audio_codec": "opus",
            "video_bitrate": "100k",
            "video_fps": 10,
            "video_resolution": "480x360",
            "image_quality": 30,
            "image_max_width": 800,
            "image_max_height": 600,
            "compression_level": 8,
            "buffer_size": 2048,
            "chunk_size": 1024
        },
        "low": {  # 64-128kbps
            "audio_bitrate": "64k",
            "audio_sample_rate": "44100",
            "audio_channels": 2,
            "audio_codec": "opus",
            "video_bitrate": "200k",
            "video_fps": 15,
            "video_resolution": "640x480",
            "image_quality": 50,
            "image_max_width": 1024,
            "image_max_height": 768,
            "compression_level": 7,
            "buffer_size": 4096,
            "chunk_size": 2048
        },
        "medium": {  # 128-256kbps
            "audio_bitrate": "128k",
            "audio_sample_rate": "44100",
            "audio_channels": 2,
            "audio_codec": "opus",
            "video_bitrate": "400k",
            "video_fps": 24,
            "video_resolution": "854x480",
            "image_quality": 70,
            "image_max_width": 1280,
            "image_max_height": 720,
            "compression_level": 6,
            "buffer_size": 8192,
            "chunk_size": 4096
        },
        "high": {  # 256-512kbps
            "audio_bitrate": "192k",
            "audio_sample_rate": "44100",
            "audio_channels": 2,
            "audio_codec": "opus",
            "video_bitrate": "800k",
            "video_fps": 30,
            "video_resolution": "1280x720",
            "image_quality": 85,
            "image_max_width": 1920,
            "image_max_height": 1080,
            "compression_level": 5,
            "buffer_size": 16384,
            "chunk_size": 8192
        },
        "ultra_high": {  # > 512kbps
            "audio_bitrate": "256k",
            "audio_sample_rate": "48000",
            "audio_channels": 2,
            "audio_codec": "opus",
            "video_bitrate": "1500k",
            "video_fps": 30,
            "video_resolution": "1920x1080",
            "image_quality": 95,
            "image_max_width": 2560,
            "image_max_height": 1440,
            "compression_level": 4,
            "buffer_size": 32768,
            "chunk_size": 16384
        }
    }
    
    @staticmethod
    def compress_video(input_path: str, output_path: str, bandwidth_profile: str = "low") -> bool:
        """
        Compress video file using ffmpeg with advanced optimization for poor networks.
        """
        try:
            if bandwidth_profile not in CompressionService.BANDWIDTH_PROFILES:
                bandwidth_profile = "low"
            
            profile = CompressionService.BANDWIDTH_PROFILES[bandwidth_profile]
            
            # Advanced video compression with multiple passes for better quality
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264',  # H.264 codec for better compatibility
                '-preset', 'ultrafast',  # Fast encoding for real-time
                '-tune', 'zerolatency',  # Optimize for low latency
                '-crf', str(28 + (9 - profile['compression_level'])),  # Quality factor
                '-maxrate', profile['video_bitrate'],
                '-bufsize', str(int(profile['video_bitrate'].replace('k', '')) * 2) + 'k',
                '-vf', f"scale={profile['video_resolution']},fps={profile['video_fps']}",
                '-c:a', 'libopus',  # Opus audio codec
                '-b:a', profile['audio_bitrate'],
                '-ar', str(profile['audio_sample_rate']),
                '-ac', str(profile['audio_channels']),
                '-movflags', '+faststart',  # Optimize for streaming
                '-f', 'mp4',
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Video compressed successfully: {input_path} -> {output_path}")
                return True
            else:
                logger.error(f"Video compression failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error compressing video: {str(e)}")
            return False

    @staticmethod
    def compress_audio(input_path: str, output_path: str, bandwidth_profile: str = "low") -> bool:
        """
        Compress audio file using ffmpeg for low-bandwidth delivery.
        
        Args:
            input_path: Path to input audio file
            output_path: Path to output compressed audio file
            bandwidth_profile: Bandwidth profile to use for compression
            
        Returns:
            bool: True if compression successful, False otherwise
        """
        try:
            profile = CompressionService.BANDWIDTH_PROFILES.get(bandwidth_profile, "low")
            
            # Get input file info
            probe = ffmpeg.probe(input_path)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            if not audio_stream:
                logger.error(f"No audio stream found in {input_path}")
                return False
            
            # Build ffmpeg command for audio compression
            input_stream = ffmpeg.input(input_path)
            
            # Compress audio with specified bitrate and sample rate
            audio = input_stream.audio.filter('aresample', ar=profile['audio_sample_rate'])
            audio = audio.filter('acompressor', threshold=0.089, ratio=9, attack=200, release=1000)
            
            # Output with specified bitrate
            output = ffmpeg.output(
                audio,
                output_path,
                acodec='mp3',
                audio_bitrate=profile['audio_bitrate'],
                ac=1,  # Mono for better compression
                ar=profile['audio_sample_rate']
            )
            
            # Overwrite output file if it exists
            output = ffmpeg.overwrite_output(output)
            
            # Run ffmpeg command
            ffmpeg.run(output, capture_stdout=True, capture_stderr=True)
            
            logger.info(f"Audio compressed successfully: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Audio compression failed: {e}")
            return False
    
    @staticmethod
    def compress_image(input_path: str, output_path: str, bandwidth_profile: str = "low") -> bool:
        """
        Compress image file for low-bandwidth delivery.
        
        Args:
            input_path: Path to input image file
            output_path: Path to output compressed image file
            bandwidth_profile: Bandwidth profile to use for compression
            
        Returns:
            bool: True if compression successful, False otherwise
        """
        try:
            profile = CompressionService.BANDWIDTH_PROFILES.get(bandwidth_profile, "low")
            
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if image is too large
                if img.width > profile['image_max_width'] or img.height > profile['image_max_height']:
                    img.thumbnail(
                        (profile['image_max_width'], profile['image_max_height']),
                        Image.Resampling.LANCZOS
                    )
                
                # Save with compression
                img.save(
                    output_path,
                    'JPEG',
                    quality=profile['image_quality'],
                    optimize=True,
                    progressive=True  # Progressive JPEG for better loading
                )
            
            logger.info(f"Image compressed successfully: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            return False
    
    @staticmethod
    def compress_pdf(input_path: str, output_path: str, bandwidth_profile: str = "low") -> bool:
        """
        Compress PDF file for low-bandwidth delivery.
        
        Args:
            input_path: Path to input PDF file
            output_path: Path to output compressed PDF file
            bandwidth_profile: Bandwidth profile to use for compression
            
        Returns:
            bool: True if compression successful, False otherwise
        """
        try:
            # Use ghostscript for PDF compression
            compression_level = "ebook" if bandwidth_profile in ["ultra_low", "low"] else "printer"
            
            cmd = [
                "gs",
                "-sDEVICE=pdfwrite",
                f"-dPDFSETTINGS=/{compression_level}",
                "-dCompatibilityLevel=1.4",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={output_path}",
                input_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"PDF compressed successfully: {input_path} -> {output_path}")
                return True
            else:
                logger.error(f"PDF compression failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"PDF compression failed: {e}")
            return False
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """Get file size in MB."""
        return os.path.getsize(file_path) / (1024 * 1024)
    
    @staticmethod
    def get_compression_ratio(original_path: str, compressed_path: str) -> float:
        """Calculate compression ratio."""
        original_size = os.path.getsize(original_path)
        compressed_size = os.path.getsize(compressed_path)
        return (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
    
    @staticmethod
    def compress_file(input_path: str, output_path: str, bandwidth_profile: str = "low") -> Tuple[bool, dict]:
        """
        Compress any supported file type based on its extension.
        
        Args:
            input_path: Path to input file
            output_path: Path to output compressed file
            bandwidth_profile: Bandwidth profile to use for compression
            
        Returns:
            Tuple[bool, dict]: (success, compression_info)
        """
        file_ext = Path(input_path).suffix.lower()
        original_size = CompressionService.get_file_size_mb(input_path)
        
        success = False
        
        if file_ext in ['.mp3', '.wav', '.m4a', '.aac', '.flac']:
            success = CompressionService.compress_audio(input_path, output_path, bandwidth_profile)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            success = CompressionService.compress_image(input_path, output_path, bandwidth_profile)
        elif file_ext == '.pdf':
            success = CompressionService.compress_pdf(input_path, output_path, bandwidth_profile)
        else:
            # For unsupported files, just copy
            import shutil
            shutil.copy2(input_path, output_path)
            success = True
        
        if success and os.path.exists(output_path):
            compressed_size = CompressionService.get_file_size_mb(output_path)
            compression_ratio = CompressionService.get_compression_ratio(input_path, output_path)
            
            return True, {
                "original_size_mb": round(original_size, 2),
                "compressed_size_mb": round(compressed_size, 2),
                "compression_ratio": round(compression_ratio, 2),
                "bandwidth_profile": bandwidth_profile,
                "file_type": file_ext
            }
        
        return False, {"error": "Compression failed"}

class BandwidthDetector:
    """Service for detecting user's bandwidth and recommending compression profile."""
    
    @staticmethod
    def detect_bandwidth_profile(user_agent: str = "", connection_type: str = "") -> str:
        """
        Detect bandwidth profile based on user agent and connection type.
        
        Args:
            user_agent: User agent string from request
            connection_type: Connection type hint from client
            
        Returns:
            str: Recommended bandwidth profile
        """
        # Check for mobile devices (typically lower bandwidth)
        mobile_indicators = ['mobile', 'android', 'iphone', 'ipad', 'blackberry']
        is_mobile = any(indicator in user_agent.lower() for indicator in mobile_indicators)
        
        # Check for slow connection indicators
        slow_indicators = ['2g', '3g', 'slow', 'low']
        is_slow = any(indicator in connection_type.lower() for indicator in slow_indicators)
        
        if is_slow or connection_type == "2g":
            return "ultra_low"
        elif is_mobile or connection_type == "3g":
            return "low"
        elif connection_type == "4g":
            return "medium"
        else:
            return "high"
    
    @staticmethod
    def get_compression_recommendations(bandwidth_profile: str) -> dict:
        """Get compression recommendations for a bandwidth profile."""
        profiles = {
            "ultra_low": {
                "audio_bitrate": "32k",
                "max_file_size_mb": 5,
                "recommended_formats": ["mp3", "jpg"],
                "description": "Ultra-low bandwidth (< 64kbps) - Maximum compression"
            },
            "low": {
                "audio_bitrate": "64k",
                "max_file_size_mb": 10,
                "recommended_formats": ["mp3", "jpg", "pdf"],
                "description": "Low bandwidth (64-128kbps) - High compression"
            },
            "medium": {
                "audio_bitrate": "128k",
                "max_file_size_mb": 25,
                "recommended_formats": ["mp3", "jpg", "pdf", "png"],
                "description": "Medium bandwidth (128-256kbps) - Moderate compression"
            },
            "high": {
                "audio_bitrate": "192k",
                "max_file_size_mb": 50,
                "recommended_formats": ["mp3", "wav", "jpg", "png", "pdf"],
                "description": "High bandwidth (> 256kbps) - Minimal compression"
            }
        }
        
        return profiles.get(bandwidth_profile, profiles["medium"])
