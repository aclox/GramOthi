from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User, Class, LiveSession, Poll, PollVote, DiscussionPost
from ..schemas import (
    LiveSessionCreate, LiveSessionResponse, PollCreate, PollResponse,
    PollVote as PollVoteSchema, DiscussionPostCreate, DiscussionPostResponse
)
from ..routes.auth import get_current_user, get_current_teacher
from datetime import datetime
import json

router = APIRouter(prefix="/live", tags=["live-sessions"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}  # class_id -> list of connections
    
    async def connect(self, websocket: WebSocket, class_id: int, user_id: int):
        await websocket.accept()
        if class_id not in self.active_connections:
            self.active_connections[class_id] = []
        self.active_connections[class_id].append({
            "websocket": websocket,
            "user_id": user_id
        })
    
    def disconnect(self, websocket: WebSocket, class_id: int):
        if class_id in self.active_connections:
            self.active_connections[class_id] = [
                conn for conn in self.active_connections[class_id]
                if conn["websocket"] != websocket
            ]
    
    async def broadcast_to_class(self, message: dict, class_id: int, exclude_user_id: int = None):
        if class_id in self.active_connections:
            for connection in self.active_connections[class_id]:
                if connection["user_id"] != exclude_user_id:
                    try:
                        await connection["websocket"].send_text(json.dumps(message))
                    except:
                        pass

manager = ConnectionManager()

# Live session management
@router.post("/sessions", response_model=LiveSessionResponse)
def start_live_session(
    session_data: LiveSessionCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Start a live session for a class."""
    # Verify class exists and user is the teacher
    db_class = db.query(Class).filter(Class.id == session_data.class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can start live sessions"
        )
    
    # Check if there's already an active session
    active_session = db.query(LiveSession).filter(
        LiveSession.class_id == session_data.class_id,
        LiveSession.is_active == True
    ).first()
    
    if active_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already an active live session for this class"
        )
    
    # Create live session
    db_session = LiveSession(
        class_id=session_data.class_id,
        is_active=True
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session

@router.put("/sessions/{session_id}/end")
def end_live_session(
    session_id: int,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """End a live session."""
    db_session = db.query(LiveSession).filter(LiveSession.id == session_id).first()
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live session not found"
        )
    
    # Verify user is the teacher of the class
    db_class = db.query(Class).filter(Class.id == db_session.class_id).first()
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can end this session"
        )
    
    db_session.is_active = False
    db.commit()
    
    return {"message": "Live session ended successfully"}

@router.get("/sessions/class/{class_id}", response_model=LiveSessionResponse)
def get_active_session(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the active live session for a class."""
    session = db.query(LiveSession).filter(
        LiveSession.class_id == class_id,
        LiveSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active live session found for this class"
        )
    
    return session

# Poll management
@router.post("/polls", response_model=PollResponse)
def create_poll(
    poll: PollCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new poll for a class."""
    # Verify class exists and user is the teacher
    db_class = db.query(Class).filter(Class.id == poll.class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if db_class.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the class teacher can create polls"
        )
    
    # Validate poll data
    if len(poll.options) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Poll must have at least 2 options"
        )
    
    # Create poll
    db_poll = Poll(
        class_id=poll.class_id,
        question=poll.question,
        options=poll.options,
        is_active=poll.is_active
    )
    db.add(db_poll)
    db.commit()
    db.refresh(db_poll)
    
    return db_poll

@router.post("/polls/{poll_id}/vote")
def vote_on_poll(
    poll_id: int,
    vote: PollVoteSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vote on a poll."""
    # Verify poll exists and is active
    db_poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not db_poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found"
        )
    
    if not db_poll.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This poll is no longer active"
        )
    
    # Verify vote is valid
    if vote.option_index < 0 or vote.option_index >= len(db_poll.options):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid option index"
        )
    
    # Check if user already voted
    existing_vote = db.query(PollVote).filter(
        PollVote.poll_id == poll_id,
        PollVote.voter_id == current_user.id
    ).first()
    
    if existing_vote:
        # Update existing vote
        existing_vote.option_index = vote.option_index
        existing_vote.timestamp = datetime.now()
    else:
        # Create new vote
        db_vote = PollVote(
            poll_id=poll_id,
            voter_id=current_user.id,
            option_index=vote.option_index
        )
        db.add(db_vote)
    
    db.commit()
    
    return {"message": "Vote recorded successfully"}

@router.get("/polls/{poll_id}/results")
def get_poll_results(
    poll_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get results for a poll."""
    db_poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not db_poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poll not found"
        )
    
    # Get all votes for this poll
    votes = db.query(PollVote).filter(PollVote.poll_id == poll_id).all()
    
    # Count votes for each option
    results = [0] * len(db_poll.options)
    for vote in votes:
        if 0 <= vote.option_index < len(results):
            results[vote.option_index] += 1
    
    return {
        "poll_id": poll_id,
        "question": db_poll.question,
        "options": db_poll.options,
        "results": results,
        "total_votes": len(votes)
    }

# Discussion posts
@router.post("/discussions", response_model=DiscussionPostResponse)
def create_discussion_post(
    post: DiscussionPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new discussion post."""
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == post.class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify parent post exists if specified
    if post.parent_id:
        parent_post = db.query(DiscussionPost).filter(DiscussionPost.id == post.parent_id).first()
        if not parent_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent post not found"
            )
    
    # Create discussion post
    db_post = DiscussionPost(
        class_id=post.class_id,
        author_id=current_user.id,
        content=post.content,
        parent_id=post.parent_id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    # Load author info
    db.refresh(db_post.author)
    
    return db_post

@router.get("/discussions/class/{class_id}", response_model=List[DiscussionPostResponse])
def get_class_discussions(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all discussion posts for a class."""
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Get top-level posts (no parent_id)
    posts = db.query(DiscussionPost).filter(
        DiscussionPost.class_id == class_id,
        DiscussionPost.parent_id == None
    ).order_by(DiscussionPost.created_at.desc()).all()
    
    # Load author info for each post
    for post in posts:
        db.refresh(post.author)
    
    return posts

@router.get("/discussions/{post_id}/replies", response_model=List[DiscussionPostResponse])
def get_post_replies(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get replies to a specific discussion post."""
    # Verify post exists
    db_post = db.query(DiscussionPost).filter(DiscussionPost.id == post_id).first()
    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Get replies
    replies = db.query(DiscussionPost).filter(
        DiscussionPost.parent_id == post_id
    ).order_by(DiscussionPost.created_at.asc()).all()
    
    # Load author info for each reply
    for reply in replies:
        db.refresh(reply.author)
    
    return replies

# WebSocket endpoint for real-time communication
@router.websocket("/ws/{class_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    class_id: int,
    token: str
):
    """WebSocket endpoint for real-time communication during live sessions."""
    # In a real implementation, you would validate the token here
    # For now, we'll accept any connection
    
    try:
        await manager.connect(websocket, class_id, user_id=0)  # user_id would come from token
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Broadcast message to all users in the class
            await manager.broadcast_to_class(message, class_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, class_id)
