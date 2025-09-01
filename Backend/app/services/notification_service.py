"""
Push notification service for GramOthi
Handles scheduled notifications, push delivery, and notification management
"""

import os
import json
import requests
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from ..models import (
    User, PushToken, NotificationPreference, ScheduledEvent, 
    ScheduledNotification, NotificationLog, Class
)
from ..schemas import (
    PushNotificationRequest, PushNotificationResponse,
    ScheduledEventNotificationRequest
)
import asyncio
import aiohttp
from celery import Celery

logger = logging.getLogger(__name__)

# Initialize Celery for background tasks
celery_app = Celery('gramothi_notifications')
celery_app.config_from_object('celeryconfig')

class PushNotificationService:
    """Service for managing push notifications."""
    
    # Push service configurations
    FIREBASE_SERVER_KEY = os.getenv("FIREBASE_SERVER_KEY", "")
    FIREBASE_API_URL = "https://fcm.googleapis.com/fcm/send"
    
    # Web push configuration
    VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
    VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
    
    @staticmethod
    def register_push_token(db: Session, user_id: int, token: str, 
                           platform: str, device_id: str = None) -> PushToken:
        """Register or update a push token for a user."""
        # Check if token already exists
        existing_token = db.query(PushToken).filter(
            and_(
                PushToken.token == token,
                PushToken.user_id == user_id
            )
        ).first()
        
        if existing_token:
            # Update existing token
            existing_token.platform = platform
            existing_token.device_id = device_id
            existing_token.last_used = datetime.now(timezone.utc)
            existing_token.is_active = True
            db.commit()
            db.refresh(existing_token)
            return existing_token
        
        # Create new token
        push_token = PushToken(
            user_id=user_id,
            token=token,
            platform=platform,
            device_id=device_id
        )
        db.add(push_token)
        db.commit()
        db.refresh(push_token)
        return push_token
    
    @staticmethod
    def unregister_push_token(db: Session, user_id: int, token: str) -> bool:
        """Unregister a push token for a user."""
        push_token = db.query(PushToken).filter(
            and_(
                PushToken.token == token,
                PushToken.user_id == user_id
            )
        ).first()
        
        if push_token:
            push_token.is_active = False
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_user_push_tokens(db: Session, user_id: int) -> List[PushToken]:
        """Get all active push tokens for a user."""
        return db.query(PushToken).filter(
            and_(
                PushToken.user_id == user_id,
                PushToken.is_active == True
            )
        ).all()
    
    @staticmethod
    def send_push_notification(db: Session, user_ids: List[int], title: str, 
                             body: str, data: Dict[str, Any] = None) -> PushNotificationResponse:
        """Send push notification to multiple users."""
        success_count = 0
        failed_count = 0
        failed_users = []
        
        for user_id in user_ids:
            try:
                # Get user's push tokens
                push_tokens = PushNotificationService.get_user_push_tokens(db, user_id)
                
                if not push_tokens:
                    failed_count += 1
                    failed_users.append(user_id)
                    continue
                
                # Send to each platform
                for token in push_tokens:
                    success = PushNotificationService._send_to_platform(
                        db, user_id, token, title, body, data
                    )
                    
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_users.append(user_id)
                        break
                        
            except Exception as e:
                logger.error(f"Failed to send notification to user {user_id}: {e}")
                failed_count += 1
                failed_users.append(user_id)
        
        return PushNotificationResponse(
            success=success_count > 0,
            message=f"Sent {success_count} notifications, {failed_count} failed",
            sent_count=success_count,
            failed_count=failed_count,
            failed_users=failed_users
        )
    
    @staticmethod
    def _send_to_platform(db: Session, user_id: int, token: PushToken, 
                          title: str, body: str, data: Dict[str, Any] = None) -> bool:
        """Send notification to a specific platform."""
        try:
            if token.platform == "android" or token.platform == "ios":
                return PushNotificationService._send_firebase_notification(
                    db, user_id, token, title, body, data
                )
            elif token.platform == "web":
                return PushNotificationService._send_web_push_notification(
                    db, user_id, token, title, body, data
                )
            else:
                logger.warning(f"Unsupported platform: {token.platform}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send {token.platform} notification: {e}")
            return False
    
    @staticmethod
    def _send_firebase_notification(db: Session, user_id: int, token: PushToken,
                                   title: str, body: str, data: Dict[str, Any] = None) -> bool:
        """Send notification via Firebase Cloud Messaging."""
        if not PushNotificationService.FIREBASE_SERVER_KEY:
            logger.error("Firebase server key not configured")
            return False
        
        # Prepare notification payload
        notification_data = {
            "to": token.token,
            "notification": {
                "title": title,
                "body": body,
                "sound": "default",
                "badge": "1"
            },
            "data": data or {},
            "priority": "high"
        }
        
        headers = {
            "Authorization": f"key={PushNotificationService.FIREBASE_SERVER_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                PushNotificationService.FIREBASE_API_URL,
                json=notification_data,
                headers=headers,
                timeout=10
            )
            
            success = response.status_code == 200
            response_data = response.json() if response.text else {}
            
            # Log the notification
            PushNotificationService._log_notification(
                db, user_id, "push", title, body, data, token.platform,
                "delivered" if success else "failed",
                json.dumps(response_data)
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Firebase notification failed: {e}")
            PushNotificationService._log_notification(
                db, user_id, "push", title, body, data, token.platform,
                "failed", str(e)
            )
            return False
    
    @staticmethod
    def _send_web_push_notification(db: Session, user_id: int, token: PushToken,
                                   title: str, body: str, data: Dict[str, Any] = None) -> bool:
        """Send web push notification."""
        # This would integrate with a web push service like web-push library
        # For now, we'll log it as a placeholder
        logger.info(f"Web push notification to user {user_id}: {title}")
        
        PushNotificationService._log_notification(
            db, user_id, "web_push", title, body, data, token.platform,
            "sent", "Web push service not implemented"
        )
        
        return True
    
    @staticmethod
    def _log_notification(db: Session, user_id: int, notification_type: str,
                          title: str, body: str, data: Dict[str, Any],
                          platform: str, delivery_status: str, device_response: str):
        """Log notification for tracking and debugging."""
        notification_log = NotificationLog(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data,
            platform=platform,
            delivery_status=delivery_status,
            device_response=device_response
        )
        
        db.add(notification_log)
        db.commit()

class ScheduledNotificationService:
    """Service for managing scheduled notifications."""
    
    @staticmethod
    def create_scheduled_event(db: Session, class_id: int, event_type: str,
                             title: str, description: str, scheduled_at: datetime,
                             duration_minutes: int = 60, is_recurring: bool = False,
                             recurrence_pattern: Dict[str, Any] = None) -> ScheduledEvent:
        """Create a new scheduled event."""
        scheduled_event = ScheduledEvent(
            class_id=class_id,
            event_type=event_type,
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            is_recurring=is_recurring,
            recurrence_pattern=recurrence_pattern
        )
        
        db.add(scheduled_event)
        db.commit()
        db.refresh(scheduled_event)
        
        # Schedule notifications for this event
        ScheduledNotificationService._schedule_event_notifications(db, scheduled_event)
        
        return scheduled_event
    
    @staticmethod
    def _schedule_event_notifications(db: Session, scheduled_event: ScheduledEvent):
        """Schedule notifications for a scheduled event."""
        # Get all students in the class
        students = db.query(User).filter(
            and_(
                User.role == "student",
                # This could be enhanced with enrollment logic
                User.id.in_(
                    db.query(Class.id).filter(Class.id == scheduled_event.class_id)
                )
            )
        ).all()
        
        # Create notification preferences if they don't exist
        for student in students:
            ScheduledNotificationService._ensure_notification_preferences(db, student.id)
        
        # Schedule different types of notifications
        notification_types = ["reminder", "start", "end"]
        
        for notification_type in notification_types:
            if notification_type == "reminder":
                # Schedule reminder 15 minutes before
                scheduled_time = scheduled_event.scheduled_at - timedelta(minutes=15)
            elif notification_type == "start":
                scheduled_time = scheduled_event.scheduled_at
            else:  # end
                scheduled_time = scheduled_event.scheduled_at + timedelta(minutes=scheduled_event.duration_minutes)
            
            # Only schedule future notifications
            if scheduled_time > datetime.now(timezone.utc):
                for student in students:
                    scheduled_notification = ScheduledNotification(
                        scheduled_event_id=scheduled_event.id,
                        user_id=student.id,
                        notification_type=notification_type,
                        scheduled_at=scheduled_time
                    )
                    db.add(scheduled_notification)
        
        db.commit()
    
    @staticmethod
    def _ensure_notification_preferences(db: Session, user_id: int):
        """Ensure user has default notification preferences."""
        default_preferences = [
            ("quiz_reminder", True, 15),
            ("live_session", True, 15),
            ("achievement", True, 0),
            ("general", True, 0)
        ]
        
        for pref_type, is_enabled, reminder_minutes in default_preferences:
            existing = db.query(NotificationPreference).filter(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.notification_type == pref_type
                )
            ).first()
            
            if not existing:
                preference = NotificationPreference(
                    user_id=user_id,
                    notification_type=pref_type,
                    is_enabled=is_enabled,
                    reminder_minutes=reminder_minutes
                )
                db.add(preference)
        
        db.commit()
    
    @staticmethod
    def get_pending_notifications(db: Session) -> List[ScheduledNotification]:
        """Get all pending notifications that should be sent now."""
        now = datetime.now(timezone.utc)
        
        return db.query(ScheduledNotification).filter(
            and_(
                ScheduledNotification.status == "pending",
                ScheduledNotification.scheduled_at <= now
            )
        ).all()
    
    @staticmethod
    def process_pending_notifications(db: Session) -> Dict[str, int]:
        """Process all pending notifications."""
        pending_notifications = ScheduledNotificationService.get_pending_notifications(db)
        
        processed_count = 0
        success_count = 0
        failed_count = 0
        
        for notification in pending_notifications:
            try:
                # Get event details
                scheduled_event = db.query(ScheduledEvent).filter(
                    ScheduledEvent.id == notification.scheduled_event_id
                ).first()
                
                if not scheduled_event:
                    notification.status = "failed"
                    notification.error_message = "Event not found"
                    db.commit()
                    failed_count += 1
                    continue
                
                # Prepare notification content
                title, body = ScheduledNotificationService._prepare_notification_content(
                    notification, scheduled_event
                )
                
                # Send notification
                result = PushNotificationService.send_push_notification(
                    db, [notification.user_id], title, body
                )
                
                # Update notification status
                if result.success:
                    notification.status = "sent"
                    notification.sent_at = datetime.now(timezone.utc)
                    success_count += 1
                else:
                    notification.status = "failed"
                    notification.error_message = "Failed to send"
                    failed_count += 1
                
                processed_count += 1
                db.commit()
                
            except Exception as e:
                logger.error(f"Failed to process notification {notification.id}: {e}")
                notification.status = "failed"
                notification.error_message = str(e)
                notification.retry_count += 1
                db.commit()
                failed_count += 1
        
        return {
            "processed": processed_count,
            "success": success_count,
            "failed": failed_count
        }
    
    @staticmethod
    def _prepare_notification_content(notification: ScheduledNotification, 
                                    event: ScheduledEvent) -> Tuple[str, str]:
        """Prepare notification title and body based on type and event."""
        if notification.notification_type == "reminder":
            title = f"⏰ Reminder: {event.title}"
            body = f"Starting in 15 minutes. Get ready for your {event.event_type}!"
        elif notification.notification_type == "start":
            title = f"🚀 {event.title} is starting now!"
            body = f"Join your {event.event_type} session."
        else:  # end
            title = f"✅ {event.title} has ended"
            body = f"Thank you for participating in the {event.event_type}."
        
        return title, body
    
    @staticmethod
    def schedule_quiz_notification(db: Session, quiz_id: int, scheduled_at: datetime,
                                 user_ids: List[int] = None) -> bool:
        """Schedule notifications for a quiz."""
        try:
            # Get quiz details
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if not quiz:
                return False
            
            # Create scheduled event
            scheduled_event = ScheduledNotificationService.create_scheduled_event(
                db=db,
                class_id=quiz.class_id,
                event_type="quiz",
                title=f"Quiz: {quiz.question[:50]}...",
                description="Time to test your knowledge!",
                scheduled_at=scheduled_at,
                duration_minutes=quiz.duration_minutes
            )
            
            # Update quiz with scheduled info
            quiz.scheduled_at = scheduled_at
            quiz.is_scheduled = True
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule quiz notification: {e}")
            return False
    
    @staticmethod
    def schedule_live_session_notification(db: Session, class_id: int, title: str,
                                        scheduled_start: datetime, duration_minutes: int = 60) -> bool:
        """Schedule notifications for a live session."""
        try:
            scheduled_event = ScheduledNotificationService.create_scheduled_event(
                db=db,
                class_id=class_id,
                event_type="live_session",
                title=title,
                description="Join your live classroom session",
                scheduled_at=scheduled_start,
                duration_minutes=duration_minutes
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule live session notification: {e}")
            return False

class NotificationPreferenceService:
    """Service for managing user notification preferences."""
    
    @staticmethod
    def update_preference(db: Session, user_id: int, notification_type: str,
                         is_enabled: bool, reminder_minutes: int = 15) -> NotificationPreference:
        """Update user's notification preference."""
        preference = db.query(NotificationPreference).filter(
            and_(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == notification_type
            )
        ).first()
        
        if preference:
            preference.is_enabled = is_enabled
            preference.reminder_minutes = reminder_minutes
            preference.updated_at = datetime.now(timezone.utc)
        else:
            preference = NotificationPreference(
                user_id=user_id,
                notification_type=notification_type,
                is_enabled=is_enabled,
                reminder_minutes=reminder_minutes
            )
            db.add(preference)
        
        db.commit()
        db.refresh(preference)
        return preference
    
    @staticmethod
    def get_user_preferences(db: Session, user_id: int) -> List[NotificationPreference]:
        """Get all notification preferences for a user."""
        return db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).all()
    
    @staticmethod
    def is_notification_enabled(db: Session, user_id: int, notification_type: str) -> bool:
        """Check if a specific notification type is enabled for a user."""
        preference = db.query(NotificationPreference).filter(
            and_(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == notification_type
            )
        ).first()
        
        return preference.is_enabled if preference else True  # Default to enabled

# Celery tasks for background processing

@celery_app.task
def process_scheduled_notifications():
    """Background task to process scheduled notifications."""
    from ..database import get_db
    
    db = next(get_db())
    try:
        result = ScheduledNotificationService.process_pending_notifications(db)
        logger.info(f"Processed notifications: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to process notifications: {e}")
        return {"error": str(e)}
    finally:
        db.close()

@celery_app.task
def send_bulk_notifications(user_ids: List[int], title: str, body: str, data: Dict[str, Any] = None):
    """Background task to send bulk notifications."""
    from ..database import get_db
    
    db = next(get_db())
    try:
        result = PushNotificationService.send_push_notification(db, user_ids, title, body, data)
        logger.info(f"Bulk notification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to send bulk notifications: {e}")
        return {"error": str(e)}
    finally:
        db.close()
