"""
Counterfactual Comparator Module

Generates alternative decisions and compares outcomes.
"""

from typing import Dict, Any, List, Optional
from modules.digital_twin import DigitalTwinSimulator

class CounterfactualComparator:
    """
    Generates and compares counterfactual decisions.
    """
    
    def __init__(self, digital_twin: DigitalTwinSimulator):
        self.digital_twin = digital_twin
    
    def generate_alternatives(self, actual_decision: Dict[str, Any], 
                            transcript: str,
                            driver_location: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """
        Generate 2-3 alternative decisions based on the actual decision.
        """
        decision_type = actual_decision.get("decision_type")
        
        if decision_type == "station_routing":
            return self._generate_routing_alternatives(actual_decision, driver_location)
        elif decision_type == "escalation_timing":
            return self._generate_escalation_alternatives(actual_decision)
        elif decision_type == "response_structure":
            return self._generate_response_alternatives(actual_decision, driver_location)
        else:
            return []
    
    def _generate_routing_alternatives(self, actual_decision: Dict[str, Any],
                                      driver_location: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Generate alternative routing decisions"""
        current_station_id = actual_decision.get("station_id", "A")
        
        # Get alternative stations
        alternatives_data = self.digital_twin.get_alternative_stations(
            current_station_id,
            driver_location
        )
        
        alternatives = []
        
        # Alternative 1: Best alternative station (lowest wait time)
        if alternatives_data:
            best_station = alternatives_data[0]
            alternatives.append({
                "decision_type": "station_routing",
                "station_id": best_station["station_id"],
                "description": f"Route to {best_station['station_name']} (better availability)"
            })
        
        # Alternative 2: Ask driver preference (response structure alternative)
        alternatives.append({
            "decision_type": "response_structure",
            "response_style": "clarifying",
            "description": "Ask driver preference before routing"
        })
        
        return alternatives
    
    def _generate_escalation_alternatives(self, actual_decision: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alternative escalation decisions"""
        current_action = actual_decision.get("escalation_action", "none")
        
        alternatives = []
        
        if current_action != "immediate":
            alternatives.append({
                "decision_type": "escalation_timing",
                "escalation_action": "immediate",
                "description": "Escalate immediately to supervisor"
            })
        
        if current_action != "none":
            alternatives.append({
                "decision_type": "escalation_timing",
                "escalation_action": "none",
                "description": "Handle without escalation"
            })
        
        return alternatives
    
    def _generate_response_alternatives(self, actual_decision: Dict[str, Any],
                                       driver_location: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Generate alternative response structure decisions"""
        current_style = actual_decision.get("response_style", "direct")
        
        alternatives = []
        
        if current_style != "clarifying":
            alternatives.append({
                "decision_type": "response_structure",
                "response_style": "clarifying",
                "description": "Ask driver preference before routing"
            })
        
        # Also suggest a better routing option if available
        if driver_location:
            alternatives_data = self.digital_twin.get_alternative_stations("A", driver_location)
            if alternatives_data:
                best_station = alternatives_data[0]
                alternatives.append({
                    "decision_type": "station_routing",
                    "station_id": best_station["station_id"],
                    "description": f"Route to {best_station['station_name']} (better availability)"
                })
        
        return alternatives
    
    def compare(self, actual_decision: Dict[str, Any], 
               alternatives: List[Dict[str, Any]],
               driver_location: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Compare actual decision with alternatives.
        
        Returns:
            {
                "alternatives": [
                    {
                        "option": str,
                        "expected_wait_time": float,
                        "congestion_risk": str,
                        "repeat_call_risk": str,
                        "description": str,
                        "improvement": Dict
                    }
                ],
                "best_option": Dict
            }
        """
        # Simulate actual decision
        actual_result = self.digital_twin.simulate_decision(actual_decision, driver_location)
        actual_result["is_actual"] = True
        actual_result["description"] = "Original decision"
        
        # Simulate alternatives
        simulated_alternatives = []
        for alt in alternatives:
            alt_result = self.digital_twin.simulate_decision(alt, driver_location)
            alt_result["description"] = alt.get("description", alt_result["option"])
            alt_result["is_actual"] = False
            alt_result["decision_type"] = alt.get("decision_type")  # Preserve decision type
            
            # Calculate improvement metrics
            wait_improvement = actual_result["expected_wait_time"] - alt_result["expected_wait_time"]
            wait_improvement_pct = (wait_improvement / actual_result["expected_wait_time"] * 100) if actual_result["expected_wait_time"] > 0 else 0
            
            alt_result["improvement"] = {
                "wait_time_reduction": round(wait_improvement, 1),
                "wait_time_reduction_pct": round(wait_improvement_pct, 1),
                "congestion_improved": self._risk_improved(
                    actual_result["congestion_risk"],
                    alt_result["congestion_risk"]
                ),
                "repeat_call_improved": self._risk_improved(
                    actual_result["repeat_call_risk"],
                    alt_result["repeat_call_risk"]
                )
            }
            
            simulated_alternatives.append(alt_result)
        
        # Find best option (lowest wait time, then lowest risks)
        # Prioritize alternatives of the same decision type as actual
        actual_decision_type = actual_decision.get("decision_type")
        
        # Filter alternatives by decision type match
        same_type_alternatives = [
            alt for alt in simulated_alternatives
            if alt.get("decision_type") == actual_decision_type
        ]
        
        # If we have same-type alternatives, prefer those
        # Otherwise, use all alternatives
        candidates = same_type_alternatives if same_type_alternatives else simulated_alternatives
        
        if not candidates:
            # Fallback to all alternatives if no candidates
            candidates = simulated_alternatives
        
        best_option = min(
            candidates,
            key=lambda x: (
                x["expected_wait_time"],
                self._risk_score(x["congestion_risk"]),
                self._risk_score(x["repeat_call_risk"])
            )
        ) if candidates else simulated_alternatives[0] if simulated_alternatives else None
        
        return {
            "alternatives": [actual_result] + simulated_alternatives,
            "best_option": best_option
        }
    
    def _risk_improved(self, actual_risk: str, alt_risk: str) -> bool:
        """Check if risk improved"""
        risk_levels = {"Low": 1, "Medium": 2, "High": 3}
        return risk_levels.get(alt_risk, 2) < risk_levels.get(actual_risk, 2)
    
    def _risk_score(self, risk: str) -> int:
        """Convert risk to numeric score"""
        risk_levels = {"Low": 1, "Medium": 2, "High": 3}
        return risk_levels.get(risk, 2)
