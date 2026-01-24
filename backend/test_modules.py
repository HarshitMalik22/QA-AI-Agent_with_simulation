"""
Quick test script to verify all modules work correctly.
Run with: python test_modules.py
"""

from modules.auto_qa import AutoQAAnalyzer
from modules.decision_extractor import DecisionExtractor
from modules.digital_twin import DigitalTwinSimulator
from modules.counterfactual import CounterfactualComparator
from modules.insight_generator import InsightGenerator
from data.mock_data import MOCK_STATIONS, MOCK_TRANSCRIPTS

def test_pipeline():
    """Test the complete pipeline with a sample transcript"""
    
    # Initialize modules
    auto_qa = AutoQAAnalyzer()
    decision_extractor = DecisionExtractor()
    digital_twin = DigitalTwinSimulator(MOCK_STATIONS)
    counterfactual = CounterfactualComparator(digital_twin)
    insight_generator = InsightGenerator()
    
    # Use first sample transcript
    sample = MOCK_TRANSCRIPTS[0]
    transcript = sample["transcript"]
    call_id = sample["call_id"]
    driver_location = sample.get("driver_location")
    
    print("=" * 60)
    print("Testing QA-Driven Digital Twin Pipeline")
    print("=" * 60)
    print(f"\nCall ID: {call_id}")
    print(f"\nTranscript:\n{transcript[:200]}...")
    print("\n" + "=" * 60)
    
    # Step 1: Auto-QA
    print("\n1. Auto-QA Analysis:")
    qa_result = auto_qa.analyze(transcript)
    print(f"   Issue Detected: {qa_result['issue_detected']}")
    print(f"   Decision Type: {qa_result.get('decision_type', 'N/A')}")
    print(f"   Reason: {qa_result.get('reason', 'N/A')}")
    print(f"   Confidence: {qa_result.get('confidence', 0):.2f}")
    
    # Step 2: Extract decision
    print("\n2. Decision Extraction:")
    actual_decision = decision_extractor.extract(transcript, qa_result, driver_location)
    print(f"   Decision Type: {actual_decision['decision_type']}")
    print(f"   Details: {actual_decision.get('details', {})}")
    
    # Step 3: Generate alternatives
    print("\n3. Generating Alternatives:")
    alternatives = []
    if qa_result.get("issue_detected"):
        alternatives = counterfactual.generate_alternatives(
            actual_decision, transcript, driver_location
        )
        print(f"   Generated {len(alternatives)} alternatives")
        for i, alt in enumerate(alternatives, 1):
            print(f"   Alt {i}: {alt.get('description', 'N/A')}")
    
    # Step 4: Compare
    print("\n4. Counterfactual Comparison:")
    if alternatives:
        comparison = counterfactual.compare(
            actual_decision, alternatives, driver_location
        )
        print(f"   Compared {len(comparison.get('alternatives', []))} options")
        if comparison.get('best_option'):
            best = comparison['best_option']
            print(f"   Best Option: {best.get('option', 'N/A')}")
            print(f"   Wait Time: {best.get('expected_wait_time', 0)} min")
    
    # Step 5: Generate insights
    print("\n5. Insights Generation:")
    insights = insight_generator.generate(
        qa_result, actual_decision,
        comparison.get('alternatives', []) if alternatives else [],
        call_id
    )
    print(f"   Issue Summary: {insights.get('issue_summary', 'N/A')}")
    print(f"   Recommendation: {insights.get('recommendation', 'N/A')}")
    print(f"   Impact: {insights.get('impact_summary', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ Pipeline test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline()
