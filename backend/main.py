from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from dotenv import load_dotenv

load_dotenv()

from modules.auto_qa import AutoQAAnalyzer
from modules.decision_extractor import DecisionExtractor
from modules.digital_twin import DigitalTwinSimulator
from modules.counterfactual import CounterfactualComparator
from modules.insight_generator import InsightGenerator
from modules.llm_service import LLMService
from modules.decision_emitter import DecisionEmitter
from data.mock_data import MOCK_STATIONS, MOCK_TRANSCRIPTS

app = FastAPI(title="QA-Driven Digital Twin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
llm_service = LLMService()
auto_qa = AutoQAAnalyzer()
decision_extractor = DecisionExtractor()
digital_twin = DigitalTwinSimulator(MOCK_STATIONS)
counterfactual = CounterfactualComparator(digital_twin)
insight_generator = InsightGenerator(llm_service)
decision_emitter = DecisionEmitter()

class TranscriptRequest(BaseModel):
    transcript: str
    call_id: str
    driver_location: Optional[Dict[str, float]] = None

class AnalysisResponse(BaseModel):
    call_id: str
    qa_result: Dict[str, Any]
    actual_decision: Dict[str, Any]
    alternatives: List[Dict[str, Any]]
    insights: Dict[str, Any]

@app.get("/")
def root():
    return {"message": "QA-Driven Digital Twin API"}

@app.get("/api/stations")
def get_stations():
    """Get all available stations"""
    return {"stations": MOCK_STATIONS}

@app.get("/api/transcripts")
def get_sample_transcripts():
    """Get sample call transcripts for testing"""
    return {"transcripts": MOCK_TRANSCRIPTS}

@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_call(request: TranscriptRequest):
    """
    Main analysis endpoint:
    1. Auto-QA detects issues (Hybrid Rule + LLM)
    2. Extract actual decision
    3. Simulate alternatives
    4. Compare counterfactuals
    5. Generate insights + Coaching
    """
    # Step 1: Auto-QA Analysis (Hybrid)
    qa_result_rules = auto_qa.analyze(request.transcript)
    if llm_service.client:
        # Refine with LLM if available
        qa_result = llm_service.analyze_call_qa(request.transcript, qa_result_rules)
    else:
        qa_result = qa_result_rules
    
    # Step 2: Extract actual decision
    actual_decision = decision_extractor.extract(
        request.transcript,
        qa_result,
        request.driver_location
    )
    
    # Step 3: Generate alternatives
    alternatives = []
    if qa_result.get("issue_detected"):
        alternatives = counterfactual.generate_alternatives(
            actual_decision,
            request.transcript,
            request.driver_location
        )
    
    # Step 4: Simulate and compare
    if alternatives:
        comparison = counterfactual.compare(
            actual_decision,
            alternatives,
            request.driver_location
        )
    else:
        comparison = {"alternatives": []}
    
    # Step 5: Generate insights
    insights = insight_generator.generate(
        qa_result,
        actual_decision,
        comparison.get("alternatives", []),
        request.call_id,
        request.transcript  # Pass transcript for coaching context
    )
    
    return AnalysisResponse(
        call_id=request.call_id,
        qa_result=qa_result,
        actual_decision=actual_decision,
        alternatives=comparison.get("alternatives", []),
        insights=insights
    )

@app.post("/api/live-demo")
def live_demo_loop():
    """
    Executes the Closed-Loop Decision System Demo:
    1. Agent emits a decision (Source of Truth)
    2. Auto-QA evaluates the decision contract
    3. Digital Twin simulates the original decision
    4. Counterfactual Generator simulates alternatives
    5. Comparison & Insights
    """
    # 1. Decision Emitter (Source of Truth)
    decision_contract = decision_emitter.emit_decision()
    
    # 2. Auto-QA (Evaluate Decision Contract)
    qa_result = auto_qa.evaluate_decision(decision_contract)
    
    # Adapter: Convert contract to internal format for Simulation
    agent_decision = decision_contract["agent_decision"]
    driver_context = decision_contract["driver_context"]
    
    internal_decision = {
        "decision_type": agent_decision["decision_type"],
        # Map recommended_station to station_id for Digital Twin
        "station_id": agent_decision.get("recommended_station"), 
        "details": agent_decision
    }
    
    # 3. Simulate Alternatives (Counterfactuals)
    # Pass 'driver_context' as 'driver_location' since the keys match (lat/lon) or close enough
    # The MOCK loc is {"lat": ..., "lon": ...}
    # Emitter context has coordinates={"lat": ..., "lon": ...}
    
    location = driver_context.get("coordinates")
    
    # Generate alternatives
    # Note: simulate_alternatives requires 'transcript' usually, but here we pass dummy text
    # because we are driven by the structured contract.
    alternatives = counterfactual.generate_alternatives(
        internal_decision,
        transcript="SYSTEM_GENERATED_DECISION", 
        driver_location=location
    )
    
    # 4. Compare Original vs Alternatives
    comparison = counterfactual.compare(
        internal_decision,
        alternatives,
        driver_location=location
    )
    
    # 5. Generate Insights
    insights = insight_generator.generate(
        qa_result,
        internal_decision,
        comparison.get("alternatives", []),
        decision_contract["decision_id"],
        transcript="System generated decision based on live context."
    )
    
    return {
        "decision_contract": decision_contract,
        "qa_evaluation": qa_result,
        "simulation_comparison": comparison,
        "final_recommendation": insights,
        "status": "Closed-Loop Execution Successful"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
