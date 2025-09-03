import os
import json
import zipfile
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import ffmpeg
from PIL import Image
import logging
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import cv2
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediaProcessor:
    """Handles media processing for lecture bundles including audio compression, slide optimization, and timeline creation"""
    
    def __init__(self, upload_dir: str = "uploads", temp_dir: str = "temp"):
        self.upload_dir = Path(upload_dir)
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Audio compression settings for low bandwidth
        self.audio_settings = {
            "codec": "libopus",
            "bitrate": "32k",  # Very low bitrate for rural areas
            "sample_rate": 16000,  # Lower sample rate to reduce size
            "channels": 1,  # Mono audio
            "format": "ogg"
        }
        
        # Image optimization settings
        self.image_settings = {
            "format": "JPEG",
            "quality": 75,  # Balanced quality/size
            "max_width": 800,  # Limit width for mobile devices
            "max_height": 600,  # Limit height for mobile devices
            "optimize": True
        }
    
    async def process_lecture_bundle(
        self, 
        video_path: str, 
        slides_path: str, 
        bundle_id: int,
        title: str
    ) -> Dict[str, any]:
        """
        Main processing pipeline for lecture bundles
        """
        try:
            logger.info(f"Starting processing for bundle {bundle_id}: {title}")
            
            # Create bundle directory
            bundle_dir = self.temp_dir / f"bundle_{bundle_id}"
            bundle_dir.mkdir(exist_ok=True)
            
            # Step 1: Extract and compress audio
            logger.info("Step 1: Extracting and compressing audio...")
            audio_result = await self._extract_and_compress_audio(
                video_path, 
                bundle_dir / "audio.ogg"
            )
            
            # Step 2: Optimize slides
            logger.info("Step 2: Optimizing slides...")
            slides_result = await self._optimize_slides(
                slides_path, 
                bundle_dir / "slides"
            )
            
            # Step 3: Create timeline
            logger.info("Step 3: Creating slide timeline...")
            timeline_result = await self._create_slide_timeline(
                video_path,
                slides_result["slide_paths"],
                bundle_dir / "timeline.json"
            )
            
            # Step 4: Create bundle
            logger.info("Step 4: Creating final bundle...")
            bundle_result = await self._create_bundle(
                bundle_dir,
                bundle_id,
                title
            )
            
            # Calculate compression ratio
            original_size = self._get_file_size(video_path) + self._get_directory_size(slides_path)
            compressed_size = bundle_result["bundle_size"]
            compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
            
            result = {
                "success": True,
                "bundle_id": bundle_id,
                "compressed_audio_path": str(audio_result["output_path"]),
                "optimized_slides_path": str(slides_result["output_dir"]),
                "timeline_json_path": str(timeline_result["timeline_path"]),
                "bundle_zip_path": str(bundle_result["bundle_path"]),
                "bundle_size": compressed_size,
                "audio_duration": audio_result["duration"],
                "slide_count": slides_result["slide_count"],
                "compression_ratio": compression_ratio,
                "processing_metadata": {
                    "audio_compression": audio_result,
                    "slide_optimization": slides_result,
                    "timeline_creation": timeline_result,
                    "bundle_creation": bundle_result
                }
            }
            
            logger.info(f"Processing completed for bundle {bundle_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing bundle {bundle_id}: {str(e)}")
            return {
                "success": False,
                "bundle_id": bundle_id,
                "error": str(e)
            }
    
    async def _extract_and_compress_audio(self, video_path: str, output_path: Path) -> Dict[str, any]:
        """Extract audio from video and compress it for low bandwidth"""
        try:
            # Probe video to get duration and audio info
            probe = ffmpeg.probe(video_path)
            duration = float(probe['streams'][0]['duration'])
            
            # Extract and compress audio
            (
                ffmpeg
                .input(video_path)
                .output(
                    str(output_path),
                    **self.audio_settings,
                    acodec=self.audio_settings["codec"],
                    audio_bitrate=self.audio_settings["bitrate"],
                    ar=self.audio_settings["sample_rate"],
                    ac=self.audio_settings["channels"]
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Get compressed audio size
            compressed_size = self._get_file_size(str(output_path))
            
            return {
                "success": True,
                "output_path": output_path,
                "duration": duration,
                "compressed_size": compressed_size,
                "settings": self.audio_settings
            }
            
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise
    
    async def _optimize_slides(self, slides_path: str, output_dir: Path) -> Dict[str, any]:
        """Optimize slide images for mobile devices and low bandwidth"""
        try:
            output_dir.mkdir(exist_ok=True)
            slide_paths = []
            total_original_size = 0
            total_optimized_size = 0
            
            # Get all image files from slides directory
            slides_dir = Path(slides_path)
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
            
            image_files = [
                f for f in slides_dir.iterdir() 
                if f.suffix.lower() in image_extensions
            ]
            
            # Process each image
            for i, image_file in enumerate(sorted(image_files)):
                try:
                    # Open and optimize image
                    with Image.open(image_file) as img:
                        # Convert to RGB if necessary
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # Resize if too large
                        if img.width > self.image_settings["max_width"] or img.height > self.image_settings["max_height"]:
                            img.thumbnail(
                                (self.image_settings["max_width"], self.image_settings["max_height"]),
                                Image.Resampling.LANCZOS
                            )
                        
                        # Save optimized image
                        output_path = output_dir / f"slide_{i+1:03d}.jpg"
                        img.save(
                            output_path,
                            format=self.image_settings["format"],
                            quality=self.image_settings["quality"],
                            optimize=self.image_settings["optimize"]
                        )
                        
                        slide_paths.append(str(output_path))
                        total_original_size += self._get_file_size(str(image_file))
                        total_optimized_size += self._get_file_size(str(output_path))
                        
                except Exception as e:
                    logger.warning(f"Error processing slide {image_file}: {str(e)}")
                    continue
            
            compression_ratio = total_original_size / total_optimized_size if total_optimized_size > 0 else 0
            
            return {
                "success": True,
                "output_dir": output_dir,
                "slide_paths": slide_paths,
                "slide_count": len(slide_paths),
                "total_original_size": total_original_size,
                "total_optimized_size": total_optimized_size,
                "compression_ratio": compression_ratio
            }
            
        except Exception as e:
            logger.error(f"Error optimizing slides: {str(e)}")
            raise
    
    async def _create_slide_timeline(
        self, 
        video_path: str, 
        slide_paths: List[str], 
        timeline_path: Path
    ) -> Dict[str, any]:
        """Create timeline JSON for slide synchronization with computer vision-based change detection"""
        try:
            # Get video duration and frame rate
            probe = ffmpeg.probe(video_path)
            duration = float(probe['streams'][0]['duration'])
            frame_rate = eval(probe['streams'][0]['r_frame_rate'])  # e.g., "30/1" -> 30.0
            
            logger.info(f"Video duration: {duration}s, Frame rate: {frame_rate}fps")
            
            # Extract frames at regular intervals for slide change detection
            frame_interval = max(1, int(frame_rate * 2))  # Sample every 2 seconds
            slide_transitions = await self._detect_slide_changes(video_path, frame_interval)
            
            # If no transitions detected, fall back to equal distribution
            if not slide_transitions:
                logger.warning("No slide transitions detected, using equal distribution")
                slide_count = len(slide_paths)
                slide_duration = duration / slide_count if slide_count > 0 else 0
                
                timeline_data = []
                for i, slide_path in enumerate(slide_paths):
                    timestamp = i * slide_duration
                    timeline_entry = {
                        "timestamp": self._format_timestamp(timestamp),
                        "slide_path": slide_path,
                        "slide_number": i + 1,
                        "duration": slide_duration
                    }
                    timeline_data.append(timeline_entry)
            else:
                # Use detected transitions to create accurate timeline
                timeline_data = await self._create_accurate_timeline(
                    slide_transitions, slide_paths, duration
                )
            
            # Save timeline JSON
            with open(timeline_path, 'w') as f:
                json.dump(timeline_data, f, indent=2)
            
            return {
                "success": True,
                "timeline_path": timeline_path,
                "timeline_data": timeline_data,
                "slide_count": slide_count,
                "total_duration": duration
            }
            
        except Exception as e:
            logger.error(f"Error creating timeline: {str(e)}")
            raise
    
    async def _create_bundle(self, bundle_dir: Path, bundle_id: int, title: str) -> Dict[str, any]:
        """Create final ZIP bundle with all processed content"""
        try:
            bundle_path = self.upload_dir / f"bundles" / f"bundle_{bundle_id}.zip"
            bundle_path.parent.mkdir(exist_ok=True)
            
            # Create ZIP bundle
            with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                # Add audio file
                audio_file = bundle_dir / "audio.ogg"
                if audio_file.exists():
                    zipf.write(audio_file, "audio.ogg")
                
                # Add slides directory
                slides_dir = bundle_dir / "slides"
                if slides_dir.exists():
                    for slide_file in slides_dir.iterdir():
                        zipf.write(slide_file, f"slides/{slide_file.name}")
                
                # Add timeline
                timeline_file = bundle_dir / "timeline.json"
                if timeline_file.exists():
                    zipf.write(timeline_file, "timeline.json")
                
                # Add metadata
                metadata = {
                    "bundle_id": bundle_id,
                    "title": title,
                    "created_at": str(bundle_dir.stat().st_mtime),
                    "version": "1.0"
                }
                zipf.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            # Calculate bundle size and checksum
            bundle_size = self._get_file_size(str(bundle_path))
            checksum = self._calculate_checksum(str(bundle_path))
            
            return {
                "success": True,
                "bundle_path": bundle_path,
                "bundle_size": bundle_size,
                "checksum": checksum,
                "file_count": len(zipf.namelist()) if 'zipf' in locals() else 0
            }
            
        except Exception as e:
            logger.error(f"Error creating bundle: {str(e)}")
            raise
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    def _get_directory_size(self, dir_path: str) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(dir_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += self._get_file_size(filepath)
        except OSError:
            pass
        return total_size
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except OSError:
            return ""
    
    async def _detect_slide_changes(self, video_path: str, frame_interval: int) -> List[Dict[str, any]]:
        """Detect slide changes using computer vision techniques"""
        try:
            logger.info("Starting slide change detection...")
            
            # Extract frames at regular intervals
            frames = await self._extract_frames(video_path, frame_interval)
            if len(frames) < 2:
                logger.warning("Not enough frames extracted for change detection")
                return []
            
            # Analyze frame differences to detect slide changes
            slide_transitions = []
            previous_frame = None
            change_threshold = 0.3  # 30% change threshold
            
            for i, frame in enumerate(frames):
                if previous_frame is not None:
                    # Calculate structural similarity between frames
                    similarity = self._calculate_frame_similarity(previous_frame, frame)
                    
                    # If similarity is below threshold, it's likely a slide change
                    if similarity < (1 - change_threshold):
                        timestamp = i * (frame_interval / 30.0)  # Approximate timestamp
                        slide_transitions.append({
                            "timestamp": timestamp,
                            "frame_index": i,
                            "similarity": similarity,
                            "confidence": 1 - similarity
                        })
                        logger.info(f"Slide change detected at {timestamp:.2f}s (similarity: {similarity:.3f})")
                
                previous_frame = frame
            
            logger.info(f"Detected {len(slide_transitions)} slide transitions")
            return slide_transitions
            
        except Exception as e:
            logger.error(f"Error in slide change detection: {str(e)}")
            return []
    
    async def _extract_frames(self, video_path: str, frame_interval: int) -> List[np.ndarray]:
        """Extract frames from video at specified intervals"""
        try:
            frames = []
            temp_dir = tempfile.mkdtemp()
            
            # Use FFmpeg to extract frames
            output_pattern = os.path.join(temp_dir, "frame_%04d.jpg")
            
            # Extract frames at specified intervals
            (
                ffmpeg
                .input(video_path)
                .filter('select', f'not(mod(n,{frame_interval}))')
                .output(output_pattern, vframes=100)  # Limit to 100 frames max
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Load extracted frames
            frame_files = sorted([f for f in os.listdir(temp_dir) if f.startswith('frame_')])
            for frame_file in frame_files:
                frame_path = os.path.join(temp_dir, frame_file)
                frame = cv2.imread(frame_path)
                if frame is not None:
                    # Convert to grayscale for comparison
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    frames.append(gray_frame)
            
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            logger.info(f"Extracted {len(frames)} frames for analysis")
            return frames
            
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            return []
    
    def _calculate_frame_similarity(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """Calculate structural similarity between two frames"""
        try:
            # Resize frames to same size if needed
            if frame1.shape != frame2.shape:
                frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
            
            # Calculate structural similarity index (SSIM)
            # For simplicity, we'll use mean squared error normalized
            mse = np.mean((frame1.astype(float) - frame2.astype(float)) ** 2)
            max_pixel_value = 255.0
            similarity = 1 - (mse / (max_pixel_value ** 2))
            
            return max(0, min(1, similarity))  # Clamp between 0 and 1
            
        except Exception as e:
            logger.error(f"Error calculating frame similarity: {str(e)}")
            return 0.0
    
    async def _create_accurate_timeline(
        self, 
        slide_transitions: List[Dict[str, any]], 
        slide_paths: List[str], 
        duration: float
    ) -> List[Dict[str, any]]:
        """Create accurate timeline using detected slide transitions"""
        try:
            timeline_data = []
            slide_count = len(slide_paths)
            
            # If we have more slides than transitions, distribute remaining slides
            if slide_count > len(slide_transitions) + 1:
                # Use detected transitions for first slides, distribute rest
                for i, transition in enumerate(slide_transitions):
                    if i < slide_count:
                        timeline_entry = {
                            "timestamp": self._format_timestamp(transition["timestamp"]),
                            "slide_path": slide_paths[i],
                            "slide_number": i + 1,
                            "duration": transition["timestamp"] - (slide_transitions[i-1]["timestamp"] if i > 0 else 0),
                            "confidence": transition["confidence"]
                        }
                        timeline_data.append(timeline_entry)
                
                # Distribute remaining slides evenly after last transition
                remaining_slides = slide_count - len(slide_transitions)
                remaining_duration = duration - slide_transitions[-1]["timestamp"]
                slide_duration = remaining_duration / remaining_slides if remaining_slides > 0 else 0
                
                for i in range(len(slide_transitions), slide_count):
                    timestamp = slide_transitions[-1]["timestamp"] + (i - len(slide_transitions) + 1) * slide_duration
                    timeline_entry = {
                        "timestamp": self._format_timestamp(timestamp),
                        "slide_path": slide_paths[i],
                        "slide_number": i + 1,
                        "duration": slide_duration,
                        "confidence": 0.5  # Lower confidence for estimated timing
                    }
                    timeline_data.append(timeline_entry)
            else:
                # Use transitions directly
                for i, transition in enumerate(slide_transitions):
                    if i < slide_count:
                        duration_val = (slide_transitions[i+1]["timestamp"] - transition["timestamp"] 
                                      if i < len(slide_transitions) - 1 
                                      else duration - transition["timestamp"])
                        
                        timeline_entry = {
                            "timestamp": self._format_timestamp(transition["timestamp"]),
                            "slide_path": slide_paths[i],
                            "slide_number": i + 1,
                            "duration": duration_val,
                            "confidence": transition["confidence"]
                        }
                        timeline_data.append(timeline_entry)
            
            logger.info(f"Created accurate timeline with {len(timeline_data)} entries")
            return timeline_data
            
        except Exception as e:
            logger.error(f"Error creating accurate timeline: {str(e)}")
            # Fallback to equal distribution
            slide_count = len(slide_paths)
            slide_duration = duration / slide_count if slide_count > 0 else 0
            
            timeline_data = []
            for i, slide_path in enumerate(slide_paths):
                timestamp = i * slide_duration
                timeline_entry = {
                    "timestamp": self._format_timestamp(timestamp),
                    "slide_path": slide_path,
                    "slide_number": i + 1,
                    "duration": slide_duration,
                    "confidence": 0.3  # Low confidence for fallback
                }
                timeline_data.append(timeline_entry)
            
            return timeline_data

class AudioAnalyzer:
    """Advanced audio analysis for better compression and timeline creation"""
    
    def __init__(self):
        self.silence_threshold = -30  # dB
        self.min_silence_duration = 0.5  # seconds
    
    async def analyze_audio(self, audio_path: str) -> Dict[str, any]:
        """Analyze audio for silence detection and volume levels"""
        try:
            # Use ffmpeg to analyze audio
            probe = ffmpeg.probe(audio_path)
            
            # Get basic audio info
            audio_stream = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
            
            analysis = {
                "duration": float(probe['format']['duration']),
                "bitrate": int(probe['format'].get('bit_rate', 0)),
                "sample_rate": int(audio_stream.get('sample_rate', 0)),
                "channels": int(audio_stream.get('channels', 0)),
                "format": audio_stream.get('codec_name', ''),
                "silence_periods": [],
                "volume_levels": []
            }
            
            # Detect silence periods (simplified implementation)
            # In production, you might use more sophisticated audio analysis
            analysis["silence_periods"] = await self._detect_silence(audio_path)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing audio: {str(e)}")
            return {}
    
    async def _detect_silence(self, audio_path: str) -> List[Dict[str, float]]:
        """Detect silence periods in audio"""
        # This is a simplified implementation
        # In production, you would use more sophisticated audio analysis
        silence_periods = []
        
        try:
            # Use ffmpeg to detect silence
            # This is a placeholder - actual implementation would be more complex
            pass
        except Exception as e:
            logger.warning(f"Could not detect silence: {str(e)}")
        
        return silence_periods
