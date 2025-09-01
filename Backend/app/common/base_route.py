"""
Base route class for GramOthi backend
Provides common imports and utilities for all route modules
"""

from .imports import (
    APIRouter, Depends, HTTPException, status, Request, Response,
    Session, logger, get_db, get_current_user, get_current_teacher
)
from typing import List, Dict, Any

class BaseRouter:
    """Base class for all route modules with common imports and utilities."""
    
    @staticmethod
    def create_router(prefix: str, tags: List[str]) -> APIRouter:
        """Create a router with consistent configuration."""
        return APIRouter(prefix=prefix, tags=tags)
    
    @staticmethod
    def log_request(request: Request, operation: str, details: Dict[str, Any] = None):
        """Log route requests with consistent formatting."""
        user_info = f"User: {request.headers.get('authorization', 'No auth')[:20]}..."
        if details:
            logger.info(f"Route request: {operation} - {user_info} - {details}")
        else:
            logger.info(f"Route request: {operation} - {user_info}")
    
    @staticmethod
    def log_error(request: Request, operation: str, error: Exception, details: Dict[str, Any] = None):
        """Log route errors with consistent formatting."""
        user_info = f"User: {request.headers.get('authorization', 'No auth')[:20]}..."
        error_msg = f"Route error in {operation}: {str(error)} - {user_info}"
        if details:
            error_msg += f" - Details: {details}"
        logger.error(error_msg)
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str], operation: str):
        """Validate that required fields are present in request data."""
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields for {operation}: {missing_fields}"
            )
    
    @staticmethod
    def validate_user_permission(user_id: int, resource_user_id: int, operation: str):
        """Validate that user has permission to access a resource."""
        if user_id != resource_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User {user_id} does not have permission to {operation}"
            )
    
    @staticmethod
    def validate_teacher_permission(user_role: str, operation: str):
        """Validate that user is a teacher for teacher-only operations."""
        if user_role != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only teachers can {operation}"
            )
    
    @staticmethod
    def validate_student_permission(user_role: str, operation: str):
        """Validate that user is a student for student-only operations."""
        if user_role != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only students can {operation}"
            )
    
    @staticmethod
    def handle_database_error(error: Exception, operation: str):
        """Handle database errors consistently across routes."""
        logger.error(f"Database error in {operation}: {str(error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database operation failed: {operation}"
        )
    
    @staticmethod
    def create_success_response(message: str, data: Dict[str, Any] = None):
        """Create a consistent success response format."""
        response = {
            "success": True,
            "message": message
        }
        if data:
            response.update(data)
        return response
    
    @staticmethod
    def create_error_response(message: str, error_code: str = None, details: Dict[str, Any] = None):
        """Create a consistent error response format."""
        response = {
            "success": False,
            "message": message
        }
        if error_code:
            response["error_code"] = error_code
        if details:
            response["details"] = details
        return response
