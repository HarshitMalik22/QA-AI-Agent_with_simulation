"""
Decision Extractor Module

Extracts the actual agent decision from the call transcript.
"""

from typing import Dict, Any, Optional, List
import re

class DecisionExtractor:
    """
    Extracts actual agent decisions from transcripts.
    Supports: Station Routing, Escalation Timing, Response Structure
    """
    
    def __init__(self):
        self.station_patterns = [
            r"station\s+([A-Z]|\d+)",
            r"route.*?station\s+([A-Z]|\d+)",
            r"send.*?station\s+([A-Z]|\d+)",
            r"go to\s+station\s+([A-Z]|\d+)",
            r"station\s+([A-Z]|\d+).*?near",
            # Specific Delhi Locations
            r"(tilak\s*nagar)",
            r"(rajouri\s*garden)",
            r"(paschim\s*vihar)",
            r"(janak\s*puri)",
            r"(okhla)",
            r"(mayapuri)"
        ]
        
        self.escalation_patterns = [
            r"escalat",
            r"supervisor",
            r"manager",
            r"transfer"
        ]
    
    def extract(self, transcript: str, qa_result: Dict[str, Any], 
                driver_location: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Extract the actual decision made by the agent.
        
        Returns:
            {
                "decision_type": str,
                "details": Dict,
                "station_id": str | None,
                "escalation_action": str | None,
                "response_style": str | None
            }
        """
        decision_type = qa_result.get("decision_type", "station_routing")
        
        if decision_type == "station_routing":
            return self._extract_routing_decision(transcript, driver_location)
        elif decision_type == "escalation_timing":
            return self._extract_escalation_decision(transcript)
        elif decision_type == "technical_safety":
            return self._extract_technical_decision(transcript)
        elif decision_type == "response_structure":
            return self._extract_response_decision(transcript)
        else:
            # Check for safety keywords if type is unknown
            if any(k in transcript.lower() for k in ["smoke", "fire", "burn", "warm", "stuck", "lock"]):
                 return self._extract_technical_decision(transcript)
            
            # Default to routing if unclear
            return self._extract_routing_decision(transcript, driver_location)
    
    def _extract_routing_decision(self, transcript: str, 
                                  driver_location: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Extract station routing decision"""
        transcript_lower = transcript.lower()
        
        # Try to find station ID or Name
        station_id = None
        station_name = None
        
        for pattern in self.station_patterns:
            match = re.search(pattern, transcript_lower, re.IGNORECASE)
            if match:
                val = match.group(1).upper()
                # Check if it's a known named location
                if "TILAK" in val: station_id = "A" # Mock map to Stn A
                elif "RAJOURI" in val: station_id = "B" # Mock map to Stn B
                elif "OKHLA" in val: station_id = "C"
                elif "MAYAPURI" in val: station_id = "D"
                else: 
                    station_id = val # A, B, C, etc.
                
                station_name = val.title()
                break
        
        # If no station found, look for generic station mentions
        if not station_id:
            # Look for station names or numbers
            station_match = re.search(r"(station|stn)\s*([A-Z0-9]+)", transcript_lower, re.IGNORECASE)
            if station_match:
                station_id = station_match.group(2).upper()
            else:
                # Default to first station if unclear (for demo purposes)
                station_id = "A"
        
        return {
            "decision_type": "station_routing",
            "station_id": station_id,
            "details": {
                "action": "route_to_station",
                "station": station_id,
                "station_name": station_name, # Pass specific name
                "driver_location": driver_location
            },
            "escalation_action": None,
            "response_style": None
        }
    
    def _extract_escalation_decision(self, transcript: str) -> Dict[str, Any]:
        """Extract escalation timing decision"""
        transcript_lower = transcript.lower()
        
        escalation_action = "none"
        if any(pattern in transcript_lower for pattern in self.escalation_patterns):
            if any(delay in transcript_lower for delay in ["later", "wait", "try first"]):
                escalation_action = "delayed"
            else:
                escalation_action = "immediate"
        
        return {
            "decision_type": "escalation_timing",
            "station_id": None,
            "details": {
                "action": "escalation",
                "timing": escalation_action
            },
            "escalation_action": escalation_action,
            "response_style": None
        }
    
    
    def _extract_response_decision(self, transcript: str) -> Dict[str, Any]:
        """Extract response structure decision"""
        transcript_lower = transcript.lower()
        
        response_style = "direct"
        if any(vague in transcript_lower for vague in ["maybe", "I think", "probably", "not sure"]):
            response_style = "vague"
        elif "preference" in transcript_lower or "would you like" in transcript_lower:
            response_style = "clarifying"
        else:
            response_style = "direct"
        
        return {
            "decision_type": "response_structure",
            "station_id": None,
            "details": {
                "action": "response",
                "style": response_style
            },
            "escalation_action": None,
            "response_style": response_style
        }

    def _extract_technical_decision(self, transcript: str) -> Dict[str, Any]:
        """Extract technical safety decision"""
        transcript_lower = transcript.lower()
        
        issue_type = "general_fault"
        if any(k in transcript_lower for k in ["smoke", "fire", "burn", "heat"]):
            issue_type = "critical_temp"
        elif any(k in transcript_lower for k in ["stuck", "lock", "jam"]):
            issue_type = "lock_failure"
            
        action = "monitor"
        if "technician" in transcript_lower:
            action = "dispatch_technician"
        elif "stop" in transcript_lower or "ruk" in transcript_lower: # Hindi 'ruk'
            action = "stop_immediately"
            
        return {
            "decision_type": "technical_safety",
            "station_id": None, 
            "details": {
                "action": action,
                "issue": issue_type
            },
            "technical_issue": issue_type,
            "safety_action": action
        }
