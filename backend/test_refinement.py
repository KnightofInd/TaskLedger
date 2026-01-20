"""
Test script for the Refinement Agent.
Tests clarification question generation and partial re-run functionality.
"""
import asyncio
from datetime import date

from models import ActionItem, RiskFlag, RiskType, Priority, ConfidenceLevel
from refinement_agent import (
    generate_clarification_questions,
    parse_user_responses,
    apply_clarifications,
    run_refinement_workflow
)


# Sample action items with missing information
SAMPLE_ITEMS = [
    ActionItem(
        id="1",
        description="Implement OAuth2 authentication",
        owner="Alice",
        deadline=date(2026, 1, 30),
        priority=Priority.HIGH,
        confidence=ConfidenceLevel.HIGH,
        confidence_score=0.85,
        risk_flags=[]  # Complete item
    ),
    ActionItem(
        id="2",
        description="Integrate with existing user database",
        owner=None,
        deadline=None,
        priority=Priority.MEDIUM,
        confidence=ConfidenceLevel.MEDIUM,
        confidence_score=0.50,
        risk_flags=[
            RiskFlag(
                risk_type=RiskType.MISSING_OWNER,
                description="No owner assigned",
                severity=Priority.HIGH,
                suggested_clarification="Who is responsible for integrating with the existing user database?"
            ),
            RiskFlag(
                risk_type=RiskType.MISSING_DEADLINE,
                description="No deadline specified",
                severity=Priority.MEDIUM,
                suggested_clarification="What is the deadline for the user database integration?"
            )
        ]
    ),
    ActionItem(
        id="3",
        description="Profile critical endpoints",
        owner="Bob",
        deadline=None,
        priority=Priority.HIGH,
        confidence=ConfidenceLevel.MEDIUM,
        confidence_score=0.65,
        risk_flags=[
            RiskFlag(
                risk_type=RiskType.MISSING_DEADLINE,
                description="No deadline specified",
                severity=Priority.MEDIUM,
                suggested_clarification="What is the deadline for profiling critical endpoints?"
            ),
            RiskFlag(
                risk_type=RiskType.VAGUE_DESCRIPTION,
                description="Description lacks specifics",
                severity=Priority.HIGH,
                suggested_clarification="Which specific endpoints need profiling?"
            )
        ]
    ),
    ActionItem(
        id="4",
        description="Security review",
        owner=None,
        deadline=None,
        priority=Priority.CRITICAL,
        confidence=ConfidenceLevel.LOW,
        confidence_score=0.35,
        risk_flags=[
            RiskFlag(
                risk_type=RiskType.MISSING_OWNER,
                description="No owner assigned",
                severity=Priority.CRITICAL,
                suggested_clarification="Who will conduct the security review?"
            ),
            RiskFlag(
                risk_type=RiskType.MISSING_DEADLINE,
                description="No deadline specified",
                severity=Priority.CRITICAL,
                suggested_clarification="What is the deadline for the security review?"
            ),
            RiskFlag(
                risk_type=RiskType.VAGUE_DESCRIPTION,
                description="Description lacks specifics",
                severity=Priority.HIGH,
                suggested_clarification="What should the security review cover?"
            )
        ]
    )
]

MEETING_CONTEXT = """
Q1 2026 Planning Meeting - January 20, 2026
Attendees: Alice (Auth Lead), Bob (Performance Engineer), Carol (Backend), David (Security)

Meeting Notes:
Alice will implement OAuth2 authentication by end of January.
We need to integrate with the existing user database.
Bob will profile the critical endpoints by Friday.
Security review is needed before launch.
Documentation updates are required.
Cache layer for frequently accessed data.
Metrics dashboard for team visibility.
"""


async def test_clarification_generation():
    """Test generating clarification questions."""
    print("=" * 80)
    print("TEST 1: Generating Clarification Questions")
    print("=" * 80)
    
    request = await generate_clarification_questions(SAMPLE_ITEMS, MEETING_CONTEXT)
    
    print(f"\n✓ Generated {len(request.questions)} questions\n")
    
    for q in request.questions:
        print(f"Q{q.question_id}: {q.question}")
        print(f"   → For Item #{q.action_item_id}: {q.field}")
        print(f"   → Priority: {q.priority.upper()}")
        print()
    
    return request


async def test_apply_clarifications():
    """Test applying user responses."""
    print("=" * 80)
    print("TEST 2: Applying Clarifications")
    print("=" * 80)
    
    # First get questions
    request = await generate_clarification_questions(SAMPLE_ITEMS, MEETING_CONTEXT)
    
    # Simulate user responses
    print("\nSimulated User Responses:")
    user_responses = {
        1: "Carol",  # Owner for item 2
        2: "2026-02-05",  # Deadline for item 2
        3: "2026-01-25",  # Deadline for item 3
        4: "David"  # Owner for item 4
    }
    
    for qid, answer in user_responses.items():
        question = next((q for q in request.questions if q.question_id == qid), None)
        if question:
            print(f"  Q{qid}: {question.question}")
            print(f"  A{qid}: {answer}\n")
    
    # Parse responses
    clarification_response = parse_user_responses(request.questions, user_responses)
    
    print(f"✓ Parsed {len(clarification_response.answers)} answers")
    
    # Apply clarifications
    updated_items = await apply_clarifications(SAMPLE_ITEMS, clarification_response)
    
    print("\nUpdated Action Items:")
    print("-" * 80)
    for item in updated_items:
        print(f"\nItem {item.id}: {item.description}")
        print(f"  Owner: {item.owner or 'NOT ASSIGNED'}")
        print(f"  Deadline: {item.deadline or 'NOT SET'}")
        print(f"  Confidence: {item.confidence.value.upper()} ({_confidence_percentage(item.confidence)})")
        print(f"  Risk Flags: {len(item.risk_flags)}")
        print(f"  Needs Clarification: {item.needs_clarification}")
    
    return updated_items


async def test_full_workflow():
    """Test complete refinement workflow."""
    print("\n" + "=" * 80)
    print("TEST 3: Full Refinement Workflow")
    print("=" * 80)
    
    # Run without responses first
    print("\nStep 1: Initial clarification request")
    items, questions = await run_refinement_workflow(
        SAMPLE_ITEMS,
        MEETING_CONTEXT
    )
    
    print(f"✓ Generated {len(questions.questions)} initial questions")
    
    # Simulate user providing some answers
    print("\nStep 2: User provides partial answers")
    user_responses = {
        1: "Carol",
        2: "2026-02-05"
    }
    
    items, remaining = await run_refinement_workflow(
        SAMPLE_ITEMS,
        MEETING_CONTEXT,
        user_responses
    )
    
    if remaining:
        print(f"✓ Applied clarifications, {len(remaining.questions)} questions remain")
    else:
        print("✓ All clarifications resolved!")
    
    # Show final state
    print("\nFinal State:")
    print("-" * 80)
    complete_items = [i for i in items if i.is_complete]
    incomplete_items = [i for i in items if not i.is_complete]
    
    print(f"Complete Items: {len(complete_items)}/{len(items)}")
    print(f"Incomplete Items: {len(incomplete_items)}/{len(items)}")
    print(f"Overall Confidence: {_avg_confidence(items)}")
    print(f"Total Risk Flags: {sum(len(i.risk_flags) for i in items)}")


def _confidence_percentage(confidence: ConfidenceLevel) -> str:
    """Convert confidence level to percentage."""
    mapping = {
        ConfidenceLevel.LOW: "0-50%",
        ConfidenceLevel.MEDIUM: "50-75%",
        ConfidenceLevel.HIGH: "75-100%"
    }
    return mapping.get(confidence, "Unknown")


def _avg_confidence(items: list[ActionItem]) -> str:
    """Calculate average confidence as percentage."""
    mapping = {
        ConfidenceLevel.LOW: 0.25,
        ConfidenceLevel.MEDIUM: 0.625,
        ConfidenceLevel.HIGH: 0.875
    }
    avg = sum(mapping.get(i.confidence, 0.5) for i in items) / len(items)
    return f"{int(avg * 100)}%"


async def main():
    """Run all tests."""
    print("\n" + "🔄" * 40)
    print("REFINEMENT AGENT TEST SUITE")
    print("🔄" * 40 + "\n")
    
    try:
        await test_clarification_generation()
        await test_apply_clarifications()
        await test_full_workflow()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
