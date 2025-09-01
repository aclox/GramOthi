from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User, Class, Quiz, Response
from ..schemas import (
    QuizCreate, QuizResponse, ResponseCreate, ResponseResponse
)
from ..routes.auth import get_current_user, get_current_teacher
from ..services.progress_service import ProgressService

router = APIRouter(prefix="/quizzes", tags=["quizzes"])

@router.post("/", response_model=QuizResponse)
def create_quiz(
    quiz: QuizCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new quiz (only teachers can create quizzes)."""
    # Verify class exists and user is the teacher
    db_class = db.query(Class).filter(Class.id == quiz.class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can create quizzes"
        )
    
    # Validate quiz data
    if len(quiz.options) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz must have at least 2 options"
        )
    
    if quiz.correct_option < 0 or quiz.correct_option >= len(quiz.options):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correct option index is out of range"
        )
    
    # Create quiz
    db_quiz = Quiz(
        class_id=quiz.class_id,
        question=quiz.question,
        options=quiz.options,
        correct_option=quiz.correct_option
    )
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    
    return db_quiz

@router.get("/class/{class_id}", response_model=List[QuizResponse])
def get_class_quizzes(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all quizzes for a specific class."""
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    quizzes = db.query(Quiz).filter(Quiz.class_id == class_id).all()
    return quizzes

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific quiz by ID."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    return quiz

@router.put("/{quiz_id}", response_model=QuizResponse)
def update_quiz(
    quiz_id: int,
    quiz_update: QuizCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Update a quiz (only by the teacher who created it)."""
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Verify user is the teacher of the class
    db_class = db.query(Class).filter(Class.id == db_quiz.class_id).first()
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can update this quiz"
        )
    
    # Validate quiz data
    if len(quiz_update.options) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz must have at least 2 options"
        )
    
    if quiz_update.correct_option < 0 or quiz_update.correct_option >= len(quiz_update.options):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correct option index is out of range"
        )
    
    # Update quiz
    db_quiz.question = quiz_update.question
    db_quiz.options = quiz_update.options
    db_quiz.correct_option = quiz_update.correct_option
    
    db.commit()
    db.refresh(db_quiz)
    
    return db_quiz

@router.delete("/{quiz_id}")
def delete_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete a quiz (only by the teacher who created it)."""
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Verify user is the teacher of the class
    db_class = db.query(Class).filter(Class.id == db_quiz.class_id).first()
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can delete this quiz"
        )
    
    db.delete(db_quiz)
    db.commit()
    
    return {"message": "Quiz deleted successfully"}

# Quiz responses
@router.post("/{quiz_id}/respond", response_model=ResponseResponse)
def submit_quiz_response(
    quiz_id: int,
    response: ResponseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a response to a quiz."""
    # Verify quiz exists
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Verify answer is valid
    if response.answer < 0 or response.answer >= len(db_quiz.options):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid answer option"
        )
    
    # Check if user already responded to this quiz
    existing_response = db.query(Response).filter(
        Response.quiz_id == quiz_id,
        Response.student_id == current_user.id
    ).first()
    
    if existing_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already responded to this quiz"
        )
    
    # Check if answer is correct and calculate points
    is_correct = response.answer == db_quiz.correct_option
    points_earned = db_quiz.points if is_correct else 0
    
    # Create response
    db_response = Response(
        quiz_id=quiz_id,
        student_id=current_user.id,
        answer=response.answer,
        is_correct=is_correct,
        points_earned=points_earned
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    
    # Update performance analytics
    try:
        ProgressService.calculate_performance_analytics(
            db, current_user.id, db_quiz.class_id
        )
    except Exception as e:
        logger.warning(f"Failed to update performance analytics: {e}")
    
    # Check for achievements
    if is_correct:
        # Award quiz-related achievements
        try:
            # Check if this is their first correct answer
            correct_responses = db.query(Response).filter(
                and_(
                    Response.student_id == current_user.id,
                    Response.is_correct == True
                )
            ).count()
            
            if correct_responses == 1:
                ProgressService.award_achievement(
                    db, current_user.id, "first_correct_answer",
                    "First Correct Answer", "Answered your first quiz correctly!", 10
                )
            elif correct_responses == 10:
                ProgressService.award_achievement(
                    db, current_user.id, "quiz_master",
                    "Quiz Master", "Answered 10 quizzes correctly!", 50
                )
        except Exception as e:
            logger.warning(f"Failed to award achievement: {e}")
    
    return db_response

@router.get("/{quiz_id}/responses", response_model=List[ResponseResponse])
def get_quiz_responses(
    quiz_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all responses for a quiz (only teachers can view responses)."""
    # Verify quiz exists
    db_quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Verify user is the teacher of the class
    db_class = db.query(Class).filter(Class.id == db_quiz.class_id).first()
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can view quiz responses"
        )
    
    responses = db.query(Response).filter(Response.quiz_id == quiz_id).all()
    return responses

@router.get("/{quiz_id}/my-response", response_model=ResponseResponse)
def get_my_quiz_response(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's response to a specific quiz."""
    response = db.query(Response).filter(
        Response.quiz_id == quiz_id,
        Response.student_id == current_user.id
    ).first()
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You haven't responded to this quiz yet"
        )
    
    return response
