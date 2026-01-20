"""
CRUD operations for TaskLedger.
Database operations for meetings, action items, risk flags, and clarifications.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, date

from db_models import (
    Meeting as DBMeeting,
    ActionItem as DBActionItem,
    RiskFlag as DBRiskFlag,
    ClarificationQuestion as DBClarificationQuestion,
    PriorityEnum,
    RiskTypeEnum,
    ConfidenceLevelEnum
)
from models import (
    Meeting,
    ActionItem,
    RiskFlag,
    MeetingInput,
    ValidationOutput
)
from logger import logger


# === MEETING CRUD ===

async def create_meeting(
    db: AsyncSession,
    meeting_input: MeetingInput,
    validation_result: ValidationOutput
) -> DBMeeting:
    """
    Create a new meeting record with action items.
    
    Args:
        db: Database session
        meeting_input: Original meeting input data
        validation_result: Processed validation output from agents
        
    Returns:
        Created meeting record
    """
    # Create meeting record
    db_meeting = DBMeeting(
        meeting_text=meeting_input.meeting_text,
        participants=meeting_input.participants,
        meeting_title=meeting_input.meeting_title,
        meeting_date=meeting_input.meeting_date or date.today(),
        total_confidence=validation_result.overall_confidence
    )
    
    db.add(db_meeting)
    await db.flush()  # Get meeting ID
    
    # Create action items
    for item in validation_result.validated_items:
        db_item = DBActionItem(
            id=item.id,
            meeting_id=db_meeting.id,
            description=item.description,
            owner=item.owner,
            deadline=item.deadline,
            priority=PriorityEnum[item.priority.name],
            confidence=ConfidenceLevelEnum[item.confidence.name],
            confidence_score=item.confidence_score,
            dependencies=item.dependencies,
            context=item.context,
            is_complete=item.is_complete
        )
        db.add(db_item)
        
        # Create risk flags for this item
        for risk in item.risk_flags:
            db_risk = DBRiskFlag(
                action_item_id=item.id,
                risk_type=RiskTypeEnum[risk.risk_type.name],
                description=risk.description,
                severity=PriorityEnum[risk.severity.name],
                suggested_clarification=risk.suggested_clarification
            )
            db.add(db_risk)
    
    await db.commit()
    await db.refresh(db_meeting)
    
    logger.info(
        "Meeting created",
        extra={
            "meeting_id": db_meeting.id,
            "action_items": len(validation_result.validated_items)
        }
    )
    
    return db_meeting


async def get_meeting(db: AsyncSession, meeting_id: str) -> Optional[DBMeeting]:
    """
    Get a meeting by ID with all related data.
    
    Args:
        db: Database session
        meeting_id: Meeting UUID
        
    Returns:
        Meeting record or None
    """
    result = await db.execute(
        select(DBMeeting)
        .options(
            selectinload(DBMeeting.action_items)
            .selectinload(DBActionItem.risk_flags)
        )
        .options(
            selectinload(DBMeeting.action_items)
            .selectinload(DBActionItem.clarification_questions)
        )
        .where(DBMeeting.id == meeting_id)
    )
    return result.scalar_one_or_none()


async def list_meetings(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50
) -> List[DBMeeting]:
    """
    List all meetings with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of meeting records
    """
    result = await db.execute(
        select(DBMeeting)
        .options(selectinload(DBMeeting.action_items))
        .order_by(DBMeeting.processed_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def delete_meeting(db: AsyncSession, meeting_id: str) -> bool:
    """
    Delete a meeting and all related records (cascade).
    
    Args:
        db: Database session
        meeting_id: Meeting UUID
        
    Returns:
        True if deleted, False if not found
    """
    result = await db.execute(
        delete(DBMeeting).where(DBMeeting.id == meeting_id)
    )
    await db.commit()
    
    deleted = result.rowcount > 0
    if deleted:
        logger.info("Meeting deleted", extra={"meeting_id": meeting_id})
    
    return deleted


# === ACTION ITEM CRUD ===

async def get_action_item(
    db: AsyncSession,
    action_item_id: str
) -> Optional[DBActionItem]:
    """
    Get an action item by ID with all related data.
    
    Args:
        db: Database session
        action_item_id: Action item UUID
        
    Returns:
        Action item record or None
    """
    result = await db.execute(
        select(DBActionItem)
        .options(selectinload(DBActionItem.risk_flags))
        .options(selectinload(DBActionItem.clarification_questions))
        .where(DBActionItem.id == action_item_id)
    )
    return result.scalar_one_or_none()


async def update_action_item(
    db: AsyncSession,
    action_item_id: str,
    owner: Optional[str] = None,
    deadline: Optional[date] = None,
    priority: Optional[str] = None,
    is_complete: Optional[bool] = None
) -> Optional[DBActionItem]:
    """
    Update an action item.
    
    Args:
        db: Database session
        action_item_id: Action item UUID
        owner: New owner name
        deadline: New deadline
        priority: New priority level
        is_complete: Completion status
        
    Returns:
        Updated action item or None
    """
    db_item = await get_action_item(db, action_item_id)
    if not db_item:
        return None
    
    if owner is not None:
        db_item.owner = owner
    if deadline is not None:
        db_item.deadline = deadline
    if priority is not None:
        db_item.priority = PriorityEnum[priority.upper()]
    if is_complete is not None:
        db_item.is_complete = is_complete
    
    db_item.updated_at = datetime.now()
    
    await db.commit()
    await db.refresh(db_item)
    
    logger.info(
        "Action item updated",
        extra={"action_item_id": action_item_id}
    )
    
    return db_item


async def list_action_items_for_meeting(
    db: AsyncSession,
    meeting_id: str
) -> List[DBActionItem]:
    """
    Get all action items for a meeting.
    
    Args:
        db: Database session
        meeting_id: Meeting UUID
        
    Returns:
        List of action items
    """
    result = await db.execute(
        select(DBActionItem)
        .options(selectinload(DBActionItem.risk_flags))
        .options(selectinload(DBActionItem.clarification_questions))
        .where(DBActionItem.meeting_id == meeting_id)
        .order_by(DBActionItem.created_at)
    )
    return result.scalars().all()


# === CLARIFICATION CRUD ===

async def add_clarification_questions(
    db: AsyncSession,
    action_item_id: str,
    questions: List[dict]
) -> List[DBClarificationQuestion]:
    """
    Add clarification questions for an action item.
    
    Args:
        db: Database session
        action_item_id: Action item UUID
        questions: List of question dictionaries
        
    Returns:
        List of created clarification questions
    """
    db_questions = []
    for q in questions:
        db_question = DBClarificationQuestion(
            action_item_id=action_item_id,
            question_id=q["question_id"],
            question=q["question"],
            field=q["field"],
            priority=q["priority"]
        )
        db.add(db_question)
        db_questions.append(db_question)
    
    await db.commit()
    return db_questions


async def answer_clarification_question(
    db: AsyncSession,
    question_id: int,
    answer: str
) -> Optional[DBClarificationQuestion]:
    """
    Answer a clarification question.
    
    Args:
        db: Database session
        question_id: Question ID
        answer: User's answer
        
    Returns:
        Updated question or None
    """
    result = await db.execute(
        select(DBClarificationQuestion)
        .where(DBClarificationQuestion.id == question_id)
    )
    db_question = result.scalar_one_or_none()
    
    if not db_question:
        return None
    
    db_question.answer = answer
    db_question.answered_at = datetime.now()
    
    await db.commit()
    await db.refresh(db_question)
    
    return db_question


# === STATISTICS ===

async def get_meeting_statistics(db: AsyncSession, meeting_id: str) -> dict:
    """
    Get statistics for a meeting.
    
    Args:
        db: Database session
        meeting_id: Meeting UUID
        
    Returns:
        Dictionary with statistics
    """
    items = await list_action_items_for_meeting(db, meeting_id)
    
    return {
        "total_items": len(items),
        "complete_items": sum(1 for item in items if item.is_complete),
        "items_with_owner": sum(1 for item in items if item.owner),
        "items_with_deadline": sum(1 for item in items if item.deadline),
        "total_risks": sum(len(item.risk_flags) for item in items),
        "items_needing_clarification": sum(
            1 for item in items if len(item.risk_flags) > 0
        ),
        "priority_breakdown": {
            "critical": sum(1 for item in items if item.priority == PriorityEnum.CRITICAL),
            "high": sum(1 for item in items if item.priority == PriorityEnum.HIGH),
            "medium": sum(1 for item in items if item.priority == PriorityEnum.MEDIUM),
            "low": sum(1 for item in items if item.priority == PriorityEnum.LOW),
        }
    }
