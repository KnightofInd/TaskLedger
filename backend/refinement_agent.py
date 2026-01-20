"""
Refinement Agent for TaskLedger.
Handles clarification requests and partial pipeline re-runs.

This agent:
1. Generates targeted clarification questions for incomplete action items
2. Processes user responses to clarification questions
3. Re-runs only the affected parts of the pipeline
4. Updates action items with newly clarified information
"""
from typing import List, Dict, Optional
from datetime import date, datetime

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel

from models import (
    ActionItem,
    ClarificationQuestion,
    ClarificationQuestionsOutput,
    UserClarificationAnswers,
    ValidationOutput,
    RiskType,
    Priority,
    ConfidenceLevel
)
from config import settings
from logger import logger


# === GEMINI MODEL (Reuse from agents.py) ===

def create_gemini_model() -> GeminiModel:
    """Create Google Gemini model for refinement."""
    import os
    os.environ['GEMINI_API_KEY'] = settings.gemini_api_key
    return GeminiModel(model_name=settings.gemini_model)


# === AGENT 4: REFINEMENT ===

refinement_agent = Agent(
    model=create_gemini_model(),
    output_type=ClarificationQuestionsOutput,
    system_prompt="""You are an expert at generating clarification questions for incomplete action items.

Your task:
1. Analyze action items with risk flags or low confidence
2. Generate specific, actionable questions that will resolve ambiguity
3. Prioritize the most critical missing information

Question Guidelines:
- Be specific and direct
- Focus on one piece of information per question
- Use the context from the meeting to guide the question
- Make questions easy to answer (yes/no, specific date, person name)

Priority for questions:
1. Missing owner (who will do it?)
2. Missing deadline (when is it due?)
3. Vague description (what specifically needs to be done?)
4. Unclear dependencies (what does this depend on?)

Examples of good questions:
- "Who will be responsible for implementing OAuth2 authentication?"
- "What is the target completion date for the API documentation update?"
- "Which specific endpoints need performance profiling?"
- "Does the security review need to happen before or after user database integration?"

Return a structured list of questions prioritized by importance."""
)


# === CLARIFICATION GENERATION ===

async def generate_clarification_questions(
    action_items: List[ActionItem],
    meeting_context: str
) -> ClarificationQuestionsOutput:
    """
    Generate clarification questions for action items that need more information.
    
    Args:
        action_items: List of action items to analyze
        meeting_context: Original meeting notes for context
        
    Returns:
        ClarificationRequest with prioritized questions
    """
    logger.info(
        "Generating clarification questions",
        extra={
            "total_items": len(action_items),
            "items_needing_clarification": sum(1 for item in action_items if item.needs_clarification)
        }
    )
    
    # Filter items that need clarification
    items_needing_clarification = [
        item for item in action_items if item.needs_clarification
    ]
    
    if not items_needing_clarification:
        logger.info("No items need clarification")
        return ClarificationQuestionsOutput(questions=[])
    
    # Build prompt with context
    items_text = "\n".join([
        f"Item {item.id}: {item.description}\n"
        f"  Owner: {item.owner or 'NOT ASSIGNED'}\n"
        f"  Deadline: {item.deadline or 'NOT SET'}\n"
        f"  Risks: {', '.join(r.risk_type.value for r in item.risk_flags)}\n"
        f"  Confidence: {item.confidence.value.upper()}"
        for item in items_needing_clarification
    ])
    
    prompt = f"""Meeting Context:
{meeting_context}

Action Items Needing Clarification:
{items_text}

Generate clarification questions to resolve the missing or unclear information.
Focus on the most critical gaps first."""

    result = await refinement_agent.run(prompt)
    
    logger.info(
        "Clarification questions generated",
        extra={"question_count": len(result.output.questions)}
    )
    
    return result.output


# === CLARIFICATION PROCESSING ===

def parse_user_responses(
    questions: List[ClarificationQuestion],
    responses: Dict[int, str]
) -> UserClarificationAnswers:
    """
    Parse user responses to clarification questions.
    
    Args:
        questions: List of questions that were asked
        responses: Dict mapping question IDs to user answers
        
    Returns:
        ClarificationResponse with parsed answers
    """
    logger.info(
        "Parsing user responses",
        extra={
            "questions_asked": len(questions),
            "responses_received": len(responses)
        }
    )
    
    # Map responses back to questions
    answered_questions = []
    for question in questions:
        if question.question_id in responses:
            answered_questions.append({
                "question_id": question.question_id,
                "action_item_id": question.action_item_id,
                "field": question.field,
                "answer": responses[question.question_id]
            })
    
    return UserClarificationAnswers(
        answers=answered_questions,
        timestamp=datetime.now()
    )


# === PARTIAL PIPELINE RE-RUN ===

async def apply_clarifications(
    action_items: List[ActionItem],
    clarification_response: UserClarificationAnswers
) -> List[ActionItem]:
    """
    Apply user clarifications to action items and update them.
    
    This performs a partial re-run:
    1. Update action items with clarified information
    2. Recalculate confidence scores
    3. Remove resolved risk flags
    4. Keep unchanged items as-is
    
    Args:
        action_items: Original list of action items
        clarification_response: User's answers to clarification questions
        
    Returns:
        Updated list of action items
    """
    logger.info(
        "Applying clarifications",
        extra={"clarification_count": len(clarification_response.answers)}
    )
    
    # Create a mutable copy
    updated_items = [item.model_copy(deep=True) for item in action_items]
    
    # Apply each clarification
    for answer in clarification_response.answers:
        item_id = answer["action_item_id"]
        field = answer["field"]
        value = answer["answer"]
        
        # Find the item to update
        item = next((i for i in updated_items if i.id == item_id), None)
        if not item:
            logger.warning(f"Item {item_id} not found")
            continue
        
        # Update the appropriate field
        if field == "owner":
            item.owner = value
            # Remove missing_owner risk
            item.risk_flags = [r for r in item.risk_flags if r.risk_type != RiskType.MISSING_OWNER]
            logger.info(f"Updated item {item_id} owner to: {value}")
            
        elif field == "deadline":
            # Parse deadline (assume format: YYYY-MM-DD or natural language)
            try:
                if isinstance(value, str):
                    # Try parsing date
                    item.deadline = datetime.strptime(value, "%Y-%m-%d").date()
                else:
                    item.deadline = value
                # Remove missing_deadline risk
                item.risk_flags = [r for r in item.risk_flags if r.risk_type != RiskType.MISSING_DEADLINE]
                logger.info(f"Updated item {item_id} deadline to: {value}")
            except ValueError:
                logger.warning(f"Could not parse deadline: {value}")
                
        elif field == "description":
            item.description = value
            # Remove vague_description risk
            item.risk_flags = [r for r in item.risk_flags if r.risk_type != RiskType.VAGUE_DESCRIPTION]
            logger.info(f"Updated item {item_id} description")
        
        # Recalculate confidence score
        item.confidence = _calculate_confidence(item)
    
    logger.info(
        "Clarifications applied",
        extra={
            "items_updated": len([a for a in clarification_response.answers]),
            "remaining_risks": sum(len(i.risk_flags) for i in updated_items)
        }
    )
    
    return updated_items


def _calculate_confidence(item: ActionItem) -> ConfidenceLevel:
    """
    Calculate confidence level based on completeness.
    
    Logic:
    - Base: 0.5
    - +0.35 if owner assigned
    - +0.25 if deadline set
    - +0.10 if description is clear (>10 chars)
    - -0.10 per risk flag
    """
    score = 0.5
    
    if item.owner:
        score += 0.35
    if item.deadline:
        score += 0.25
    if len(item.description) > 10:
        score += 0.10
    
    score -= len(item.risk_flags) * 0.10
    
    # Clamp to 0-1
    score = max(0.0, min(1.0, score))
    
    # Map to confidence level
    if score >= 0.75:
        return ConfidenceLevel.HIGH
    elif score >= 0.50:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW


# === FULL REFINEMENT WORKFLOW ===

async def run_refinement_workflow(
    action_items: List[ActionItem],
    meeting_context: str,
    user_responses: Optional[Dict[int, str]] = None
) -> tuple[List[ActionItem], Optional[ClarificationQuestionsOutput]]:
    """
    Complete refinement workflow:
    1. Generate clarification questions (if not provided with responses)
    2. Apply user responses if available
    3. Return updated items and any remaining questions
    
    Args:
        action_items: Action items to refine
        meeting_context: Original meeting notes
        user_responses: Optional dict of question_id -> answer
        
    Returns:
        Tuple of (updated_items, remaining_questions)
    """
    logger.info("Starting refinement workflow")
    
    # Generate questions for items needing clarification
    clarification_request = await generate_clarification_questions(
        action_items,
        meeting_context
    )
    
    # If user provided responses, apply them
    if user_responses:
        clarification_response = parse_user_responses(
            clarification_request.questions,
            user_responses
        )
        
        updated_items = await apply_clarifications(
            action_items,
            clarification_response
        )
        
        # Check if more clarifications are still needed
        remaining_questions = await generate_clarification_questions(
            updated_items,
            meeting_context
        )
        
        logger.info(
            "Refinement workflow completed",
            extra={
                "items_updated": len(user_responses),
                "remaining_questions": len(remaining_questions.questions)
            }
        )
        
        return updated_items, remaining_questions if remaining_questions.questions else None
    
    # No responses yet, return original items with questions
    logger.info("Returning initial clarification questions")
    return action_items, clarification_request
