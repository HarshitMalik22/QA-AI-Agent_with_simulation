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
            
    def analyze_call_qa(self, transcript: str, rules_detected: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to analyze the call for qualitative issues that rules might miss.
        Merges rule-based findings with LLM reasoning.
        """
        if not self.client:
            return rules_detected

        prompt = f"""
        You are an expert QA analyst for a battery swapping network. 
        Analyze this customer support call transcript.
        
        Transcript:
        "{transcript}"
        
        Rule-based system flagged this issue: {json.dumps(rules_detected)}
        
        Your task:
        1. Verify if the rule-based flag is accurate.
        2. Identify if there's a deeper issue (tone, empathy, missed opportunities).
        3. Explain WHY the decision was suboptimal in 1 sentence.
        
        Return JSON format:
        {{
            "issue_detected": true/false,
            "decision_type": "station_routing" | "escalation_timing" | "response_structure",
            "reason": "Clear explanation of the mistake",
            "confidence": 0.0-1.0
        }}
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return json.loads(chat_completion.choices[0].message.content)
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
        You are a friendly, encouraging AI Performance Coach for support agents.
        
        Context:
        - The agent made this decision: {actual_decision.get('details', {})}
        - A better alternative was: {best_alternative.get('option')}
        - Impact of change: {json.dumps(best_alternative.get('improvement', {}))}
        
        Write a SHORT, friendly coaching message (max 2 sentences) to the agent.
        Start with "Hey!" or "Tip:".
        Focus on the positive impact of the alternative (e.g., "Checking availability first would have saved the driver 5 mins!").
        Do not sound robotic. Be a helpful colleague.
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
