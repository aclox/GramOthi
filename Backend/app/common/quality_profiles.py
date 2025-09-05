"""
Shared quality profiles configuration for GramOthi
Consolidates all quality profile definitions to avoid duplication
"""

from typing import Dict, Any

# Video Quality Presets - Used by video quality service and compression service
VIDEO_QUALITY_PRESETS = {
    "ultra_low": {
        "resolution": "320x240",
        "bitrate": "50k",
        "fps": 5,
        "crf": 35,
        "preset": "ultrafast",
        "description": "Ultra Low - Emergency mode for very poor connections"
    },
    "low": {
        "resolution": "480x360",
        "bitrate": "100k",
        "fps": 10,
        "crf": 32,
        "preset": "ultrafast",
        "description": "Low - Basic quality for poor connections"
    },
    "medium": {
        "resolution": "640x480",
        "bitrate": "200k",
        "fps": 15,
        "crf": 28,
        "preset": "fast",
        "description": "Medium - Balanced quality and bandwidth"
    },
    "high": {
        "resolution": "854x480",
        "bitrate": "400k",
        "fps": 24,
        "crf": 25,
        "preset": "medium",
        "description": "High - Good quality for stable connections"
    },
    "very_high": {
        "resolution": "1280x720",
        "bitrate": "800k",
        "fps": 30,
        "crf": 22,
        "preset": "slow",
        "description": "Very High - Excellent quality for good connections"
    },
    "ultra_high": {
        "resolution": "1920x1080",
        "bitrate": "1500k",
        "fps": 30,
        "crf": 20,
        "preset": "slower",
        "description": "Ultra High - Best quality for excellent connections"
    }
}

# Adaptive Streaming Profiles - Used by network quality service and signaling server
ADAPTIVE_PROFILES = {
    "emergency": {
        "audio": {"bitrate": "8k", "sampleRate": 16000, "channels": 1, "codec": "opus"},
        "video": {"bitrate": "25k", "fps": 3, "resolution": "240x180", "codec": "h264"},
        "network": {"bufferSize": 512, "chunkSize": 256, "retryAttempts": 5, "timeout": 30000}
    },
    "critical": {
        "audio": {"bitrate": "16k", "sampleRate": 22050, "channels": 1, "codec": "opus"},
        "video": {"bitrate": "50k", "fps": 5, "resolution": "320x240", "codec": "h264"},
        "network": {"bufferSize": 1024, "chunkSize": 512, "retryAttempts": 3, "timeout": 20000}
    },
    "poor": {
        "audio": {"bitrate": "32k", "sampleRate": 44100, "channels": 1, "codec": "opus"},
        "video": {"bitrate": "100k", "fps": 10, "resolution": "480x360", "codec": "h264"},
        "network": {"bufferSize": 2048, "chunkSize": 1024, "retryAttempts": 2, "timeout": 15000}
    },
    "fair": {
        "audio": {"bitrate": "64k", "sampleRate": 44100, "channels": 2, "codec": "opus"},
        "video": {"bitrate": "200k", "fps": 15, "resolution": "640x480", "codec": "h264"},
        "network": {"bufferSize": 4096, "chunkSize": 2048, "retryAttempts": 2, "timeout": 10000}
    },
    "good": {
        "audio": {"bitrate": "128k", "sampleRate": 44100, "channels": 2, "codec": "opus"},
        "video": {"bitrate": "400k", "fps": 24, "resolution": "854x480", "codec": "h264"},
        "network": {"bufferSize": 8192, "chunkSize": 4096, "retryAttempts": 1, "timeout": 8000}
    },
    "excellent": {
        "audio": {"bitrate": "192k", "sampleRate": 48000, "channels": 2, "codec": "opus"},
        "video": {"bitrate": "800k", "fps": 30, "resolution": "1280x720", "codec": "h264"},
        "network": {"bufferSize": 16384, "chunkSize": 8192, "retryAttempts": 1, "timeout": 5000}
    }
}

# Bandwidth Profiles - Used by compression service (legacy support)
BANDWIDTH_PROFILES = {
    "ultra_low": {  # < 32kbps - Emergency mode
        "audio_bitrate": "16k",
        "audio_sample_rate": "16000",
        "audio_channels": 1,
        "audio_codec": "opus",
        "video_bitrate": "50k",
        "video_fps": 5,
        "video_resolution": "320x240",
        "image_quality": 20,
        "image_max_width": 640,
        "image_max_height": 480,
        "compression_level": 9,
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

def get_video_quality_presets() -> Dict[str, Dict[str, Any]]:
    """Get video quality presets."""
    return VIDEO_QUALITY_PRESETS

def get_adaptive_profiles() -> Dict[str, Dict[str, Any]]:
    """Get adaptive streaming profiles."""
    return ADAPTIVE_PROFILES

def get_bandwidth_profiles() -> Dict[str, Dict[str, Any]]:
    """Get bandwidth profiles (legacy support)."""
    return BANDWIDTH_PROFILES
