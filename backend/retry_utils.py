"""
Retry and fallback utilities for TaskLedger agents.
Handles LLM failures, malformed outputs, and API errors gracefully.
"""
from typing import Optional, Callable, Any, TypeVar
from functools import wraps
import asyncio

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from pydantic import ValidationError
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior

from logger import logger
from models import (
    ActionItem,
    ExtractionOutput,
    AttributionOutput,
    ValidationOutput,
    ClarificationQuestionsOutput,
    Priority,
    ConfidenceLevel,
    RiskFlag,
    RiskType
)


# === RETRY DECORATORS ===

def retry_agent_call(max_attempts: int = 3, initial_wait: float = 1.0):
    """
    Decorator for retrying agent calls with exponential backoff.
    
    Retries on:
    - ModelHTTPError (API errors, rate limits, timeouts)
    - UnexpectedModelBehavior (malformed LLM responses)
    - ValidationError (schema validation failures)
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_wait: Initial wait time in seconds (doubles each retry)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=initial_wait, min=1, max=10),
        retry=retry_if_exception_type((
            ModelHTTPError,
            UnexpectedModelBehavior,
            ValidationError,
            asyncio.TimeoutError
        )),
        before_sleep=before_sleep_log(logger, logger.level),
        after=after_log(logger, logger.level),
        reraise=True
    )


# === FALLBACK STRATEGIES ===

class FallbackStrategies:
    """
    Fallback strategies when agent calls fail after all retries.
    Provides conservative defaults to keep the pipeline running.
    """
    
    @staticmethod
    def extraction_fallback(meeting_text: str) -> ExtractionOutput:
        """
        Fallback for extraction agent failure.
        Returns a single generic action item.
        """
        logger.warning("Using extraction fallback - returning generic action")
        return ExtractionOutput(
            raw_actions=[
                f"Review meeting notes and identify action items (Length: {len(meeting_text)} chars)"
            ]
        )
    
    @staticmethod
    def attribution_fallback(raw_actions: list[str]) -> AttributionOutput:
        """
        Fallback for attribution agent failure.
        Returns action items without owner/deadline assignment.
        """
        logger.warning("Using attribution fallback - no owner/deadline assignment")
        
        action_items = [
            ActionItem(
                id=str(i + 1),
                description=action,
                owner=None,
                deadline=None,
                priority=Priority.MEDIUM,
                confidence=ConfidenceLevel.LOW,
                confidence_score=0.3,
                risk_flags=[
                    RiskFlag(
                        risk_type=RiskType.MISSING_OWNER,
                        description="Owner not assigned due to extraction failure",
                        severity=Priority.HIGH,
                        suggested_clarification=f"Who should be responsible for: {action}?"
                    ),
                    RiskFlag(
                        risk_type=RiskType.MISSING_DEADLINE,
                        description="Deadline not set due to extraction failure",
                        severity=Priority.HIGH,
                        suggested_clarification=f"What is the deadline for: {action}?"
                    )
                ]
            )
            for i, action in enumerate(raw_actions)
        ]
        
        return AttributionOutput(action_items=action_items)
    
    @staticmethod
    def validation_fallback(action_items: list[ActionItem]) -> ValidationOutput:
        """
        Fallback for validation agent failure.
        Returns items with conservative confidence and generic risks.
        """
        logger.warning("Using validation fallback - conservative confidence assignment")
        
        for item in action_items:
            # Add generic risk if no owner or deadline
            if not item.owner and not any(r.risk_type == RiskType.MISSING_OWNER for r in item.risk_flags):
                item.risk_flags.append(
                    RiskFlag(
                        risk_type=RiskType.MISSING_OWNER,
                        description="No owner assigned",
                        severity=Priority.HIGH,
                        suggested_clarification=f"Who will handle: {item.description}?"
                    )
                )
            
            if not item.deadline and not any(r.risk_type == RiskType.MISSING_DEADLINE for r in item.risk_flags):
                item.risk_flags.append(
                    RiskFlag(
                        risk_type=RiskType.MISSING_DEADLINE,
                        description="No deadline specified",
                        severity=Priority.MEDIUM,
                        suggested_clarification=f"When is the deadline for: {item.description}?"
                    )
                )
            
            # Set conservative confidence
            item.confidence = ConfidenceLevel.LOW
            item.confidence_score = 0.3
        
        overall_confidence = sum(item.confidence_score for item in action_items) / len(action_items) if action_items else 0.0
        
        return ValidationOutput(
            validated_items=action_items,
            overall_confidence=overall_confidence
        )
    
    @staticmethod
    def refinement_fallback(action_items: list[ActionItem]) -> ClarificationQuestionsOutput:
        """
        Fallback for refinement agent failure.
        Returns basic clarification questions for incomplete items.
        """
        logger.warning("Using refinement fallback - generic clarification questions")
        
        questions = []
        question_id = 1
        
        for item in action_items:
            if not item.owner:
                questions.append({
                    "question_id": question_id,
                    "question": f"Who should be responsible for: {item.description}?",
                    "field": "owner",
                    "action_item_id": item.id,
                    "priority": "critical"
                })
                question_id += 1
            
            if not item.deadline:
                questions.append({
                    "question_id": question_id,
                    "question": f"What is the deadline for: {item.description}?",
                    "field": "deadline",
                    "action_item_id": item.id,
                    "priority": "high"
                })
                question_id += 1
        
        from models import ClarificationQuestion
        return ClarificationQuestionsOutput(
            questions=[ClarificationQuestion(**q) for q in questions]
        )


# === SAFE AGENT WRAPPERS ===

T = TypeVar('T')

async def safe_agent_call(
    agent_func: Callable[..., Any],
    fallback_func: Callable[..., T],
    *args,
    **kwargs
) -> T:
    """
    Safely execute an agent call with retry and fallback.
    
    Args:
        agent_func: The agent function to call (with @retry_agent_call decorator)
        fallback_func: Fallback function to use if all retries fail
        *args: Arguments to pass to agent_func
        **kwargs: Keyword arguments to pass to agent_func
        
    Returns:
        Result from agent_func or fallback_func
    """
    try:
        # Try the agent call (will retry automatically)
        result = await agent_func(*args, **kwargs)
        return result
    
    except (ModelHTTPError, UnexpectedModelBehavior, ValidationError) as e:
        logger.error(
            f"Agent call failed after all retries: {agent_func.__name__}",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "fallback_used": True
            }
        )
        
        # Use fallback strategy
        return fallback_func(*args, **kwargs)
    
    except Exception as e:
        logger.error(
            f"Unexpected error in agent call: {agent_func.__name__}",
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "fallback_used": True
            }
        )
        
        # Use fallback for any unexpected errors
        return fallback_func(*args, **kwargs)


def log_retry_attempt(retry_state):
    """Log retry attempts for debugging."""
    logger.warning(
        "Retrying agent call",
        extra={
            "attempt": retry_state.attempt_number,
            "wait_time": retry_state.next_action.sleep if hasattr(retry_state.next_action, 'sleep') else 0,
            "error": str(retry_state.outcome.exception()) if retry_state.outcome.failed else None
        }
    )


# === ERROR CONTEXT MANAGERS ===

class AgentErrorContext:
    """
    Context manager for handling agent errors gracefully.
    
    Usage:
        async with AgentErrorContext("extraction", fallback_func):
            result = await agent.run(prompt)
    """
    
    def __init__(self, agent_name: str, fallback_func: Optional[Callable] = None):
        self.agent_name = agent_name
        self.fallback_func = fallback_func
        self.result = None
    
    async def __aenter__(self):
        logger.debug(f"Starting {self.agent_name} agent")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                f"{self.agent_name} agent failed",
                extra={
                    "error_type": exc_type.__name__,
                    "error_message": str(exc_val),
                    "has_fallback": self.fallback_func is not None
                }
            )
            
            if self.fallback_func:
                logger.info(f"Using fallback for {self.agent_name}")
                return True  # Suppress exception
        
        return False  # Let exception propagate if no fallback


# === VALIDATION HELPERS ===

def validate_agent_output(output: Any, expected_type: type) -> bool:
    """
    Validate that agent output matches expected schema.
    
    Args:
        output: The output to validate
        expected_type: Expected Pydantic model type
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not isinstance(output, expected_type):
            logger.warning(
                f"Agent output type mismatch",
                extra={
                    "expected": expected_type.__name__,
                    "actual": type(output).__name__
                }
            )
            return False
        
        # Additional validation checks
        if hasattr(output, 'model_validate'):
            output.model_validate(output.model_dump())
        
        return True
    
    except ValidationError as e:
        logger.error(
            "Agent output validation failed",
            extra={
                "errors": e.errors(),
                "output_type": type(output).__name__
            }
        )
        return False


def sanitize_agent_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize input text for agent processing.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        logger.warning(
            f"Input text truncated from {len(text)} to {max_length} chars"
        )
        text = text[:max_length] + "... [truncated]"
    
    # Remove potentially problematic characters
    text = text.replace('\x00', '')  # Null bytes
    
    return text
