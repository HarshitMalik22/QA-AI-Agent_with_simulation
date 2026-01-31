from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import os
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
import os
import logging

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("vapi_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
from modules.llm_service import LLMService
from modules.decision_emitter import DecisionEmitter
from modules.excel_logger import log_interaction, LOG_FILE_PATH
from modules.telegram_handler import TelegramHandler
from data.mock_data import MOCK_STATIONS, MOCK_TRANSCRIPTS
from modules.simulation import driver_sim
from modules.assistant_tools import (
    TOOLS_SCHEMA,
    get_driver_profile,
    get_swap_history,
    get_nearest_station,
    get_nearest_dsk,
    get_plan_details
)

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
telegram_handler = TelegramHandler()

class TranscriptRequest(BaseModel):
    transcript: str
    call_id: str
    driver_location: Optional[Dict[str, float]] = None

class AnalysisResponse(BaseModel):
    call_id: str
    transcript: str
    qa_result: Dict[str, Any]
    actual_decision: Dict[str, Any]
    alternatives: List[Dict[str, Any]]
    insights: Dict[str, Any]

@app.get("/")
def root():
    return {"message": "QA-Driven Digital Twin API"}

@app.post("/")
async def root_post(request: Request):
    """
    Handle Vapi requests sent to root URL.
    Delegates to vapi_assistant_request.
    """
    return await vapi_assistant_request(request)

@app.get("/api/stations")
def get_stations():
    """Get all available stations"""
    return {"stations": MOCK_STATIONS}

@app.get("/api/transcripts")
def get_sample_transcripts():
    """Get sample call transcripts for testing"""
    return {"transcripts": MOCK_TRANSCRIPTS}

@app.get("/api/simulation/live")
def get_live_simulation_state():
    """Returns the current location of the simulated driver."""
    return driver_sim.get_location()

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
    return perform_analysis(request)

def perform_analysis(request: TranscriptRequest) -> AnalysisResponse:
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
    
    analysis_res = AnalysisResponse(
        call_id=request.call_id,
        transcript=request.transcript,
        qa_result=qa_result,
        actual_decision=actual_decision,
        alternatives=comparison.get("alternatives", []),
        insights=insights
    )
    
    # Log to Excel
    try:
        log_interaction(analysis_res)
    except Exception as e:
        print(f"Logging failed: {e}")
        
    return analysis_res

@app.get("/api/logs/download")
def download_logs():
    """
    Download the interaction logs Excel file.
    """
    if os.path.exists(LOG_FILE_PATH):
        return FileResponse(
            path=LOG_FILE_PATH,
            filename="interaction_logs.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    return {"error": "Log file not found"}

# --- Vapi Integration ---

LATEST_ANALYSIS = None

VAPI_ASSISTANT_CONFIG = {
    "name": "Raju Rastogi",
    "firstMessage": "Namaste Sir! Main Raju Rastogi bol raha hoon. Kahiye, main aapki kya madad kar sakta hoon?",
    "transcriber": {
        "provider": "deepgram",
        "model": "nova-2",
        "language": "hi"
    },
    "model": {
        "provider": "openai",
        "model": "gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": """You are **Raju Rastogi**, a helpful Support Agent for 'Battery Smart', India's largest battery swapping network for e-rickshaws.

                **Core Persona**:
                - You are a generic Indian driver support agent.
                - **CRITICAL**: You must speak in **PURE HINDI (Devanagari Script)**.
                - **ABSOLUTE RULE**: Do NOT use English/Roman script for Hindi words. (e.g., write "नमस्ते", NOT "Namaste").
                - Only use English for specific technical nouns: 'Battery', 'Station', 'Swapping', 'Login', 'OTP'.
                - Example: "नमस्ते सर! मैं राजू रस्तोगी बोल रहा हूँ। बताइए मैं आपकी क्या मदद कर सकता हूँ?"

                **Data Context (Live)**:
                - **Tilak Nagar (Stn A)**: OVERLOADED (Waittime: 20 mins).
                - **Rajouri Garden (Stn B)**: FREE (Waittime: 2 mins). Distance: 3km from Tilak Nagar.

                **Protocol**:
                1. **Greeting**: "नमस्ते सर! मैं राजू बोल रहा हूँ। कहिए, क्या सेवा करूँ?"
                2. **Location First**: If the driver reports an issue, ALWAYS ask: "सर, अभी आप कहाँ पर हैं?" (Where are you right now?).
                
                **Scenarios**:
                - **High Traffic**: If they are at Tilak Nagar: "सर, वहाँ बहुत भीड़ है (20 मिनट वेटिंग)। आप राजौरी गार्डन (Rajouri Garden) चले जाइए? वो पास है और खाली है।"
                - **Battery Issue**: "ज़ोर मत लगाइए सर, लॉक टूट जाएगा। मैं टेक्निशियन (Technician) को भेज रहा हूँ।"
                - **General Help**: Keep it polite and helpful. "जी सर, मैं चेक करता हूँ।"

                **Tone**: Respectful, patient, and clear. Native Hindi speaker. Use short sentences."""
            }
        ]
    },
    "voice": {
        "provider": "11labs",
        "voiceId": "IMzcdjL6UK1gZxag6QAU"
    }
}

@app.post("/api/vapi/assistant")
async def vapi_assistant_request(request: Request):
    """
    Returns the assistant configuration for Vapi to use when a call comes in.
    DYNAMICALLY updates based on incoming call payload.
    """
    data = await request.json()
    call = data.get("message", {}).get("call", {})
    customer_number = call.get("customer", {}).get("number", "+11234567890") # Default to test number
    
    print(f"Incoming Call from: {customer_number}")
    
    # Determined Callback URL
    # PRIORITIZE Environment Variable for local dev (ngrok)
    env_server_url = os.getenv("VAPI_SERVER_URL")
    if env_server_url:
        server_url = env_server_url
        logger.info(f"Using VAPI_SERVER_URL from env: {server_url}")
    else:
        # Fallback to dynamic determination
        scheme = request.headers.get("x-forwarded-proto", "https")
        host = request.headers.get("host")
        server_url = f"{scheme}://{host}/api/vapi/webhook"
        logger.info(f"Dynamically determined server_url: {server_url}")
    
    print(f"Setting Server URL to: {server_url}")

    # Deep copy config to avoid global state pollution
    config = json.loads(json.dumps(VAPI_ASSISTANT_CONFIG))
    
    # 1. Update System Prompt with Context
    system_msg = config["model"]["messages"][0]["content"]
    context_injection = f"""
    
    **CURRENT CALL CONTEXT**:
    - **Customer Phone**: {customer_number}
    - **Tools**: You have access to tools to fetch driver profile, swap history, nearby stations, and plans.
    - **Rule**: ALWAYS verify the correct driver details using 'get_driver_profile' if account specific info is needed.
    """
    config["model"]["messages"][0]["content"] = system_msg + context_injection
    
    # 2. Add Tools
    config["model"]["tools"] = TOOLS_SCHEMA
    
    # 3. Set Server URL for Tool Calls
    config["serverUrl"] = server_url
    
    # Wrap in "assistant" key as per Vapi requirements or return directly if needed.
    # Based on "system id" error, Vapi likely expects a wrapped response or strict structure.
    # Trying wrapped format first.
    response_payload = {"assistant": config}
    
    logger.info(f"Sending Vapi Response: {json.dumps(response_payload)}")
    return response_payload

from fastapi import Request

@app.post("/api/vapi/webhook")
async def vapi_webhook(request: Request):
    """
    Receives call events from Vapi.
    Triggers analysis on 'end-of-call-report'.
    """
    global LATEST_ANALYSIS
    data = await request.json()
    
    # Log incoming webhook type for debugging
    msg_type = data.get("message", {}).get("type")
    print(f"\n{'='*50}")
    print(f"Vapi Webhook Received: {msg_type}")
    print(f"Full payload: {json.dumps(data, indent=2)[:1000]}")
    print(f"{'='*50}")

    if msg_type == "end-of-call-report":
        transcript = data.get("message", {}).get("transcript", "")
        call_id = data.get("message", {}).get("call", {}).get("id", "mobile-call")
        
        if transcript:
            print(f"Analyzing Vapi Call: {transcript[:50]}...")
            
            # Create request object
            req = TranscriptRequest(
                transcript=transcript,
                call_id=call_id,
                driver_location=None 
            )
            
            # Run analysis
            try:
                analysis_result = perform_analysis(req)
                LATEST_ANALYSIS = analysis_result
                print("Analysis completed and stored.")
            except Exception as e:
                print(f"Error during Vapi analysis: {e}")
            
    elif msg_type == "tool-calls":
        print("Handling Tool Calls...")
        tool_calls = data.get("message", {}).get("toolCalls", [])
        results = []
        
        for tc in tool_calls:
            func_name = tc.get("function", {}).get("name")
            args = tc.get("function", {}).get("arguments", {})
            if isinstance(args, str):
                args = json.loads(args)
            
            call_id = tc["id"]
            print(f"Executing Tool: {func_name} with args: {args}")
            
            result = {"error": "Function not found"}
            
            try:
                if func_name == "get_driver_profile":
                    result = get_driver_profile(args.get("phone_number"))
                elif func_name == "get_swap_history":
                    result = get_swap_history(args.get("phone_number"))
                elif func_name == "get_nearest_station":
                    result = get_nearest_station(
                        lat=args.get("lat"), 
                        lon=args.get("lon"),
                        location_name=args.get("location_name")
                    )
                elif func_name == "get_nearest_dsk":
                    result = get_nearest_dsk(
                        lat=args.get("lat"), 
                        lon=args.get("lon"),
                        location_name=args.get("location_name")
                    )
                elif func_name == "update_driver_location":
                     # Magic tool to move the driver
                     loc_name = args.get("location_name")
                     result = driver_sim.set_location_by_name(loc_name)
                elif func_name == "get_plan_details":
                    result = get_plan_details(args.get("plan_name"))
            except Exception as e:
                print(f"Error executing {func_name}: {e}")
                result = {"error": str(e)}
            
            results.append({
                "toolCallId": call_id,
                "result": json.dumps(result)  # Result must be a string
            })
            
        return {"results": results}

    return {"status": "ok"}

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Receives updates from Telegram.
    """
    try:
        data = await request.json()
        print(f"Telegram Update: {json.dumps(data)[:100]}...")
        result = await telegram_handler.process_update(data)
        return result
    except Exception as e:
        print(f"Telegram Webhook Error: {e}")
        return {"error": str(e)}

@app.get("/api/analysis/latest")
def get_latest_analysis():
    return LATEST_ANALYSIS

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
