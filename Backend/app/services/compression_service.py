"""
Compression service for low-bandwidth optimization
Handles audio, image, and document compression for rural connectivity
"""

import os
import subprocess
from typing import Optional, Tuple, Dict, Any
from PIL import Image
import ffmpeg
import logging
from pathlib import Path
from ..common.quality_profiles import get_video_quality_presets, get_bandwidth_profiles

logger = logging.getLogger(__name__)

class CompressionService:
    """Service for compressing files to optimize for low-bandwidth scenarios."""
    
    # Get bandwidth profiles from shared configuration
    BANDWIDTH_PROFILES = get_bandwidth_profiles()
    
    @staticmethod
    def get_video_quality_presets() -> Dict[str, Dict[str, Any]]:
        """Get predefined video quality presets for manual adjustment."""
        return get_video_quality_presets()

    @staticmethod
    def compress_video_with_quality(
        input_path: str, 
        output_path: str, 
        quality_preset: str = "medium",
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Compress video with specific quality settings.
        
        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            quality_preset: Quality preset name or custom settings
            custom_settings: Custom quality settings to override preset
        """
        try:
            # Get quality settings
            if custom_settings:
                settings = custom_settings
            else:
                presets = CompressionService.get_video_quality_presets()
                if quality_preset not in presets:
                    quality_preset = "medium"
                settings = presets[quality_preset]
            
            # Build ffmpeg command with quality settings
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264',
                '-preset', settings.get('preset', 'medium'),
                '-crf', str(settings.get('crf', 28)),
                '-maxrate', settings.get('bitrate', '400k'),
                '-bufsize', str(int(settings.get('bitrate', '400k').replace('k', '')) * 2) + 'k',
                '-vf', f"scale={settings.get('resolution', '854x480')},fps={settings.get('fps', 24)}",
                '-c:a', 'libopus',
                '-b:a', '64k',  # Fixed audio bitrate
                '-ar', '44100',
                '-ac', '2',
                '-movflags', '+faststart',
                '-f', 'mp4',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Video compressed with quality preset '{quality_preset}': {input_path} -> {output_path}")
                return True
            else:
                logger.error(f"Video compression failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error compressing video with quality settings: {str(e)}")
            return False

    @staticmethod
    def compress_video(input_path: str, output_path: str, bandwidth_profile: str = "low") -> bool:
        """
        Compress video file using ffmpeg with advanced optimization for poor networks.
        This method is deprecated - use compress_video_with_quality instead.
        """
        # Convert bandwidth profile to quality preset
        profile_mapping = {
            "ultra_low": "ultra_low",
            "very_low": "low", 
            "low": "low",
            "medium": "medium",
            "high": "high",
            "ultra_high": "very_high"
        }
        
        quality_preset = profile_mapping.get(bandwidth_profile, "medium")
        return CompressionService.compress_video_with_quality(input_path, output_path, quality_preset)
    
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
