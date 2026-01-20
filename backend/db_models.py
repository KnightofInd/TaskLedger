"""
SQLAlchemy models for TaskLedger database.
Maps to PostgreSQL tables and mirrors the Pydantic models structure.
"""
from sqlalchemy import (
    Column, String, Text, Float, DateTime, Date, ForeignKey, 
    Integer, Enum as SQLEnum, JSON, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from uuid import uuid4
import enum

from database import Base


# === ENUMS ===

class PriorityEnum(str, enum.Enum):
    """Priority levels for action items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskTypeEnum(str, enum.Enum):
    """Types of risks identified during validation."""
    VAGUE_DESCRIPTION = "vague_description"
    MISSING_OWNER = "missing_owner"
    MISSING_DEADLINE = "missing_deadline"
    UNCLEAR_DEPENDENCY = "unclear_dependency"
    SCOPE_TOO_BROAD = "scope_too_broad"
    CONFLICTING_ASSIGNMENT = "conflicting_assignment"


class ConfidenceLevelEnum(str, enum.Enum):
    """Confidence levels for action item extraction."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# === DATABASE MODELS ===

class Meeting(Base):
    """
    Meeting table - stores processed meetings and metadata.
    """
    __tablename__ = "meetings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    meeting_text = Column(Text, nullable=False)
    participants = Column(JSON, default=list)  # Stored as JSON array
    meeting_title = Column(String(255), nullable=True)
    meeting_date = Column(Date, nullable=False, default=date.today)
    processed_at = Column(DateTime, nullable=False, default=datetime.now)
    total_confidence = Column(Float, nullable=False)
    
    # Relationships
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    
    # Computed properties would be done in application layer
    
    def __repr__(self):
        return f"<Meeting(id={self.id}, title={self.meeting_title}, items={len(self.action_items)})>"


class ActionItem(Base):
    """
    ActionItem table - stores individual action items extracted from meetings.
    """
    __tablename__ = "action_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    meeting_id = Column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    owner = Column(String(255), nullable=True)
    deadline = Column(Date, nullable=True)
    priority = Column(SQLEnum(PriorityEnum), nullable=False, default=PriorityEnum.MEDIUM)
    confidence = Column(SQLEnum(ConfidenceLevelEnum), nullable=False)
    confidence_score = Column(Float, nullable=False)
    dependencies = Column(JSON, default=list)  # List of action_item IDs
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    is_complete = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="action_items")
    risk_flags = relationship("RiskFlag", back_populates="action_item", cascade="all, delete-orphan")
    clarification_questions = relationship("ClarificationQuestion", back_populates="action_item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ActionItem(id={self.id}, description={self.description[:50]}, owner={self.owner})>"


class RiskFlag(Base):
    """
    RiskFlag table - stores risks identified for action items.
    """
    __tablename__ = "risk_flags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_item_id = Column(String(36), ForeignKey("action_items.id", ondelete="CASCADE"), nullable=False)
    risk_type = Column(SQLEnum(RiskTypeEnum), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SQLEnum(PriorityEnum), nullable=False)
    suggested_clarification = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Relationships
    action_item = relationship("ActionItem", back_populates="risk_flags")
    
    def __repr__(self):
        return f"<RiskFlag(id={self.id}, type={self.risk_type.value}, severity={self.severity.value})>"


class ClarificationQuestion(Base):
    """
    ClarificationQuestion table - stores clarification questions for action items.
    """
    __tablename__ = "clarification_questions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_item_id = Column(String(36), ForeignKey("action_items.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    field = Column(String(50), nullable=False)  # owner, deadline, description
    priority = Column(String(20), nullable=False)  # critical, high, medium, low
    answer = Column(Text, nullable=True)  # User's answer
    answered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Relationships
    action_item = relationship("ActionItem", back_populates="clarification_questions")
    
    def __repr__(self):
        return f"<ClarificationQuestion(id={self.id}, field={self.field}, answered={bool(self.answer)})>"
