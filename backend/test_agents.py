"""
Test script for agent pipeline.
Run with: python test_agents.py
"""
import asyncio
from agents import run_full_pipeline
from logger import logger


# Test meeting notes
TEST_MEETING = """
Team Meeting - Q1 Planning
Date: January 19, 2026
Attendees: Alice, Bob, Charlie, Dana

Discussion Points:

1. Authentication System
   - Alice will implement OAuth2 authentication by January 30th
   - Need to integrate with existing user database
   - Bob mentioned security review is required before deployment

2. API Documentation
   - Someone needs to review and update the API docs
   - Current documentation is outdated
   - Should include examples for each endpoint

3. Performance Issues
   - Charlie raised concerns about database query performance
   - Need to investigate slow queries
   - Bob will profile the most used endpoints this week

4. Mobile App
   - Dana suggested we should start planning the mobile app
   - No timeline discussed yet
   - Requires research on React Native vs Flutter

5. Bug Fixes
   - Fix the login redirect bug ASAP
   - Address the email notification issues
   - Charlie mentioned users are complaining about slow load times

Next meeting scheduled for next Friday.
"""


async def test_pipeline():
    """Test the full agent pipeline with sample meeting notes."""
    
    print("\n" + "="*80)
    print("TESTING AGENT PIPELINE")
    print("="*80 + "\n")
    
    participants = ["Alice", "Bob", "Charlie", "Dana"]
    
    try:
        # Run the full pipeline
        result = await run_full_pipeline(
            meeting_text=TEST_MEETING,
            participants=participants
        )
        
        print(f"\n📊 RESULTS SUMMARY")
        print("-" * 80)
        print(f"Total Action Items: {len(result.validated_items)}")
        print(f"Overall Confidence: {result.overall_confidence:.2%}")
        print()
        
        # Display each action item
        for i, item in enumerate(result.validated_items, 1):
            print(f"\n🎯 ACTION ITEM #{i}")
            print(f"   Description: {item.description}")
            print(f"   Owner: {item.owner or 'NOT ASSIGNED ⚠️'}")
            print(f"   Deadline: {item.deadline or 'NOT SET ⚠️'}")
            print(f"   Priority: {item.priority.value.upper()}")
            print(f"   Confidence: {item.confidence.value.upper()} ({item.confidence_score:.2%})")
            
            if item.risk_flags:
                print(f"   ⚠️  RISK FLAGS ({len(item.risk_flags)}):")
                for risk in item.risk_flags:
                    print(f"      • {risk.risk_type.value}: {risk.description}")
                    if risk.suggested_clarification:
                        print(f"        → Question: {risk.suggested_clarification}")
            else:
                print(f"   ✅ No risks identified")
            
            if item.context:
                print(f"   Context: {item.context}")
        
        # Summary statistics
        print("\n" + "="*80)
        print("📈 STATISTICS")
        print("-" * 80)
        
        items_with_owner = sum(1 for item in result.validated_items if item.owner)
        items_with_deadline = sum(1 for item in result.validated_items if item.deadline)
        total_risks = sum(len(item.risk_flags) for item in result.validated_items)
        items_needing_clarification = sum(1 for item in result.validated_items if item.risk_flags)
        
        print(f"Items with Owner: {items_with_owner}/{len(result.validated_items)}")
        print(f"Items with Deadline: {items_with_deadline}/{len(result.validated_items)}")
        print(f"Total Risk Flags: {total_risks}")
        print(f"Items Needing Clarification: {items_needing_clarification}")
        
        # Priority breakdown
        from models import Priority
        for priority in Priority:
            count = sum(1 for item in result.validated_items if item.priority == priority)
            if count > 0:
                print(f"{priority.value.capitalize()} Priority: {count}")
        
        print("\n" + "="*80)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        print(f"\n❌ TEST FAILED: {str(e)}\n")
        raise


if __name__ == "__main__":
    asyncio.run(test_pipeline())
