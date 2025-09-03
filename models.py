from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Boolean, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .config import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "student" or "teacher"
    
    classes = relationship("Class", back_populates="teacher")
    responses = relationship("Response", back_populates="student")
    discussion_posts = relationship("DiscussionPost", back_populates="author")
    poll_votes = relationship("PollVote", back_populates="voter")
    # Progress tracking relationships
    student_progress = relationship("StudentProgress", back_populates="student")
    learning_sessions = relationship("LearningSession", back_populates="student")
    achievements = relationship("Achievement", back_populates="student")
    # Notification and sync relationships
    push_tokens = relationship("PushToken", back_populates="user")
    notification_preferences = relationship("NotificationPreference", back_populates="user")
    offline_activities = relationship("OfflineActivity", back_populates="user")

class Class(Base):
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    teacher = relationship("User", back_populates="classes")
    slides = relationship("Slide", back_populates="class_")
    recordings = relationship("Recording", back_populates="class_")
    quizzes = relationship("Quiz", back_populates="class_")
    live_sessions = relationship("LiveSession", back_populates="class_")
    polls = relationship("Poll", back_populates="class_")
    discussion_posts = relationship("DiscussionPost", back_populates="class_")
    # Progress tracking relationships
    student_progress = relationship("StudentProgress", back_populates="class_")
    learning_objectives = relationship("LearningObjective", back_populates="class_")
    # Scheduled events relationships
    scheduled_events = relationship("ScheduledEvent", back_populates="class_")

class Slide(Base):
    __tablename__ = "slides"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    file_url = Column(String, nullable=False)
    order_no = Column(Integer, default=1)
    
    class_ = relationship("Class", back_populates="slides")
    slide_progress = relationship("SlideProgress", back_populates="slide")

class Recording(Base):
    __tablename__ = "recordings"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    audio_url = Column(String, nullable=False)
    bundle_url = Column(String, nullable=True)
    
    class_ = relationship("Class", back_populates="recordings")
    recording_progress = relationship("RecordingProgress", back_populates="recording")

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    question = Column(String, nullable=False)
    options = Column(JSON, nullable=False)
    correct_option = Column(Integer, nullable=False)
    points = Column(Integer, default=1)  # Points for correct answer
    scheduled_at = Column(DateTime, nullable=True)  # When quiz should be available
    duration_minutes = Column(Integer, default=30)  # Quiz duration in minutes
    is_scheduled = Column(Boolean, default=False)  # Whether quiz is scheduled
    
    class_ = relationship("Class", back_populates="quizzes")
    responses = relationship("Response", back_populates="quiz")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    answer = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_correct = Column(Boolean, default=False)  # Whether answer was correct
    points_earned = Column(Integer, default=0)   # Points earned for this answer
    
    quiz = relationship("Quiz", back_populates="responses")
    student = relationship("User", back_populates="responses")

class LiveSession(Base):
    __tablename__ = "live_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    scheduled_start = Column(DateTime, nullable=True)  # When session should start
    scheduled_end = Column(DateTime, nullable=True)    # When session should end
    title = Column(String, nullable=True)  # Session title/description
    is_scheduled = Column(Boolean, default=False)  # Whether session is scheduled
    
    class_ = relationship("Class", back_populates="live_sessions")
    session_attendance = relationship("SessionAttendance", back_populates="live_session")

class Poll(Base):
    __tablename__ = "polls"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    question = Column(String, nullable=False)
    options = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    class_ = relationship("Class", back_populates="polls")
    votes = relationship("PollVote", back_populates="poll")

class PollVote(Base):
    __tablename__ = "poll_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    voter_id = Column(Integer, ForeignKey("users.id"))
    option_index = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    poll = relationship("Poll", back_populates="votes")
    voter = relationship("User", back_populates="poll_votes")

class DiscussionPost(Base):
    __tablename__ = "discussion_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("discussion_posts.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    class_ = relationship("Class", back_populates="discussion_posts")
    author = relationship("User", back_populates="discussion_posts")
    replies = relationship("DiscussionPost", remote_side=[id])

# New Progress Tracking Models

class LearningObjective(Base):
    """Learning objectives for each class."""
    __tablename__ = "learning_objectives"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_no = Column(Integer, default=1)
    is_required = Column(Boolean, default=True)  # Whether this objective is mandatory
    
    class_ = relationship("Class", back_populates="learning_objectives")
    student_progress = relationship("StudentProgress", back_populates="learning_objective")

class StudentProgress(Base):
    """Track student progress through learning objectives."""
    __tablename__ = "student_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))
    learning_objective_id = Column(Integer, ForeignKey("learning_objectives.id"), nullable=True)
    status = Column(String, default="not_started")  # not_started, in_progress, completed, failed
    progress_percentage = Column(Float, default=0.0)  # 0.0 to 100.0
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    student = relationship("User", back_populates="student_progress")
    class_ = relationship("Class", back_populates="student_progress")
    learning_objective = relationship("LearningObjective", back_populates="student_progress")

class SlideProgress(Base):
    """Track student progress through slides."""
    __tablename__ = "slide_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    slide_id = Column(Integer, ForeignKey("slides.id"))
    status = Column(String, default="not_viewed")  # not_viewed, viewed, completed
    time_spent = Column(Integer, default=0)  # Time spent in seconds
    viewed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    slide = relationship("Slide", back_populates="slide_progress")

class RecordingProgress(Base):
    """Track student progress through recordings."""
    __tablename__ = "recording_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    recording_id = Column(Integer, ForeignKey("recordings.id"))
    status = Column(String, default="not_listened")  # not_listened, listening, completed
    time_listened = Column(Integer, default=0)  # Time listened in seconds
    total_duration = Column(Integer, nullable=True)  # Total duration in seconds
    progress_percentage = Column(Float, default=0.0)  # 0.0 to 100.0
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    recording = relationship("Recording", back_populates="recording_progress")

class LearningSession(Base):
    """Track individual learning sessions for analytics."""
    __tablename__ = "learning_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))
    session_type = Column(String, nullable=False)  # live, recorded, self_study
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0)
    activities_completed = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)  # 0.0 to 10.0
    
    student = relationship("User", back_populates="learning_sessions")

class SessionAttendance(Base):
    """Track attendance in live sessions."""
    __tablename__ = "session_attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    live_session_id = Column(Integer, ForeignKey("live_sessions.id"))
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    left_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0)
    participation_level = Column(String, default="passive")  # passive, active, very_active
    
    live_session = relationship("LiveSession", back_populates="session_attendance")
    student = relationship("User")

class Achievement(Base):
    """Track student achievements and badges."""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    achievement_type = Column(String, nullable=False)  # quiz_master, attendance_king, discussion_leader, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    earned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    points_awarded = Column(Integer, default=0)
    
    student = relationship("User", back_populates="achievements")

class PerformanceAnalytics(Base):
    """Aggregated performance data for teachers."""
    __tablename__ = "performance_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))
    total_points = Column(Integer, default=0)
    quizzes_taken = Column(Integer, default=0)
    quizzes_passed = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    total_study_time = Column(Integer, default=0)  # Total time in minutes
    attendance_rate = Column(Float, default=0.0)  # 0.0 to 100.0
    engagement_score = Column(Float, default=0.0)  # 0.0 to 10.0
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # This will be updated automatically based on other progress data

# New Push Notification and Sync Models

class PushToken(Base):
    """Store push notification tokens for users."""
    __tablename__ = "push_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, nullable=False, unique=True)
    platform = Column(String, nullable=False)  # ios, android, web
    device_id = Column(String, nullable=True)  # Unique device identifier
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="push_tokens")

class NotificationPreference(Base):
    """User preferences for different types of notifications."""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    notification_type = Column(String, nullable=False)  # quiz_reminder, live_session, achievement, general
    is_enabled = Column(Boolean, default=True)
    reminder_minutes = Column(Integer, default=15)  # Minutes before event to send reminder
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="notification_preferences")

class ScheduledEvent(Base):
    """Scheduled events like quizzes and live sessions."""
    __tablename__ = "scheduled_events"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    event_type = Column(String, nullable=False)  # quiz, live_session, assignment
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # For recurring events
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    class_ = relationship("Class", back_populates="scheduled_events")
    notifications = relationship("ScheduledNotification", back_populates="scheduled_event")

class ScheduledNotification(Base):
    """Track scheduled notifications for events."""
    __tablename__ = "scheduled_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    scheduled_event_id = Column(Integer, ForeignKey("scheduled_events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    notification_type = Column(String, nullable=False)  # reminder, start, end
    scheduled_at = Column(DateTime, nullable=False)  # When to send notification
    sent_at = Column(DateTime, nullable=True)  # When notification was actually sent
    status = Column(String, default="pending")  # pending, sent, failed, cancelled
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    scheduled_event = relationship("ScheduledEvent", back_populates="notifications")

class NotificationLog(Base):
    """Log of all sent notifications for tracking and debugging."""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    notification_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    data = Column(JSON, nullable=True)  # Additional data sent with notification
    platform = Column(String, nullable=False)  # ios, android, web
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    delivery_status = Column(String, default="sent")  # sent, delivered, failed
    device_response = Column(Text, nullable=True)  # Response from push service
    
    user = relationship("User")

class OfflineActivity(Base):
    """Track offline activities for later synchronization."""
    __tablename__ = "offline_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String, nullable=False)  # slide_progress, recording_progress, quiz_response, etc.
    activity_data = Column(JSON, nullable=False)  # Serialized activity data
    offline_id = Column(String, nullable=False)  # Unique ID generated on device
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    synced_at = Column(DateTime, nullable=True)  # When activity was synced to server
    sync_status = Column(String, default="pending")  # pending, synced, failed, conflict
    conflict_resolution = Column(String, default="server_wins")  # server_wins, client_wins, manual
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="offline_activities")

class SyncSession(Base):
    """Track synchronization sessions for conflict resolution."""
    __tablename__ = "sync_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    device_id = Column(String, nullable=False)
    session_start = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    session_end = Column(DateTime, nullable=True)
    activities_synced = Column(Integer, default=0)
    conflicts_resolved = Column(Integer, default=0)
    sync_status = Column(String, default="in_progress")  # in_progress, completed, failed
    last_activity_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User")
