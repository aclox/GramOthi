from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Class schemas
class ClassBase(BaseModel):
    title: str

class ClassCreate(ClassBase):
    pass

class ClassResponse(ClassBase):
    id: int
    teacher_id: int
    created_at: datetime
    teacher: UserResponse
    
    class Config:
        from_attributes = True

# Slide schemas
class SlideBase(BaseModel):
    file_url: str
    order_no: int = 1

class SlideCreate(SlideBase):
    class_id: int

class SlideResponse(SlideBase):
    id: int
    class_id: int
    
    class Config:
        from_attributes = True

# Recording schemas
class RecordingBase(BaseModel):
    audio_url: str
    bundle_url: Optional[str] = None

class RecordingCreate(RecordingBase):
    class_id: int

class RecordingResponse(RecordingBase):
    id: int
    class_id: int
    
    class Config:
        from_attributes = True

# Quiz schemas
class QuizBase(BaseModel):
    question: str
    options: List[str]
    correct_option: int
    points: int = 1
    scheduled_at: Optional[datetime] = None
    duration_minutes: int = 30
    is_scheduled: bool = False

class QuizCreate(QuizBase):
    class_id: int

class QuizResponse(QuizBase):
    id: int
    class_id: int
    
    class Config:
        from_attributes = True

# Response schemas
class ResponseBase(BaseModel):
    answer: int

class ResponseCreate(ResponseBase):
    quiz_id: int

class ResponseResponse(ResponseBase):
    id: int
    quiz_id: int
    student_id: int
    timestamp: datetime
    is_correct: bool
    points_earned: int
    
    class Config:
        from_attributes = True

# Live session schemas
class LiveSessionBase(BaseModel):
    class_id: int
    is_active: bool = True
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    title: Optional[str] = None
    is_scheduled: bool = False

class LiveSessionCreate(LiveSessionBase):
    pass

class LiveSessionResponse(LiveSessionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Poll schemas
class PollBase(BaseModel):
    question: str
    options: List[str]
    is_active: bool = True

class PollCreate(PollBase):
    class_id: int

class PollResponse(PollBase):
    id: int
    class_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PollVote(BaseModel):
    poll_id: int
    option_index: int

# Discussion schemas
class DiscussionPostBase(BaseModel):
    content: str
    parent_id: Optional[int] = None

class DiscussionPostCreate(DiscussionPostBase):
    class_id: int

class DiscussionPostResponse(DiscussionPostBase):
    id: int
    class_id: int
    author_id: int
    created_at: datetime
    author: UserResponse
    
    class Config:
        from_attributes = True

# Progress Tracking Schemas

class LearningObjectiveBase(BaseModel):
    title: str
    description: Optional[str] = None
    order_no: int = 1
    is_required: bool = True

class LearningObjectiveCreate(LearningObjectiveBase):
    class_id: int

class LearningObjectiveResponse(LearningObjectiveBase):
    id: int
    class_id: int
    
    class Config:
        from_attributes = True

class StudentProgressBase(BaseModel):
    status: str = "not_started"  # not_started, in_progress, completed, failed
    progress_percentage: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None

class StudentProgressCreate(StudentProgressBase):
    student_id: int
    class_id: int
    learning_objective_id: Optional[int] = None

class StudentProgressResponse(StudentProgressBase):
    id: int
    student_id: int
    class_id: int
    learning_objective_id: Optional[int] = None
    student: UserResponse
    class_: ClassResponse
    learning_objective: Optional[LearningObjectiveResponse] = None
    
    class Config:
        from_attributes = True

class SlideProgressBase(BaseModel):
    status: str = "not_viewed"  # not_viewed, viewed, completed
    time_spent: int = 0
    viewed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class SlideProgressCreate(SlideProgressBase):
    student_id: int
    slide_id: int

class SlideProgressResponse(SlideProgressBase):
    id: int
    student_id: int
    slide_id: int
    slide: SlideResponse
    
    class Config:
        from_attributes = True

class RecordingProgressBase(BaseModel):
    status: str = "not_listened"  # not_listened, listening, completed
    time_listened: int = 0
    total_duration: Optional[int] = None
    progress_percentage: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class RecordingProgressCreate(RecordingProgressBase):
    student_id: int
    recording_id: int

class RecordingProgressResponse(RecordingProgressBase):
    id: int
    student_id: int
    recording_id: int
    recording: RecordingResponse
    
    class Config:
        from_attributes = True

class LearningSessionBase(BaseModel):
    class_id: int
    session_type: str  # live, recorded, self_study
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_minutes: int = 0
    activities_completed: int = 0
    engagement_score: float = 0.0

class LearningSessionCreate(LearningSessionBase):
    pass

class LearningSessionResponse(LearningSessionBase):
    id: int
    student_id: int
    student: UserResponse
    
    class Config:
        from_attributes = True

class SessionAttendanceBase(BaseModel):
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    duration_minutes: int = 0
    participation_level: str = "passive"  # passive, active, very_active

class SessionAttendanceCreate(SessionAttendanceBase):
    student_id: int
    live_session_id: int

class SessionAttendanceResponse(SessionAttendanceBase):
    id: int
    student_id: int
    live_session_id: int
    student: UserResponse
    
    class Config:
        from_attributes = True

class AchievementBase(BaseModel):
    achievement_type: str
    title: str
    description: Optional[str] = None
    points_awarded: int = 0

class AchievementCreate(AchievementBase):
    student_id: int

class AchievementResponse(AchievementBase):
    id: int
    student_id: int
    earned_at: datetime
    student: UserResponse
    
    class Config:
        from_attributes = True

class PerformanceAnalyticsBase(BaseModel):
    total_points: int = 0
    quizzes_taken: int = 0
    quizzes_passed: int = 0
    average_score: float = 0.0
    total_study_time: int = 0
    attendance_rate: float = 0.0
    engagement_score: float = 0.0
    last_updated: Optional[datetime] = None

class PerformanceAnalyticsResponse(PerformanceAnalyticsBase):
    id: int
    student_id: int
    class_id: int
    student: UserResponse
    class_: ClassResponse
    
    class Config:
        from_attributes = True

# Progress Summary Schemas

class StudentProgressSummary(BaseModel):
    """Summary of student progress across all classes."""
    student_id: int
    student_name: str
    total_classes: int
    completed_classes: int
    total_points: int
    average_score: float
    total_study_time_hours: float
    overall_attendance_rate: float
    achievements_count: int
    current_streak_days: int
    
    class Config:
        from_attributes = True

class ClassProgressSummary(BaseModel):
    """Summary of class progress for teachers."""
    class_id: int
    class_title: str
    total_students: int
    active_students: int
    average_progress: float
    average_score: float
    completion_rate: float
    top_performers: List[UserResponse]
    
    class Config:
        from_attributes = True

class ProgressUpdateRequest(BaseModel):
    """Request to update student progress."""
    progress_type: str  # slide, recording, quiz, objective
    item_id: int
    status: str
    progress_percentage: Optional[float] = None
    time_spent: Optional[int] = None
    additional_data: Optional[Dict[str, Any]] = None

class ProgressAnalyticsRequest(BaseModel):
    """Request for progress analytics."""
    student_id: Optional[int] = None
    class_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    group_by: str = "day"  # day, week, month

# Push Notification and Sync Schemas

class PushTokenBase(BaseModel):
    token: str
    platform: str  # ios, android, web
    device_id: Optional[str] = None
    is_active: bool = True

class PushTokenCreate(PushTokenBase):
    pass

class PushTokenResponse(PushTokenBase):
    id: int
    user_id: int
    created_at: datetime
    last_used: datetime
    
    class Config:
        from_attributes = True

class NotificationPreferenceBase(BaseModel):
    notification_type: str  # quiz_reminder, live_session, achievement, general
    is_enabled: bool = True
    reminder_minutes: int = 15  # Minutes before event to send reminder

class NotificationPreferenceCreate(NotificationPreferenceBase):
    pass

class NotificationPreferenceResponse(NotificationPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ScheduledEventBase(BaseModel):
    event_type: str  # quiz, live_session, assignment
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = 60
    is_recurring: bool = False
    recurrence_pattern: Optional[Dict[str, Any]] = None
    is_active: bool = True

class ScheduledEventCreate(ScheduledEventBase):
    class_id: int

class ScheduledEventResponse(ScheduledEventBase):
    id: int
    class_id: int
    created_at: datetime
    class_: ClassResponse
    
    class Config:
        from_attributes = True

class ScheduledNotificationBase(BaseModel):
    scheduled_event_id: int
    user_id: int
    notification_type: str  # reminder, start, end
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed, cancelled
    retry_count: int = 0
    error_message: Optional[str] = None

class ScheduledNotificationResponse(ScheduledNotificationBase):
    id: int
    
    class Config:
        from_attributes = True

class NotificationLogBase(BaseModel):
    user_id: int
    notification_type: str
    title: str
    body: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    platform: str
    delivery_status: str = "sent"
    device_response: Optional[str] = None

class NotificationLogResponse(NotificationLogBase):
    id: int
    sent_at: datetime
    
    class Config:
        from_attributes = True

class OfflineActivityBase(BaseModel):
    activity_type: str  # slide_progress, recording_progress, quiz_response, etc.
    activity_data: Dict[str, Any]  # Serialized activity data
    offline_id: str  # Unique ID generated on device
    sync_status: str = "pending"  # pending, synced, failed, conflict
    conflict_resolution: str = "server_wins"  # server_wins, client_wins, manual
    retry_count: int = 0
    error_message: Optional[str] = None

class OfflineActivityCreate(OfflineActivityBase):
    pass

class OfflineActivityResponse(OfflineActivityBase):
    id: int
    user_id: int
    created_at: datetime
    synced_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SyncSessionBase(BaseModel):
    device_id: str
    activities_synced: int = 0
    conflicts_resolved: int = 0
    sync_status: str = "in_progress"  # in_progress, completed, failed
    last_activity_at: Optional[datetime] = None

class SyncSessionCreate(SyncSessionBase):
    pass

class SyncSessionResponse(SyncSessionBase):
    id: int
    user_id: int
    session_start: datetime
    session_end: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Notification and Sync Request/Response Schemas

class PushNotificationRequest(BaseModel):
    """Request to send push notification."""
    user_ids: List[int]
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    notification_type: str = "general"

class PushNotificationResponse(BaseModel):
    """Response from push notification service."""
    success: bool
    message: str
    sent_count: int
    failed_count: int
    failed_users: List[int] = []

class OfflineSyncRequest(BaseModel):
    """Request to sync offline activities."""
    device_id: str
    activities: List[OfflineActivityCreate]
    last_sync_at: Optional[datetime] = None

class OfflineSyncResponse(BaseModel):
    """Response from offline sync."""
    success: bool
    message: str
    synced_count: int
    conflict_count: int
    conflicts: List[Dict[str, Any]] = []
    server_activities: List[OfflineActivityResponse] = []

class ConflictResolutionRequest(BaseModel):
    """Request to resolve sync conflicts."""
    offline_activity_id: int
    resolution: str  # server_wins, client_wins, manual
    client_data: Optional[Dict[str, Any]] = None

class ScheduledEventNotificationRequest(BaseModel):
    """Request to schedule event notifications."""
    event_id: int
    notification_type: str  # reminder, start, end
    reminder_minutes: Optional[int] = None  # For reminder notifications
    user_ids: Optional[List[int]] = None  # If None, notify all class students
