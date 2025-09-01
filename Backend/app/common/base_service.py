"""
Base service class for GramOthi backend
Provides common imports and utilities for all service classes
"""

from .imports import (
    logger, Session, List, Dict, Any, Optional, Tuple,
    datetime, timezone, timedelta, and_, or_, func
)

class BaseService:
    """Base class for all services with common imports and utilities."""
    
    @staticmethod
    def log_operation(operation: str, details: Dict[str, Any] = None):
        """Log service operations with consistent formatting."""
        if details:
            logger.info(f"Service operation: {operation} - {details}")
        else:
            logger.info(f"Service operation: {operation}")
    
    @staticmethod
    def log_error(operation: str, error: Exception, details: Dict[str, Any] = None):
        """Log service errors with consistent formatting."""
        error_msg = f"Service error in {operation}: {str(error)}"
        if details:
            error_msg += f" - Details: {details}"
        logger.error(error_msg)
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Format datetime to ISO string with timezone."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    
    @staticmethod
    def parse_datetime(dt_str: str) -> datetime:
        """Parse ISO datetime string to datetime object."""
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    
    @staticmethod
    def get_current_utc() -> datetime:
        """Get current UTC datetime."""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def calculate_duration(start_time: datetime, end_time: datetime) -> int:
        """Calculate duration in minutes between two datetimes."""
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        
        duration = end_time - start_time
        return int(duration.total_seconds() / 60)
    
    @staticmethod
    def safe_commit(db: Session, operation: str = "database operation"):
        """Safely commit database changes with error handling."""
        try:
            db.commit()
            logger.debug(f"Successfully committed: {operation}")
            return True
        except Exception as e:
            db.rollback()
            BaseService.log_error(operation, e)
            return False
    
    @staticmethod
    def safe_refresh(db: Session, obj: Any, operation: str = "database refresh"):
        """Safely refresh database object with error handling."""
        try:
            db.refresh(obj)
            logger.debug(f"Successfully refreshed: {operation}")
            return True
        except Exception as e:
            BaseService.log_error(operation, e)
            return False
