import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..app.database import get_db
from .models import LectureBundle, ProcessingQueue, SlideTimeline
from .media_processor import MediaProcessor
from .schemas import ProcessingStatus, TaskType, TaskStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """Manages background processing tasks for lecture bundles"""
    
    def __init__(self):
        self.media_processor = MediaProcessor()
        self.active_tasks: Dict[int, asyncio.Task] = {}
    
    async def process_lecture_bundle(self, bundle_id: int, video_path: str, slides_path: str) -> Dict[str, Any]:
        """
        Main background task for processing lecture bundles
        """
        db = next(get_db())
        try:
            logger.info(f"Starting background processing for bundle {bundle_id}")
            
            # Update bundle status
            bundle = db.query(LectureBundle).filter(LectureBundle.id == bundle_id).first()
            if not bundle:
                logger.error(f"Bundle {bundle_id} not found")
                return {"success": False, "error": "Bundle not found"}
            
            bundle.processing_status = ProcessingStatus.PROCESSING
            bundle.processing_progress = 0.0
            db.commit()
            
            # Create processing tasks
            tasks = [
                self._create_processing_task(bundle_id, TaskType.AUDIO_COMPRESSION, {"video_path": video_path}),
                self._create_processing_task(bundle_id, TaskType.SLIDE_OPTIMIZATION, {"slides_path": slides_path}),
                self._create_processing_task(bundle_id, TaskType.TIMELINE_CREATION, {"video_path": video_path}),
                self._create_processing_task(bundle_id, TaskType.BUNDLE_CREATION, {})
            ]
            
            # Process tasks sequentially
            total_tasks = len(tasks)
            completed_tasks = 0
            
            for task in tasks:
                try:
                    # Mark task as running
                    task.task_status = TaskStatus.RUNNING
                    task.started_at = datetime.now()
                    db.commit()
                    
                    # Execute task
                    result = await self._execute_processing_task(task, bundle_id)
                    
                    if result["success"]:
                        task.task_status = TaskStatus.COMPLETED
                        task.task_result = result
                        task.completed_at = datetime.now()
                        completed_tasks += 1
                        
                        # Update bundle progress
                        bundle.processing_progress = completed_tasks / total_tasks
                        db.commit()
                        
                        logger.info(f"Task {task.task_type} completed for bundle {bundle_id}")
                    else:
                        task.task_status = TaskStatus.FAILED
                        task.error_message = result.get("error", "Unknown error")
                        db.commit()
                        
                        logger.error(f"Task {task.task_type} failed for bundle {bundle_id}: {task.error_message}")
                        break
                        
                except Exception as e:
                    task.task_status = TaskStatus.FAILED
                    task.error_message = str(e)
                    db.commit()
                    
                    logger.error(f"Task {task.task_type} failed for bundle {bundle_id}: {str(e)}")
                    break
            
            # Update final bundle status
            if completed_tasks == total_tasks:
                bundle.processing_status = ProcessingStatus.COMPLETED
                bundle.processed_at = datetime.now()
                bundle.processing_progress = 1.0
                
                # Save processing results to bundle
                processing_result = await self.media_processor.process_lecture_bundle(
                    video_path, slides_path, bundle_id, bundle.title
                )
                
                if processing_result["success"]:
                    bundle.compressed_audio_path = processing_result["compressed_audio_path"]
                    bundle.optimized_slides_path = processing_result["optimized_slides_path"]
                    bundle.timeline_json_path = processing_result["timeline_json_path"]
                    bundle.bundle_zip_path = processing_result["bundle_zip_path"]
                    bundle.bundle_size = processing_result["bundle_size"]
                    bundle.audio_duration = processing_result["audio_duration"]
                    bundle.slide_count = processing_result["slide_count"]
                    bundle.compression_ratio = processing_result["compression_ratio"]
                    
                    # Create timeline record
                    timeline = SlideTimeline(
                        bundle_id=bundle_id,
                        timeline_data=processing_result["processing_metadata"]["timeline_creation"]["timeline_data"]
                    )
                    db.add(timeline)
                
                logger.info(f"Bundle {bundle_id} processing completed successfully")
            else:
                bundle.processing_status = ProcessingStatus.FAILED
                bundle.processing_error = f"Failed to complete {total_tasks - completed_tasks} tasks"
                logger.error(f"Bundle {bundle_id} processing failed")
            
            db.commit()
            return {"success": completed_tasks == total_tasks, "completed_tasks": completed_tasks, "total_tasks": total_tasks}
            
        except Exception as e:
            logger.error(f"Error processing bundle {bundle_id}: {str(e)}")
            
            # Update bundle status to failed
            bundle = db.query(LectureBundle).filter(LectureBundle.id == bundle_id).first()
            if bundle:
                bundle.processing_status = ProcessingStatus.FAILED
                bundle.processing_error = str(e)
                db.commit()
            
            return {"success": False, "error": str(e)}
        
        finally:
            db.close()
    
    def _create_processing_task(self, bundle_id: int, task_type: TaskType, parameters: Dict[str, Any]) -> ProcessingQueue:
        """Create a processing task record"""
        db = next(get_db())
        try:
            task = ProcessingQueue(
                bundle_id=bundle_id,
                task_type=task_type,
                task_parameters=parameters,
                task_status=TaskStatus.QUEUED
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return task
        finally:
            db.close()
    
    async def _execute_processing_task(self, task: ProcessingQueue, bundle_id: int) -> Dict[str, Any]:
        """Execute a specific processing task"""
        try:
            if task.task_type == TaskType.AUDIO_COMPRESSION:
                return await self._compress_audio(task, bundle_id)
            elif task.task_type == TaskType.SLIDE_OPTIMIZATION:
                return await self._optimize_slides(task, bundle_id)
            elif task.task_type == TaskType.TIMELINE_CREATION:
                return await self._create_timeline(task, bundle_id)
            elif task.task_type == TaskType.BUNDLE_CREATION:
                return await self._create_bundle(task, bundle_id)
            else:
                return {"success": False, "error": f"Unknown task type: {task.task_type}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _compress_audio(self, task: ProcessingQueue, bundle_id: int) -> Dict[str, Any]:
        """Compress audio from video"""
        try:
            video_path = task.task_parameters["video_path"]
            # This would use the media processor to compress audio
            # For now, return a mock result
            return {
                "success": True,
                "compressed_audio_path": f"audio_{bundle_id}.ogg",
                "duration": 1800.0,  # 30 minutes
                "compressed_size": 5000000  # 5MB
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _optimize_slides(self, task: ProcessingQueue, bundle_id: int) -> Dict[str, Any]:
        """Optimize slide images"""
        try:
            slides_path = task.task_parameters["slides_path"]
            # This would use the media processor to optimize slides
            # For now, return a mock result
            return {
                "success": True,
                "optimized_slides_path": f"slides_{bundle_id}",
                "slide_count": 25,
                "compressed_size": 2000000  # 2MB
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_timeline(self, task: ProcessingQueue, bundle_id: int) -> Dict[str, Any]:
        """Create slide timeline"""
        try:
            video_path = task.task_parameters["video_path"]
            # This would use the media processor to create timeline
            # For now, return a mock result
            timeline_data = [
                {"timestamp": "00:00:00", "slide_path": "slide_001.jpg", "slide_number": 1, "duration": 72.0},
                {"timestamp": "00:01:12", "slide_path": "slide_002.jpg", "slide_number": 2, "duration": 72.0},
                # ... more timeline entries
            ]
            return {
                "success": True,
                "timeline_data": timeline_data,
                "timeline_path": f"timeline_{bundle_id}.json"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_bundle(self, task: ProcessingQueue, bundle_id: int) -> Dict[str, Any]:
        """Create final bundle"""
        try:
            # This would use the media processor to create the final bundle
            # For now, return a mock result
            return {
                "success": True,
                "bundle_path": f"bundle_{bundle_id}.zip",
                "bundle_size": 7000000,  # 7MB
                "compression_ratio": 0.1  # 10:1 compression
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global task manager instance
task_manager = BackgroundTaskManager()

# Background task functions for FastAPI
async def process_lecture_bundle_task(bundle_id: int, video_path: str, slides_path: str):
    """Background task function for processing lecture bundles"""
    await task_manager.process_lecture_bundle(bundle_id, video_path, slides_path)

async def cleanup_old_downloads_task():
    """Background task for cleaning up old downloads"""
    from .download_manager import OfflineContentManager
    manager = OfflineContentManager()
    cleaned_count = await manager.cleanup_old_content(max_age_days=30)
    logger.info(f"Cleaned up {cleaned_count} old downloads")

async def process_pending_bundles():
    """Process any pending bundles in the queue"""
    db = next(get_db())
    try:
        pending_bundles = db.query(LectureBundle).filter(
            LectureBundle.processing_status == ProcessingStatus.PENDING
        ).all()
        
        for bundle in pending_bundles:
            if bundle.original_video_path and bundle.original_slides_path:
                asyncio.create_task(
                    process_lecture_bundle_task(
                        bundle.id,
                        bundle.original_video_path,
                        bundle.original_slides_path
                    )
                )
                logger.info(f"Queued processing for bundle {bundle.id}")
    finally:
        db.close()
