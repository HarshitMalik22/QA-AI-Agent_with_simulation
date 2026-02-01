import os
from groq import Groq
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("⚠️ GROQ_API_KEY not found. LLM features will be disabled.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
            
    def analyze_call_qa(self, transcript: str, rules_detected: Dict[str, Any], sop_context: str = "") -> Dict[str, Any]:
        """
        Use LLM to analyze the call with strict reference to SOPs.
        Returns a weighted scorecard.
        """
        if not self.client:
            return rules_detected

        prompt = f"""
        You are a STRICT, METICULOUS QA Auditor for Battery Smart. Your job is to DEEPLY SCRUTINIZE every line of this call transcript and catch ALL violations.

        **GROUND TRUTH SOP & PRICING (AUTHORITATIVE):**
        {sop_context}
        
        **CALL TRANSCRIPT TO AUDIT:**
        "{transcript}"
        
        **RULE-BASED FLAG (Hint):** {json.dumps(rules_detected)}
        
        ===== CRITICAL AUDIT INSTRUCTIONS =====
        
        **STEP 1: READ THE ENTIRE TRANSCRIPT LINE BY LINE**
        - Identify EVERY statement made by the Agent.
        - For each Agent statement, ask: "Is this correct? Is this on-topic? Did they follow SOP?"
        
        **STEP 2: CHECK FOR THESE SPECIFIC VIOLATIONS**
        
        🔴 **OFF-TOPIC VIOLATION (INSTANT -50 PENALTY)**
        - Did the agent answer ANY question unrelated to Battery Smart?
        - Examples: Math tables, jokes, songs, general knowledge, coding, weather, stories, recipes, games.
        - If Agent said ANYTHING like "2 ka table", "ek joke sunao", answered homework/math questions → AUTOMATIC -50 penalty.
        - CORRECT BEHAVIOR: Agent should say "Main sirf Battery Smart services mein help kar sakta hoon."
        
        🔴 **AUTHENTICATION BYPASS (0/30 on Authentication)**
        - Did Agent give account info (balance, swaps, profile) BEFORE asking for Driver ID?
        - Did Agent verify ID through the tool before sharing sensitive data?
        
        🔴 **WRONG INFORMATION GIVEN (0/40 on Solution)**
        - Did Agent give incorrect pricing, penalty amounts, or policies?
        - Cross-check EVERY number against the Ground Truth SOP above.
        
        **STEP 3: KEY STEPS CHECKLIST (Check each one)**
        For each step, mark true ONLY if explicitly done:
        1. greeting_offered: Did agent say Namaste/Hello?
        2. language_choice_given: Did agent offer language options?
        3. id_requested: Did agent explicitly ASK for Driver ID?
        4. id_verified_via_tool: Was verify_driver_by_id called? (Look for verification confirmation)
        5. correct_info_provided: Was all info given factually correct per SOP?
        6. closing_script_used: Did agent use the mandatory closing script OR a polite closing?
        
        **STEP 4: SENTIMENT TRAJECTORY ANALYSIS**
        - Track customer sentiment at START vs END of call.
        - Identify frustration signals: raised voice indicators (caps, exclamations), repeated questions, explicit complaints.
        - Determine escalation_risk: 
          - "Low" = Customer satisfied, no frustration
          - "Medium" = Some frustration but resolved
          - "High" = Customer angry/frustrated at end, or issue unresolved
        
        **STEP 5: SCORE EACH SECTION WITH EVIDENCE**
        
        1. **Greeting (0-10)**: Quote the greeting. Was it professional?
        2. **Authentication (0-30)**: 
           - Quote where Agent asked for ID (or didn't).
           - If info given before ID verification → 0/30.
        3. **Solution Correctness (0-40)**:
           - Quote the solution/answer given.
           - Were wrong prices, wrong rules, or wrong info provided? → Deduct heavily.
        4. **Closing (0-20)**: Was there a polite closing?
        5. **Guardrails Penalty (-50)**: 
           - Quote ANY off-topic response by Agent.
           - If found → Apply -50 penalty to total.
        
        **STEP 6: CALCULATE FINAL SCORE**
        - Start with sum of sections 1-4 (max 100).
        - Apply -50 penalty if guardrails violated.
        - Minimum score is 0 (no negatives).
        
        ===== OUTPUT JSON FORMAT =====
        {{
            "transcript_analysis": {{
                "off_topic_violations": ["Quote exact off-topic responses here, or empty array if none"],
                "auth_violations": ["Quote where auth was skipped, or empty if followed"],
                "incorrect_info": ["Quote any wrong information given, or empty if all correct"]
            }},
            "key_steps_checklist": {{
                "greeting_offered": true/false,
                "language_choice_given": true/false,
                "id_requested": true/false,
                "id_verified_via_tool": true/false,
                "correct_info_provided": true/false,
                "closing_script_used": true/false
            }},
            "sentiment_trajectory": {{
                "start_sentiment": "Neutral" | "Positive" | "Negative",
                "end_sentiment": "Neutral" | "Positive" | "Negative",
                "escalation_risk": "Low" | "Medium" | "High",
                "frustration_indicators": ["Quote any frustration signals from customer, or empty array"]
            }},
            "call_summary": "2-3 sentence summary of what happened in the call, citing specific issues.",
            "improvement_explanation": "Specific, actionable feedback with exact quotes of what went wrong.",
            "issue_detected": true/false,
            "decision_type": "station_routing" | "escalation_timing" | "response_structure" | "information_providing" | "off_topic_violation",
            "reason": "Root cause with evidence from transcript.",
            "confidence": 0.0-1.0,
            "scorecard": {{
                "greeting_score": 0-10,
                "authentication_score": 0-30,
                "solution_score": 0-40,
                "closing_score": 0-20,
                "guardrails_penalty": 0 or -50,
                "total_score": (sum of above, min 0),
                "adherence_score": <same as total_score>,
                "correctness_score": <solution_score normalized to 0-100>,
                "sentiment_label": "Positive" | "Neutral" | "Negative"
            }},
            "coaching_insights": {{
                "primary_theme": "The #1 thing this agent needs to improve",
                "specific_example": "Exact quote from transcript showing the issue",
                "suggested_fix": "Concrete action to take next time"
            }},
            "supervisor_flag": true/false,
            "supervisor_flag_reasons": ["List reasons: low score, auth bypass, off-topic, high escalation risk, wrong info, etc."]
        }}
        
        **SUPERVISOR FLAG TRIGGERS (flag if ANY of these):**
        - total_score < 70
        - authentication_score = 0
        - off_topic_violation detected
        - escalation_risk = "High"
        - Customer expressed anger/frustration without proper handling
        - Wrong pricing/penalty info provided
        
        **REMEMBER: Be HARSH. Catch EVERY mistake. Do NOT give 100/100 unless the call is PERFECT.**
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a specific, strict QA auditor. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.0, # Zero temp for strict evaluation
                response_format={"type": "json_object"}
            )
            result = json.loads(chat_completion.choices[0].message.content)
            
            # SAFEGUARD: Ensure scorecard exists. If not, use rule-based default or perfect score.
            if "scorecard" not in result:
                is_issue = result.get("issue_detected") or rules_detected.get("issue_detected")
                
                if is_issue:
                     default_score = {
                        "total_score": 40,
                        "greeting_score": 5,
                        "authentication_score": 0, # Assume auth fail if critical issue matched
                        "solution_score": 15,
                        "closing_score": 10,
                        "sentiment_label": "Negative",
                        "adherence_score": 40,
                        "correctness_score": 40
                    }
                else:
                    default_score = {
                        "total_score": 100,
                        "greeting_score": 10,
                        "authentication_score": 30,
                        "solution_score": 40,
                        "closing_score": 20,
                        "sentiment_label": "Positive",
                        "adherence_score": 100,
                        "correctness_score": 100
                    }
                    
                result["scorecard"] = rules_detected.get("scorecard", default_score)
            
            return result
        except Exception as e:
            print(f"LLM Error: {e}")
            return rules_detected

    def generate_coaching(self, transcript: str, actual_decision: Dict, best_alternative: Dict) -> str:
        """
        Generate a friendly, constructive coaching message from the AI 'Coach'.
        """
        if not self.client:
            return "Analysis complete. Review the alternatives table for optimization opportunities."

        prompt = f"""
        You are a friendly but data-driven AI Performance Coach.
        
        TRANSCRIPT Excerpt:
        "{transcript[:500]}..."
        
        DECISION CONTEXT:
        - Agent Action: {actual_decision.get('details', {})}
        - Better Option: {best_alternative.get('option')}
        - Quantitative Impact: {json.dumps(best_alternative.get('improvement', {}))}
        
        TASK:
        Write a 1-sentence specific coaching tip.
        
        GUIDELINES:
        1. **Be Specific**: Quote the exact location or issue mentioned in the transcript if possible (e.g. "Since the driver is at Paschim Vihar...").
        2. **Be Encouraging**: "Hey! checking availability first would have saved 5 mins."
        3. **No Robot Speak**: Do not say "Based on the analysis". Speak like a lead engineer.
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful, friendly coach."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return "Tip: Choosing a station with lower load can significantly reduce wait times for our drivers."

    def analyze_image(self, image_url: str, prompt: str = "Analyze this image relevant to battery swapping context.") -> str:
        """
        Use Llama 3.2 Vision model to analyze images (e.g., error codes, damaged batteries).
        """
        if not self.client:
            return "Vision features unavailable (API Key missing)."

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                model="llama-3.2-11b-vision-preview",
                temperature=0.5,
                max_tokens=150
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Vision API Error: {e}")
            return "Sorry, I couldn't process the image due to a technical issue."
