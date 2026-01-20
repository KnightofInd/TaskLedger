"""
PydanticAI Agents for TaskLedger.
Implements the multi-agent pipeline for meeting-to-action conversion.

Pipeline Flow:
1. Extraction Agent → raw action descriptions
2. Attribution Agent → adds owner/deadline (only if explicit)
3. Validation Agent → adds risk flags and confidence scores
4. Refinement Agent → generates clarification questions (separate file)
"""
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from typing import List
from datetime import date

from models import (
    ExtractionOutput,
    AttributionOutput,
    ValidationOutput,
    ActionItem,
    RiskFlag,
    RiskType,
    Priority,
    ConfidenceLevel
)
from config import settings
from logger import logger
from retry_utils import (
    retry_agent_call,
    safe_agent_call,
    FallbackStrategies,
    sanitize_agent_input,
    validate_agent_output
)


# === GEMINI MODEL CONFIGURATION ===

def create_gemini_model() -> GeminiModel:
    """
    Create Google Gemini model.
    Uses Gemini 2.0 Flash via Google AI Studio API.
    The API key is loaded from GEMINI_API_KEY environment variable.
    """
    import os
    # Set the API key as environment variable for PydanticAI
    os.environ['GEMINI_API_KEY'] = settings.gemini_api_key
    
    return GeminiModel(
        model_name=settings.gemini_model
    )


# === AGENT 1: EXTRACTION ===

extraction_agent = Agent(
    model=create_gemini_model(),
    output_type=ExtractionOutput,
    system_prompt="""You are an expert at extracting action items from meeting notes.

Your task:
- Identify ALL actionable tasks mentioned in the meeting
- Extract ONLY the task description (what needs to be done)
- Do NOT infer or assign owners
- Do NOT infer or add deadlines
- Do NOT add your own interpretation
- Keep descriptions concise but complete
- Each action should be a single, clear task

Examples of good extractions:
- "Implement user authentication system"
- "Review API documentation for accuracy"
- "Schedule follow-up meeting with stakeholders"

What NOT to include:
- Discussion points without action
- General observations
- Questions unless they require specific action

Return a list of raw action descriptions."""
)


@retry_agent_call(max_attempts=3, initial_wait=1.0)
async def _run_extraction_with_retry(meeting_text: str) -> ExtractionOutput:
    """Internal extraction function with retry logic."""
    sanitized_text = sanitize_agent_input(meeting_text)
    
    result = await extraction_agent.run(
        f"Extract action items from this meeting:\n\n{sanitized_text}"
    )
    
    # Validate output
    if not validate_agent_output(result.output, ExtractionOutput):
        raise ValueError("Invalid extraction output schema")
    
    return result.output


async def run_extraction_agent(meeting_text: str) -> ExtractionOutput:
    """
    Run the Extraction Agent on meeting notes with retry and fallback.
    
    Args:
        meeting_text: Raw meeting notes or transcript
        
    Returns:
        ExtractionOutput with list of raw action descriptions
    """
    logger.info("Running Extraction Agent", extra={"meeting_length": len(meeting_text)})
    
    result = await safe_agent_call(
        _run_extraction_with_retry,
        FallbackStrategies.extraction_fallback,
        meeting_text
    )
    
    logger.info(
        "Extraction Agent completed",
        extra={
            "actions_found": len(result.raw_actions),
            "used_fallback": len(result.raw_actions) == 1 and "Review meeting notes" in result.raw_actions[0]
        }
    )
    
    return result


# === AGENT 2: ATTRIBUTION ===

attribution_agent = Agent(
    model=create_gemini_model(),
    output_type=AttributionOutput,
    system_prompt="""You are an expert at attributing action items to owners and deadlines.

CRITICAL RULES:
1. ONLY assign an owner if EXPLICITLY mentioned in the meeting text
   - Look for phrases like "Alice will...", "Bob is responsible for...", "assigned to Charlie"
   - Do NOT guess or infer based on context
   - If unclear, leave owner as null

2. ONLY assign a deadline if EXPLICITLY stated
   - Look for specific dates or timeframes mentioned
   - Accept formats like "by Jan 30", "end of week", "next Friday"
   - Do NOT infer based on urgency or context
   - If unclear, leave deadline as null

3. For each action item, provide:
   - description: the task to be done
   - owner: person's name (null if not explicit)
   - deadline: date in YYYY-MM-DD format (null if not explicit)
   - context: relevant surrounding information from the meeting

Examples:
Meeting: "Alice will implement auth by Jan 30"
→ owner: "Alice", deadline: "2026-01-30"

Meeting: "Someone needs to review the docs"
→ owner: null, deadline: null

Meeting: "We should fix the bug soon"
→ owner: null, deadline: null

When in doubt, leave it null. It's better to flag for clarification than to guess."""
)


@retry_agent_call(max_attempts=3, initial_wait=1.0)
async def _run_attribution_with_retry(
    raw_actions: List[str],
    meeting_text: str,
    participants: List[str]
) -> AttributionOutput:
    """Internal attribution function with retry logic."""
    sanitized_text = sanitize_agent_input(meeting_text)
    
    prompt = f"""Meeting Participants: {', '.join(participants) if participants else 'Unknown'}

Original Meeting Notes:
{sanitized_text}

Action Items to Attribute:
{chr(10).join(f'{i+1}. {action}' for i, action in enumerate(raw_actions))}

For each action item, determine if an owner or deadline is EXPLICITLY mentioned.
Remember: Only assign if clearly stated. When in doubt, leave as null."""

    result = await attribution_agent.run(prompt)
    
    # Validate output
    if not validate_agent_output(result.output, AttributionOutput):
        raise ValueError("Invalid attribution output schema")
    
    return result.output


async def run_attribution_agent(
    raw_actions: List[str],
    meeting_text: str,
    participants: List[str]
) -> AttributionOutput:
    """
    Run the Attribution Agent to add owner and deadline info with retry and fallback.
    
    Args:
        raw_actions: List of action descriptions from Extraction Agent
        meeting_text: Original meeting text for context
        participants: List of meeting participant names
        
    Returns:
        AttributionOutput with action items including owner/deadline
    """
    logger.info(
        "Running Attribution Agent",
        extra={
            "action_count": len(raw_actions),
            "participant_count": len(participants)
        }
    )
    
    result = await safe_agent_call(
        _run_attribution_with_retry,
        FallbackStrategies.attribution_fallback,
        raw_actions,
        meeting_text,
        participants
    )
    
    logger.info(
        "Attribution Agent completed",
        extra={
            "items_with_owner": sum(1 for item in result.action_items if item.owner),
            "items_with_deadline": sum(1 for item in result.action_items if item.deadline),
            "used_fallback": all(item.confidence == ConfidenceLevel.LOW for item in result.action_items)
        }
    )
    
    return result


# === AGENT 3: VALIDATION ===

validation_agent = Agent(
    model=create_gemini_model(),
    output_type=ValidationOutput,
    system_prompt="""You are an expert at validating action items and identifying risks.

Your task:
1. Analyze each action item for potential issues
2. Assign risk flags for problems that need clarification
3. Calculate confidence scores (0.0 - 1.0)
4. Assign priority levels

RISK TYPES TO CHECK:

1. vague_description
   - Task is unclear or ambiguous
   - Missing specific details about what needs to be done
   - Could be interpreted in multiple ways

2. missing_owner
   - No person assigned to the task
   - Creates accountability issues

3. missing_deadline
   - No timeline specified
   - Could be deprioritized indefinitely

4. unclear_dependency
   - Task mentions depending on something not clearly defined
   - Blocking issues not well specified

5. scope_too_broad
   - Task is too large or complex
   - Should be broken into smaller items
   - Would take more than a week to complete

6. conflicting_assignment
   - Owner might be overloaded
   - Multiple critical tasks assigned to same person

CONFIDENCE SCORING:
- HIGH (0.71-1.0): Clear task, explicit owner, specific deadline, no ambiguity
- MEDIUM (0.41-0.70): Most info present, minor clarification needed
- LOW (0.0-0.40): Significant missing info, vague description, needs clarification

PRIORITY ASSIGNMENT:
- CRITICAL: Urgent, blocking other work, security/data loss risk
- HIGH: Important for project success, clear deadline within 1 week
- MEDIUM: Standard work items, moderate importance
- LOW: Nice-to-have, no immediate deadline

For each risk flag, provide:
- risk_type: one of the types above
- description: specific explanation of the issue
- severity: how critical the risk is
- suggested_clarification: question to ask user to resolve

Be thorough but fair. Don't flag minor issues."""
)


@retry_agent_call(max_attempts=3, initial_wait=1.0)
async def _run_validation_with_retry(action_items: List[ActionItem]) -> ValidationOutput:
    """Internal validation function with retry logic."""
    # Prepare items for validation
    items_summary = []
    for i, item in enumerate(action_items, 1):
        summary = f"{i}. {item.description}"
        if item.owner:
            summary += f" (Owner: {item.owner})"
        if item.deadline:
            summary += f" (Deadline: {item.deadline})"
        items_summary.append(summary)
    
    prompt = f"""Validate these action items and identify risks:

{chr(10).join(items_summary)}

For each item:
1. Identify any risk flags that need attention
2. Calculate a confidence score (0.0-1.0)
3. Set appropriate priority level
4. Provide clarification questions for flagged items

Return validated items with all fields populated."""

    result = await validation_agent.run(prompt)
    
    # Validate output
    if not validate_agent_output(result.output, ValidationOutput):
        raise ValueError("Invalid validation output schema")
    
    return result.output


async def run_validation_agent(action_items: List[ActionItem]) -> ValidationOutput:
    """
    Run the Validation Agent to add risk flags and confidence scores with retry and fallback.
    
    Args:
        action_items: List of action items with attribution
        
    Returns:
        ValidationOutput with validated items including risk flags
    """
    logger.info(
        "Running Validation Agent",
        extra={"item_count": len(action_items)}
    )
    
    result = await safe_agent_call(
        _run_validation_with_retry,
        FallbackStrategies.validation_fallback,
        action_items
    )
    
    total_risks = sum(len(item.risk_flags) for item in result.validated_items)
    
    logger.info(
        "Validation Agent completed",
        extra={
            "total_risks": total_risks,
            "avg_confidence": result.overall_confidence,
            "used_fallback": all(item.confidence == ConfidenceLevel.LOW for item in result.validated_items)
        }
    )
    
    return result


# === ORCHESTRATOR ===

async def run_full_pipeline(
    meeting_text: str,
    participants: List[str]
) -> ValidationOutput:
    """
    Run the complete agent pipeline:
    Extraction → Attribution → Validation
    
    Args:
        meeting_text: Raw meeting notes
        participants: List of participant names
        
    Returns:
        ValidationOutput with fully processed action items
    """
    logger.info("Starting full agent pipeline")
    
    # Step 1: Extract raw actions
    extraction_result = await run_extraction_agent(meeting_text)
    
    if not extraction_result.raw_actions:
        logger.warning("No actions extracted from meeting")
        return ValidationOutput(validated_items=[], overall_confidence=0.0)
    
    # Step 2: Attribute owners and deadlines
    attribution_result = await run_attribution_agent(
        raw_actions=extraction_result.raw_actions,
        meeting_text=meeting_text,
        participants=participants
    )
    
    # Step 3: Validate and add risk flags
    validation_result = await run_validation_agent(
        action_items=attribution_result.action_items
    )
    
    logger.info(
        "Full pipeline completed",
        extra={
            "total_items": len(validation_result.validated_items),
            "overall_confidence": validation_result.overall_confidence
        }
    )
    
    return validation_result


# === HELPER FUNCTIONS ===

def calculate_overall_confidence(items: List[ActionItem]) -> float:
    """Calculate average confidence across all action items."""
    if not items:
        return 0.0
    return sum(item.confidence_score for item in items) / len(items)


def get_high_risk_items(items: List[ActionItem]) -> List[ActionItem]:
    """Get items with 2 or more risk flags."""
    return [item for item in items if len(item.risk_flags) >= 2]


def get_items_by_priority(items: List[ActionItem], priority: Priority) -> List[ActionItem]:
    """Filter items by priority level."""
    return [item for item in items if item.priority == priority]
