import pandas as pd
import os
from datetime import datetime
import json

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "interaction_logs.xlsx")

def log_interaction(analysis_result):
    """
    Logs the analysis result to an Excel file.
    Appends to existing file or creates a new one.
    """
    try:
        # 1. Flatten the data
        # We want to capture: Time, Call ID, Transcript, Auto-QA Status, Decision Type, Wait Time, Sim Alternatives
        
        # Convert Pydantic model to dict if needed
        data = analysis_result.dict() if hasattr(analysis_result, "dict") else analysis_result
        
        qa_result = data.get("qa_result", {})
        actual_decision = data.get("actual_decision", {})
        alternatives = data.get("alternatives", [])
        insights = data.get("insights", {})

        # Find the alternative that corresponds to the actual decision (for comparison)
        actual_sim = next((alt for alt in alternatives if alt.get("is_actual")), {})
        # Find the best alternative (usually the one recommended or the counterfactual)
        counterfactual_sim = next((alt for alt in alternatives if not alt.get("is_actual")), {})

        row_data = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Call ID": data.get("call_id"),
            "Transcript": data.get("transcript"),
            
            # Auto-QA
            "Issue Detected": qa_result.get("issue_detected"),
            "Confidence Score": qa_result.get("confidence_score"),
            "QA Reason": qa_result.get("reason"),
            
            # Actual Decision
            "Actual Decision Type": actual_decision.get("decision_type"),
            "Actual Details": json.dumps(actual_decision), # Store full JSON for debug
            "Actual Wait Time (min)": actual_sim.get("expected_wait_time"),
            "Actual Risk Level": actual_sim.get("congestion_risk"),
            
            # Counterfactual / Optimization
            "Optimized Option": counterfactual_sim.get("option", "N/A"),
            "Optimized Wait Time (min)": counterfactual_sim.get("expected_wait_time"),
            "Optimized Risk Level": counterfactual_sim.get("congestion_risk"),
            "Wait Time Reduction (%)": counterfactual_sim.get("improvement", {}).get("wait_time_reduction_pct"),
            
            # Insights
            "Recommendation": insights.get("recommendation"),
            "Impact Summary": insights.get("impact_summary")
        }

        # 2. Create DataFrame
        df_new = pd.DataFrame([row_data])

        # 3. Append to Excel
        if os.path.exists(LOG_FILE_PATH):
            with pd.ExcelWriter(LOG_FILE_PATH, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                # Load existing sheet to find the next row? 
                # Pandas 'a' mode with overlay doesn't automatically append to bottom if we don't specify startrow
                # Easier approach: Read all, append, write all (okay for local hackathon scale)
                # Or use openpyxl directly for appending if file processes huge data. 
                # For now, read-append-write is safer and simpler for small datasets.
                df_existing = pd.read_excel(LOG_FILE_PATH)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                df_combined.to_excel(LOG_FILE_PATH, index=False)
        else:
            df_new.to_excel(LOG_FILE_PATH, index=False)
            
        print(f"Interaction logged to {LOG_FILE_PATH}")

    except Exception as e:
        print(f"Error logging to Excel: {e}")
