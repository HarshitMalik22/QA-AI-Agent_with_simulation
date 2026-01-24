"""
Decision Emitter Module

Emits structured decision contracts to drive the closed-loop system.
This serves as the "source of truth" for the decision pipeline.
"""

import uuid
from typing import Dict, Any

class DecisionEmitter:
    """
    Simulates an agent making explicit decisions.
    For the demo, this emits a 'bad' decision to demonstrate the improvement loop.
    """
    
    def emit_decision(self) -> Dict[str, Any]:
        """
        Emit a structured decision contract.
        
        Scenario: Driver is at Dwarka Mor. 
        Agent routes to Tilak Nagar (Station A) which is congested.
        """
        return {
            "decision_id": str(uuid.uuid4()),
            "driver_context": {
                "location": "Dwarka Mor",
                "battery_pct": 18,
                "coordinates": {"lat": 28.6196, "lon": 77.0332} # Dwarka Mor approx
            },
            "agent_decision": {
                "decision_type": "station_routing",
                "recommended_station": "A", # Station A - Tilak Nagar (Congested)
                "primary_reason": "closest_distance",
                "tradeoff_acknowledged": False
            }
        }
