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
        You are an expert QA analyst for Battery Smart.
        Your job is to Audit this call against the Strict SOPs provided below.
        
        **GROUND TRUTH SOP & PRICING (AUTHORITATIVE):**
        {sop_context}
        
        **CALL TRANSCRIPT:**
        "{transcript}"
        
        **RULE-BASED FLAG (Hint):** {json.dumps(rules_detected)}
        
        **YOUR TASK:**
        Score the agent's performance (0-100) based on these weighted sections:
        
        1. **Greeting (10%)**: Did they say "Namaste/Hello" and offer language choice if needed?
        2. **Authentication (30%) [CRITICAL]**: 
           - Did the Agent explicitly ASK for the Driver ID? (e.g. "Apna ID batayein")
           - Did the Agent call the `verify_driver_by_id` tool?
           - **AUTOMATIC FAIL (0/30)** if the agent provided 'swap history', 'balance', or 'profile' WITHOUT first asking for ID or calling the verify tool. Even if the tool provided the data, the AGENT failed the protocol.
        3. **Solution Correctness (40%)**: 
           - Was the pricing/penalty/rule explained ACCURATELY per the Ground Truth?
           - Did they check for 'availability' before routing?
        4. **Closing (20%)**: Polite closing?
        
        **OUTPUT JSON:**
        {{
            "issue_detected": true/false (Set true if ANY critical fail),
            "decision_type": "station_routing" | "escalation_timing" | "response_structure" | "information_providing",
            "reason": "Root cause of the failure or main observation.",
            "confidence": 0.0-1.0,
            "scorecard": {{
                "greeting_score": 0-10,
                "authentication_score": 0-30,
                "solution_score": 0-40,
                "closing_score": 0-20,
                "total_score": 0-100,
                "adherence_score": 0-100, # Legacy field (same as total_score)
                "correctness_score": 0-100, # Normalized solution score (0-100 scale)
                "sentiment_label": "Positive" | "Neutral" | "Negative"
            }},
            "coaching_theme": "The #1 thing to fix next time.",
            "supervisor_flag": true/false (Flag if total_score < 70 or critical compliance breach)
        }}
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
