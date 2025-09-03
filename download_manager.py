import asyncio
import aiofiles
import os
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DownloadManager:
    """Manages background downloads and offline content storage"""
    
    def __init__(self, download_dir: str = "downloads", offline_dir: str = "offline"):
        self.download_dir = Path(download_dir)
        self.offline_dir = Path(offline_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.offline_dir.mkdir(exist_ok=True)
        
        # Track active downloads
        self.active_downloads: Dict[int, asyncio.Task] = {}
    
    async def download_bundle(self, download_id: int, bundle_path: str) -> Dict[str, any]:
        """
        Download a lecture bundle in the background
        """
        try:
            logger.info(f"Starting download for bundle {download_id}")
            
            # Create download directory for this bundle
            download_path = self.download_dir / str(download_id)
            download_path.mkdir(exist_ok=True)
            
            # Copy bundle to download directory
            bundle_file = Path(bundle_path)
            if not bundle_file.exists():
                raise FileNotFoundError(f"Bundle file not found: {bundle_path}")
            
            # Simulate download progress (in production, this would be actual network download)
            total_size = bundle_file.stat().st_size
            downloaded_size = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            with open(bundle_file, 'rb') as source:
                with open(download_path / bundle_file.name, 'wb') as dest:
                    while True:
                        chunk = source.read(chunk_size)
                        if not chunk:
                            break
                        
                        dest.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Update progress (in production, this would update database)
                        progress = downloaded_size / total_size
                        logger.info(f"Download {download_id} progress: {progress:.2%}")
                        
                        # Simulate network delay
                        await asyncio.sleep(0.1)
            
            # Extract bundle for offline access
            await self._extract_bundle_for_offline(download_id, download_path / bundle_file.name)
            
            logger.info(f"Download completed for bundle {download_id}")
            return {
                "success": True,
                "download_id": download_id,
                "downloaded_size": downloaded_size,
                "total_size": total_size,
                "offline_path": str(self.offline_dir / str(download_id))
            }
            
        except Exception as e:
            logger.error(f"Error downloading bundle {download_id}: {str(e)}")
            return {
                "success": False,
                "download_id": download_id,
                "error": str(e)
            }
    
    async def _extract_bundle_for_offline(self, download_id: int, bundle_file: Path) -> None:
        """
        Extract bundle contents for offline access
        """
        try:
            offline_path = self.offline_dir / str(download_id)
            offline_path.mkdir(exist_ok=True)
            
            # Extract ZIP bundle
            with zipfile.ZipFile(bundle_file, 'r') as zip_ref:
                zip_ref.extractall(offline_path)
            
            logger.info(f"Bundle {download_id} extracted for offline access")
            
        except Exception as e:
            logger.error(f"Error extracting bundle {download_id}: {str(e)}")
            raise
    
    async def get_offline_content(self, download_id: int) -> Optional[Dict[str, str]]:
        """
        Get offline content paths for a downloaded bundle
        """
        offline_path = self.offline_dir / str(download_id)
        if not offline_path.exists():
            return None
        
        content_paths = {}
        
        # Find audio file
        audio_files = list(offline_path.glob("*.ogg")) + list(offline_path.glob("*.mp3"))
        if audio_files:
            content_paths["audio"] = str(audio_files[0])
        
        # Find slides directory
        slides_dir = offline_path / "slides"
        if slides_dir.exists():
            content_paths["slides"] = str(slides_dir)
        
        # Find timeline file
        timeline_file = offline_path / "timeline.json"
        if timeline_file.exists():
            content_paths["timeline"] = str(timeline_file)
        
        # Find metadata file
        metadata_file = offline_path / "metadata.json"
        if metadata_file.exists():
            content_paths["metadata"] = str(metadata_file)
        
        return content_paths
    
    async def cleanup_download(self, download_id: int) -> bool:
        """
        Clean up download files
        """
        try:
            download_path = self.download_dir / str(download_id)
            offline_path = self.offline_dir / str(download_id)
            
            if download_path.exists():
                shutil.rmtree(download_path)
            
            if offline_path.exists():
                shutil.rmtree(offline_path)
            
            logger.info(f"Cleaned up download {download_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up download {download_id}: {str(e)}")
            return False
    
    async def get_download_status(self, download_id: int) -> Dict[str, any]:
        """
        Get current download status
        """
        if download_id in self.active_downloads:
            task = self.active_downloads[download_id]
            if task.done():
                try:
                    result = await task
                    return {
                        "status": "completed" if result["success"] else "failed",
                        "result": result
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "error": str(e)
                    }
            else:
                return {"status": "downloading"}
        else:
            # Check if download exists in offline directory
            offline_path = self.offline_dir / str(download_id)
            if offline_path.exists():
                return {"status": "completed"}
            else:
                return {"status": "not_found"}

class OfflineContentManager:
    """Manages offline content access and synchronization"""
    
    def __init__(self, offline_dir: str = "offline"):
        self.offline_dir = Path(offline_dir)
        self.offline_dir.mkdir(exist_ok=True)
    
    async def get_lecture_content(self, download_id: int) -> Optional[Dict[str, any]]:
        """
        Get all content for an offline lecture
        """
        offline_path = self.offline_dir / str(download_id)
        if not offline_path.exists():
            return None
        
        content = {
            "download_id": download_id,
            "offline_path": str(offline_path),
            "available": True,
            "content": {}
        }
        
        # Load metadata
        metadata_file = offline_path / "metadata.json"
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r') as f:
                content["metadata"] = json.load(f)
        
        # Load timeline
        timeline_file = offline_path / "timeline.json"
        if timeline_file.exists():
            import json
            with open(timeline_file, 'r') as f:
                content["timeline"] = json.load(f)
        
        # Get audio file
        audio_files = list(offline_path.glob("*.ogg")) + list(offline_path.glob("*.mp3"))
        if audio_files:
            content["audio_file"] = str(audio_files[0])
        
        # Get slides
        slides_dir = offline_path / "slides"
        if slides_dir.exists():
            slide_files = sorted(slides_dir.glob("*.jpg")) + sorted(slides_dir.glob("*.png"))
            content["slides"] = [str(f) for f in slide_files]
        
        return content
    
    async def is_content_available(self, download_id: int) -> bool:
        """
        Check if offline content is available
        """
        offline_path = self.offline_dir / str(download_id)
        return offline_path.exists()
    
    async def get_content_size(self, download_id: int) -> int:
        """
        Get total size of offline content
        """
        offline_path = self.offline_dir / str(download_id)
        if not offline_path.exists():
            return 0
        
        total_size = 0
        for file_path in offline_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size
    
    async def cleanup_old_content(self, max_age_days: int = 30) -> int:
        """
        Clean up old offline content
        """
        cleaned_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        
        for item in self.offline_dir.iterdir():
            if item.is_dir():
                # Check if directory is older than max_age_days
                if item.stat().st_mtime < cutoff_time:
                    try:
                        shutil.rmtree(item)
                        cleaned_count += 1
                        logger.info(f"Cleaned up old offline content: {item.name}")
                    except Exception as e:
                        logger.error(f"Error cleaning up {item.name}: {str(e)}")
        
        return cleaned_count
