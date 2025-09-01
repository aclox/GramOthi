from .config import Base, engine
from .models import (
    User, Class, Slide, Recording, Quiz, Response, LiveSession, Poll, PollVote, 
    DiscussionPost, LearningObjective, StudentProgress, SlideProgress, RecordingProgress,
    LearningSession, SessionAttendance, Achievement, PerformanceAnalytics,
    PushToken, NotificationPreference, ScheduledEvent, ScheduledNotification, 
    NotificationLog, OfflineActivity, SyncSession
)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")

if __name__ == "__main__":
    init_db()
