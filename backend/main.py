"""
FastAPI backend for TaskLedger - Meeting to Action Agent System.
Handles all AI orchestration, validation, and business logic.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import date
import uvicorn

from config import settings
from logger import logger
from database import get_db, init_db, close_db, check_db_connection
from models import MeetingInput, ActionItem as ActionItemModel, Meeting as MeetingModel
from agents import run_full_pipeline
import crud


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Multi-agent system for converting meeting notes into validated action items",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health Check Models
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    environment: str
    version: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check with dependencies."""
    status: str
    service: str
    environment: str
    version: str
    dependencies: Dict[str, str]


# === HEALTH CHECK ENDPOINTS ===

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - basic health check."""
    logger.info("Root health check called")
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    logger.info("Health check called")
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
        "version": "1.0.0"
    }


@app.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """Detailed health check with dependency status."""
    logger.info("Detailed health check called")
    
    # Check database connection
    db_status = "connected" if await check_db_connection() else "disconnected"
    
    dependencies = {
        "gemini_configured": "ready" if settings.gemini_api_key else "missing",
        "model": settings.gemini_model,
        "database": db_status
    }
    
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
        "version": "1.0.0",
        "dependencies": dependencies
    }


# === REQUEST/RESPONSE MODELS ===

class ActionItemUpdateRequest(BaseModel):
    """Request model for updating action items."""
    owner: Optional[str] = None
    deadline: Optional[date] = None
    priority: Optional[str] = None
    is_complete: Optional[bool] = None


class ClarificationAnswerRequest(BaseModel):
    """Request model for answering clarification questions."""
    question_id: int
    answer: str


# === MEETING ENDPOINTS ===

@app.post("/meetings", status_code=201)
async def create_meeting(
    meeting_input: MeetingInput,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new meeting and process it through the agent pipeline.
    
    Steps:
    1. Extract action items from meeting notes
    2. Attribute owners and deadlines (if explicit)
    3. Validate and add risk flags
    4. Store in database
    
    Returns:
        Processed meeting with action items
    """
    try:
        logger.info(
            "Processing new meeting",
            extra={
                "meeting_length": len(meeting_input.meeting_text),
                "participants": len(meeting_input.participants)
            }
        )
        
        # Run agent pipeline
        validation_result = await run_full_pipeline(
            meeting_input.meeting_text,
            meeting_input.participants
        )
        
        # Store in database
        db_meeting = await crud.create_meeting(db, meeting_input, validation_result)
        
        # Get full meeting with relations
        meeting = await crud.get_meeting(db, db_meeting.id)
        
        return {
            "id": meeting.id,
            "meeting_title": meeting.meeting_title,
            "meeting_date": meeting.meeting_date,
            "processed_at": meeting.processed_at,
            "total_confidence": meeting.total_confidence,
            "action_items_count": len(meeting.action_items),
            "meeting_id": meeting.id
        }
        
    except Exception as e:
        logger.error(f"Failed to process meeting: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process meeting: {str(e)}")


@app.get("/meetings")
async def list_meetings(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    List all meetings with pagination.
    
    Query params:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 50, max: 100)
    """
    if limit > 100:
        limit = 100
    
    meetings = await crud.list_meetings(db, skip, limit)
    
    return {
        "meetings": [
            {
                "id": m.id,
                "meeting_title": m.meeting_title,
                "meeting_date": m.meeting_date,
                "processed_at": m.processed_at,
                "total_confidence": m.total_confidence,
                "action_items_count": len(m.action_items),
                "participants": m.participants
            }
            for m in meetings
        ],
        "skip": skip,
        "limit": limit,
        "count": len(meetings)
    }


@app.get("/meetings/{meeting_id}")
async def get_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific meeting with all action items and details.
    """
    meeting = await crud.get_meeting(db, meeting_id)
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get statistics
    stats = await crud.get_meeting_statistics(db, meeting_id)
    
    return {
        "id": meeting.id,
        "meeting_title": meeting.meeting_title,
        "meeting_text": meeting.meeting_text,
        "meeting_date": meeting.meeting_date,
        "participants": meeting.participants,
        "processed_at": meeting.processed_at,
        "total_confidence": meeting.total_confidence,
        "action_items": [
            {
                "id": item.id,
                "description": item.description,
                "owner": item.owner,
                "deadline": item.deadline,
                "priority": item.priority.value,
                "confidence": item.confidence.value,
                "confidence_score": item.confidence_score,
                "is_complete": item.is_complete,
                "risk_flags_count": len(item.risk_flags),
                "created_at": item.created_at
            }
            for item in meeting.action_items
        ],
        "statistics": stats
    }


@app.delete("/meetings/{meeting_id}", status_code=204)
async def delete_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a meeting and all associated action items.
    """
    deleted = await crud.delete_meeting(db, meeting_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return None


# === ACTION ITEM ENDPOINTS ===

@app.get("/meetings/{meeting_id}/action-items")
async def get_meeting_action_items(
    meeting_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all action items for a specific meeting.
    """
    items = await crud.list_action_items_for_meeting(db, meeting_id)
    
    return {
        "meeting_id": meeting_id,
        "action_items": [
            {
                "id": item.id,
                "description": item.description,
                "owner": item.owner,
                "deadline": item.deadline,
                "priority": item.priority.value,
                "confidence": item.confidence.value,
                "confidence_score": item.confidence_score,
                "is_complete": item.is_complete,
                "dependencies": item.dependencies,
                "context": item.context,
                "risk_flags": [
                    {
                        "risk_type": risk.risk_type.value,
                        "description": risk.description,
                        "severity": risk.severity.value,
                        "suggested_clarification": risk.suggested_clarification
                    }
                    for risk in item.risk_flags
                ],
                "clarification_questions": [
                    {
                        "id": q.id,
                        "question": q.question,
                        "field": q.field,
                        "priority": q.priority,
                        "answer": q.answer,
                        "answered_at": q.answered_at
                    }
                    for q in item.clarification_questions
                ],
                "created_at": item.created_at,
                "updated_at": item.updated_at
            }
            for item in items
        ],
        "count": len(items)
    }


@app.get("/action-items/{action_item_id}")
async def get_action_item(
    action_item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific action item with all details.
    """
    item = await crud.get_action_item(db, action_item_id)
    
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    return {
        "id": item.id,
        "meeting_id": item.meeting_id,
        "description": item.description,
        "owner": item.owner,
        "deadline": item.deadline,
        "priority": item.priority.value,
        "confidence": item.confidence.value,
        "confidence_score": item.confidence_score,
        "is_complete": item.is_complete,
        "dependencies": item.dependencies,
        "context": item.context,
        "risk_flags": [
            {
                "id": risk.id,
                "risk_type": risk.risk_type.value,
                "description": risk.description,
                "severity": risk.severity.value,
                "suggested_clarification": risk.suggested_clarification
            }
            for risk in item.risk_flags
        ],
        "clarification_questions": [
            {
                "id": q.id,
                "question": q.question,
                "field": q.field,
                "priority": q.priority,
                "answer": q.answer,
                "answered_at": q.answered_at
            }
            for q in item.clarification_questions
        ],
        "created_at": item.created_at,
        "updated_at": item.updated_at
    }


@app.put("/action-items/{action_item_id}")
async def update_action_item(
    action_item_id: str,
    update_data: ActionItemUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an action item (owner, deadline, priority, or completion status).
    """
    updated_item = await crud.update_action_item(
        db,
        action_item_id,
        owner=update_data.owner,
        deadline=update_data.deadline,
        priority=update_data.priority,
        is_complete=update_data.is_complete
    )
    
    if not updated_item:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    return {
        "id": updated_item.id,
        "description": updated_item.description,
        "owner": updated_item.owner,
        "deadline": updated_item.deadline,
        "priority": updated_item.priority.value,
        "is_complete": updated_item.is_complete,
        "updated_at": updated_item.updated_at
    }


@app.post("/action-items/{action_item_id}/clarify")
async def answer_clarification(
    action_item_id: str,
    answer_data: ClarificationAnswerRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit an answer to a clarification question.
    """
    # Verify action item exists
    item = await crud.get_action_item(db, action_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    # Answer the question
    updated_question = await crud.answer_clarification_question(
        db,
        answer_data.question_id,
        answer_data.answer
    )
    
    if not updated_question:
        raise HTTPException(status_code=404, detail="Clarification question not found")
    
    return {
        "question_id": updated_question.id,
        "question": updated_question.question,
        "field": updated_question.field,
        "answer": updated_question.answer,
        "answered_at": updated_question.answered_at
    }


# === STARTUP & SHUTDOWN EVENTS ===

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(
        "Starting TaskLedger backend",
        extra={
            "environment": settings.environment,
            "model": settings.gemini_model
        }
    )
    
    # Initialize database
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down TaskLedger backend")
    
    # Close database connections
    await close_db()


# === MAIN ===

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False,
        log_level=settings.log_level.lower()
    )
