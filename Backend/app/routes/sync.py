"""
Offline sync routes for GramOthi
Provides endpoints for offline activity storage, synchronization, and conflict resolution
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import get_db
from ..models import User
from ..schemas import (
    OfflineActivityCreate, OfflineActivityResponse, OfflineSyncRequest,
    OfflineSyncResponse, ConflictResolutionRequest
)
from ..routes.auth import get_current_user
from ..services.sync_service import OfflineSyncService
from datetime import datetime, timezone
import logging
from sqlalchemy import and_

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["offline-sync"])

# Offline Activity Storage
@router.post("/activities", response_model=OfflineActivityResponse)
def store_offline_activity(
    activity_type: str,
    activity_data: Dict[str, Any],
    offline_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Store an offline activity for later synchronization."""
    # Validate activity type
    valid_types = [
        "slide_progress", "recording_progress", "quiz_response",
        "learning_session", "student_progress"
    ]
    
    if activity_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid activity type. Must be one of: {valid_types}"
        )
    
    # Validate required fields based on activity type
    if not OfflineSyncService._validate_activity_data(activity_type, activity_data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid activity data for type: {activity_type}"
        )
    
    # Add timestamp to activity data
    activity_data["created_at"] = datetime.now(timezone.utc).isoformat()
    
    offline_activity = OfflineSyncService.store_offline_activity(
        db, current_user.id, activity_type, activity_data, offline_id
    )
    
    return offline_activity

@router.get("/activities", response_model=List[OfflineActivityResponse])
def get_offline_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all offline activities for the current user."""
    from ..models import OfflineActivity
    
    activities = db.query(OfflineActivity).filter(
        OfflineActivity.user_id == current_user.id
    ).order_by(OfflineActivity.created_at.desc()).all()
    
    return activities

# Synchronization
@router.post("/sync", response_model=OfflineSyncResponse)
def sync_offline_activities(
    sync_request: OfflineSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Synchronize offline activities with the server."""
    if not sync_request.activities:
        return OfflineSyncResponse(
            success=True,
            message="No activities to sync",
            synced_count=0,
            conflict_count=0,
            conflicts=[],
            server_activities=[]
        )
    
    # Validate all activities belong to the current user
    for activity in sync_request.activities:
        if not OfflineSyncService._validate_activity_data(activity.activity_type, activity.activity_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid activity data for type: {activity.activity_type}"
            )
    
    # Perform synchronization
    result = OfflineSyncService.sync_offline_activities(
        db, current_user.id, sync_request.device_id, sync_request.activities
    )
    
    return result

# Conflict Resolution
@router.post("/conflicts/{activity_id}/resolve")
def resolve_sync_conflict(
    activity_id: int,
    resolution: str,
    client_data: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve a sync conflict."""
    # Validate resolution type
    valid_resolutions = ["server_wins", "client_wins", "manual"]
    if resolution not in valid_resolutions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resolution. Must be one of: {valid_resolutions}"
        )
    
    # Validate manual resolution has client data
    if resolution == "manual" and not client_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manual resolution requires client data"
        )
    
    success = OfflineSyncService.resolve_conflict(
        db, current_user.id, activity_id, resolution, client_data
    )
    
    if success:
        return {
            "message": f"Conflict resolved using {resolution} strategy",
            "activity_id": activity_id,
            "resolution": resolution
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offline activity not found"
        )

@router.get("/conflicts")
def get_sync_conflicts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all sync conflicts for the current user."""
    from ..models import OfflineActivity
    
    conflicts = db.query(OfflineActivity).filter(
        and_(
            OfflineActivity.user_id == current_user.id,
            OfflineActivity.sync_status == "conflict"
        )
    ).order_by(OfflineActivity.created_at.desc()).all()
    
    return {
        "user_id": current_user.id,
        "total_conflicts": len(conflicts),
        "conflicts": [
            {
                "id": conflict.id,
                "activity_type": conflict.activity_type,
                "activity_data": conflict.activity_data,
                "offline_id": conflict.offline_id,
                "created_at": conflict.created_at,
                "conflict_resolution": conflict.conflict_resolution,
                "retry_count": conflict.retry_count
            }
            for conflict in conflicts
        ]
    }

# Sync Status and Management
@router.get("/status")
def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get synchronization status for the current user."""
    status_info = OfflineSyncService.get_sync_status(db, current_user.id)
    return status_info

@router.post("/retry")
def retry_failed_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retry failed offline activities."""
    result = OfflineSyncService.retry_failed_activities(db, current_user.id)
    
    return {
        "message": f"Retry completed. {result['successful']} successful, {result['still_failed']} still failed",
        "details": result
    }

# Bulk Operations
@router.post("/bulk-store")
def bulk_store_offline_activities(
    activities: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Store multiple offline activities at once."""
    stored_activities = []
    errors = []
    
    for i, activity_data in enumerate(activities):
        try:
            activity_type = activity_data.get("activity_type")
            offline_id = activity_data.get("offline_id")
            data = activity_data.get("activity_data", {})
            
            if not activity_type or not offline_id:
                errors.append({
                    "index": i,
                    "error": "Missing activity_type or offline_id"
                })
                continue
            
            # Validate activity data
            if not OfflineSyncService._validate_activity_data(activity_type, data):
                errors.append({
                    "index": i,
                    "error": f"Invalid activity data for type: {activity_type}"
                })
                continue
            
            # Add timestamp
            data["created_at"] = datetime.now(timezone.utc).isoformat()
            
            # Store activity
            offline_activity = OfflineSyncService.store_offline_activity(
                db, current_user.id, activity_type, data, offline_id
            )
            
            stored_activities.append(offline_activity)
            
        except Exception as e:
            errors.append({
                "index": i,
                "error": str(e)
            })
    
    return {
        "message": f"Bulk store completed. {len(stored_activities)} stored, {len(errors)} errors",
        "stored_count": len(stored_activities),
        "error_count": len(errors),
        "stored_activities": stored_activities,
        "errors": errors
    }

# Sync History
@router.get("/history")
def get_sync_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get synchronization history for the current user."""
    from ..models import SyncSession
    
    sync_sessions = db.query(SyncSession).filter(
        SyncSession.user_id == current_user.id
    ).order_by(SyncSession.session_start.desc()).limit(20).all()
    
    return {
        "user_id": current_user.id,
        "total_sessions": len(sync_sessions),
        "sessions": [
            {
                "id": session.id,
                "device_id": session.device_id,
                "session_start": session.session_start,
                "session_end": session.session_end,
                "activities_synced": session.activities_synced,
                "conflicts_resolved": session.conflicts_resolved,
                "sync_status": session.sync_status,
                "last_activity_at": session.last_activity_at
            }
            for session in sync_sessions
        ]
    }

# Device Management
@router.get("/devices")
def get_sync_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all devices used for synchronization by the current user."""
    from ..models import SyncSession
    
    # Get unique devices from sync sessions
    devices = db.query(SyncSession.device_id).filter(
        SyncSession.user_id == current_user.id
    ).distinct().all()
    
    device_list = []
    for device in devices:
        device_id = device[0]
        
        # Get latest sync session for this device
        latest_session = db.query(SyncSession).filter(
            and_(
                SyncSession.user_id == current_user.id,
                SyncSession.device_id == device_id
            )
        ).order_by(SyncSession.session_start.desc()).first()
        
        # Get pending activities for this device
        from ..models import OfflineActivity
        pending_count = db.query(OfflineActivity).filter(
            and_(
                OfflineActivity.user_id == current_user.id,
                OfflineActivity.sync_status == "pending"
            )
        ).count()
        
        device_list.append({
            "device_id": device_id,
            "last_sync": latest_session.session_start if latest_session else None,
            "last_sync_status": latest_session.sync_status if latest_session else None,
            "pending_activities": pending_count
        })
    
    return {
        "user_id": current_user.id,
        "total_devices": len(device_list),
        "devices": device_list
    }

# Cleanup and Maintenance
@router.delete("/activities/cleanup")
def cleanup_old_activities(
    days_old: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up old synced offline activities."""
    from ..models import OfflineActivity
    from datetime import timedelta
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
    
    # Get old synced activities
    old_activities = db.query(OfflineActivity).filter(
        and_(
            OfflineActivity.user_id == current_user.id,
            OfflineActivity.sync_status == "synced",
            OfflineActivity.synced_at < cutoff_date
        )
    ).all()
    
    deleted_count = 0
    for activity in old_activities:
        db.delete(activity)
        deleted_count += 1
    
    db.commit()
    
    return {
        "message": f"Cleaned up {deleted_count} old synced activities",
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat()
    }

# Health Check
@router.get("/health")
def sync_health_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check the health of the sync system for the current user."""
    status_info = OfflineSyncService.get_sync_status(db, current_user.id)
    
    # Check for any critical issues
    critical_issues = []
    
    if status_info["failed_activities"] > 10:
        critical_issues.append("High number of failed activities")
    
    if status_info["conflicted_activities"] > 5:
        critical_issues.append("Multiple sync conflicts detected")
    
    # Get last sync info
    from ..models import SyncSession
    last_sync = db.query(SyncSession).filter(
        SyncSession.user_id == current_user.id
    ).order_by(SyncSession.session_start.desc()).first()
    
    if last_sync and last_sync.sync_status == "failed":
        critical_issues.append("Last sync session failed")
    
    return {
        "user_id": current_user.id,
        "sync_status": "healthy" if not critical_issues else "unhealthy",
        "critical_issues": critical_issues,
        "status_details": status_info,
        "last_sync": {
            "session_start": last_sync.session_start if last_sync else None,
            "session_end": last_sync.session_end if last_sync else None,
            "status": last_sync.sync_status if last_sync else None
        }
    }
