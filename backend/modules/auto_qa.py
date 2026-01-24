"""
Auto-QA Analyzer Module

Detects suboptimal agent decisions using rule-based + LLM-assisted logic.
Detects: SOP deviation, risky routing, late escalation, incomplete explanation.
"""

from typing import Dict, Any, Optional
import re
from data.mock_data import MOCK_STATIONS

class AutoQAAnalyzer:
    """
    Rule + LLM-assisted QA analyzer.
    Uses deterministic rules first, then LLM for nuanced reasoning.
    """
    
    def __init__(self):
        # Rule-based patterns for quick detection
        self.risk_keywords = {
            "station_routing": [
                "busy", "crowded", "long queue", "wait time", "congestion",
                "high load", "near capacity"
            ],
            "escalation_timing": [
                "escalate", "supervisor", "manager", "later", "wait",
                "try first", "see if"
            ],
            "response_structure": [
                "just go", "try", "maybe", "I think", "probably",
                "not sure", "guess"
            ]
        }
        
        self.sop_violations = [
            "didn't check availability",
            "didn't verify location",
            "didn't confirm preference",
            "assumed without asking"
        ]
        
        # Load station data for rule checks
        self.station_map = {s["id"]: s for s in MOCK_STATIONS}

    def evaluate_decision(self, decision_contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a structured decision contract.
        """
        agent_decision = decision_contract.get("agent_decision", {})
        decision_type = agent_decision.get("decision_type")
        
        if decision_type == "station_routing":
            station_id = agent_decision.get("recommended_station")
            station = self.station_map.get(station_id)
            
            if station:
                load_ratio = station["current_load"] / station["capacity"]
                
                # Rule: Do not route to congested stations (>80% load) without acknowledging tradeoff
                if load_ratio >= 0.8:
                    if not agent_decision.get("tradeoff_acknowledged"):
                        return {
                            "issue_detected": True,
                            "decision_type": "station_routing",
                            "reason": f"Agent routed to Station {station_id} which is critically congested ({int(load_ratio*100)}% load)",
                            "confidence": 1.0
                        }
        
        return {
            "issue_detected": False,
            "decision_type": None,
            "reason": "Decision appears optimal",
            "confidence": 0.0
        }

    
    def analyze(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze transcript for suboptimal decisions.
        
        Returns:
            {
                "issue_detected": bool,
                "decision_type": str | None,
                "reason": str,
                "confidence": float
            }
        """
        transcript_lower = transcript.lower()
        
        # Rule 1: Check for risky routing mentions
        routing_risk = self._detect_routing_risk(transcript_lower)
        if routing_risk:
            return {
                "issue_detected": True,
                "decision_type": "station_routing",
                "reason": routing_risk["reason"],
                "confidence": routing_risk["confidence"]
            }
        
        # Rule 2: Check for late escalation
        escalation_risk = self._detect_escalation_risk(transcript_lower)
        if escalation_risk:
            return {
                "issue_detected": True,
                "decision_type": "escalation_timing",
                "reason": escalation_risk["reason"],
                "confidence": escalation_risk["confidence"]
            }
        
        # Rule 3: Check for incomplete explanation
        explanation_risk = self._detect_explanation_risk(transcript_lower)
        if explanation_risk:
            return {
                "issue_detected": True,
                "decision_type": "response_structure",
                "reason": explanation_risk["reason"],
                "confidence": explanation_risk["confidence"]
            }
        
        # Rule 4: Check for SOP violations
        sop_risk = self._detect_sop_violation(transcript_lower)
        if sop_risk:
            return {
                "issue_detected": True,
                "decision_type": sop_risk.get("decision_type", "station_routing"),
                "reason": sop_risk["reason"],
                "confidence": sop_risk["confidence"]
            }
        
        # No issue detected
        return {
            "issue_detected": False,
            "decision_type": None,
            "reason": "No suboptimal decisions detected",
            "confidence": 0.0
        }
    
    def _detect_routing_risk(self, transcript: str) -> Optional[Dict[str, Any]]:
        """Detect risky station routing decisions"""
        routing_keywords = self.risk_keywords["station_routing"]
        matches = sum(1 for keyword in routing_keywords if keyword in transcript)
        
        # Check for mentions of busy/crowded stations
        if any(keyword in transcript for keyword in ["busy", "crowded", "long queue"]):
            return {
                "reason": "Agent routed driver to station with high load or mentioned congestion",
                "confidence": 0.85
            }
        
        # Check for routing without checking availability
        if "route" in transcript or "send" in transcript or "go to" in transcript:
            if "check" not in transcript and "availability" not in transcript:
                return {
                    "reason": "Agent routed driver without checking station availability",
                    "confidence": 0.75
                }
        
        return None
    
    def _detect_escalation_risk(self, transcript: str) -> Optional[Dict[str, Any]]:
        """Detect late escalation decisions"""
        if "escalate" in transcript or "supervisor" in transcript:
            # Check if escalation was delayed
            if any(delay_word in transcript for delay_word in ["later", "wait", "try first", "see if"]):
                return {
                    "reason": "Agent delayed escalation when immediate escalation may have been appropriate",
                    "confidence": 0.80
                }
        
        return None
    
    def _detect_explanation_risk(self, transcript: str) -> Optional[Dict[str, Any]]:
        """Detect incomplete or vague explanations"""
        vague_phrases = ["just go", "try", "maybe", "I think", "probably", "not sure", "guess"]
        
        if any(phrase in transcript for phrase in vague_phrases):
            return {
                "reason": "Agent provided vague or incomplete instructions without clarifying driver preference",
                "confidence": 0.70
            }
        
        return None
    
    def _detect_sop_violation(self, transcript: str) -> Optional[Dict[str, Any]]:
        """Detect SOP violations"""
        # Check if agent verified location
        if ("route" in transcript or "send" in transcript) and "location" not in transcript:
            return {
                "decision_type": "station_routing",
                "reason": "Agent routed without verifying driver location",
                "confidence": 0.65
            }
        
        return None
