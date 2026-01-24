"""
Micro Digital Twin Simulator Module

Simulates station operations using deterministic logic.
Models: capacity, current load, service time, distance.
"""

from typing import Dict, Any, List, Optional
import math

class DigitalTwinSimulator:
    """
    Micro digital twin for battery swapping stations.
    Simulates wait time, congestion risk, and repeat-call probability.
    """
    
    def __init__(self, stations: List[Dict[str, Any]]):
        """
        Initialize with station data.
        
        Expected station format:
        {
            "id": str,
            "name": str,
            "capacity": int,
            "current_load": int,
            "avg_service_time": float,  # minutes
            "location": {"lat": float, "lon": float}
        }
        """
        self.stations = {station["id"]: station for station in stations}
    
    def simulate_decision(self, decision: Dict[str, Any], 
                         driver_location: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Simulate the outcome of an agent decision.
        
        Returns:
            {
                "option": str,
                "expected_wait_time": float,
                "congestion_risk": str,
                "repeat_call_risk": str
            }
        """
        decision_type = decision.get("decision_type")
        
        if decision_type == "station_routing":
            return self._simulate_routing(decision, driver_location)
        elif decision_type == "escalation_timing":
            return self._simulate_escalation(decision)
        elif decision_type == "response_structure":
            return self._simulate_response(decision, driver_location)
        else:
            return {
                "option": "Unknown",
                "expected_wait_time": 0.0,
                "congestion_risk": "Low",
                "repeat_call_risk": "Low"
            }
    
    def _simulate_routing(self, decision: Dict[str, Any], 
                         driver_location: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Simulate station routing decision"""
        station_id = decision.get("station_id", "A")
        station = self.stations.get(station_id)
        
        if not station:
            # Default station if not found
            station = list(self.stations.values())[0]
        
        # Calculate expected wait time using queue approximation
        # M/M/1 queue approximation: wait_time = (load / capacity) * avg_service_time
        load_ratio = station["current_load"] / station["capacity"]
        
        # Base wait time from queue
        queue_wait = load_ratio * station["avg_service_time"]
        
        # Add travel time if driver location provided
        travel_time = 0.0
        if driver_location:
            travel_time = self._estimate_travel_time(
                driver_location,
                station["location"]
            )
        
        expected_wait_time = queue_wait + travel_time
        
        # Determine congestion risk
        if load_ratio >= 0.8:
            congestion_risk = "High"
        elif load_ratio >= 0.5:
            congestion_risk = "Medium"
        else:
            congestion_risk = "Low"
        
        # Estimate repeat-call risk based on wait time and congestion
        if expected_wait_time > 10 or congestion_risk == "High":
            repeat_call_risk = "High"
        elif expected_wait_time > 5 or congestion_risk == "Medium":
            repeat_call_risk = "Medium"
        else:
            repeat_call_risk = "Low"
        
        option_name = f"Route to Station {station_id}"
        
        return {
            "option": option_name,
            "expected_wait_time": round(expected_wait_time, 1),
            "congestion_risk": congestion_risk,
            "repeat_call_risk": repeat_call_risk,
            "station_id": station_id,
            "load_ratio": round(load_ratio, 2)
        }
    
    def _simulate_escalation(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate escalation timing decision"""
        escalation_action = decision.get("escalation_action", "none")
        
        # Escalation timing affects wait time and repeat-call risk
        if escalation_action == "delayed":
            # Delayed escalation increases wait time
            expected_wait_time = 12.0
            repeat_call_risk = "High"
        elif escalation_action == "immediate":
            # Immediate escalation reduces wait time
            expected_wait_time = 3.0
            repeat_call_risk = "Low"
        else:
            # No escalation
            expected_wait_time = 8.0
            repeat_call_risk = "Medium"
        
        congestion_risk = "Low"  # Escalation doesn't directly affect congestion
        
        option_name = f"Escalation: {escalation_action.title()}"
        
        return {
            "option": option_name,
            "expected_wait_time": round(expected_wait_time, 1),
            "congestion_risk": congestion_risk,
            "repeat_call_risk": repeat_call_risk
        }
    
    def _simulate_response(self, decision: Dict[str, Any], 
                          driver_location: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Simulate response structure decision"""
        response_style = decision.get("response_style", "direct")
        
        # Response structure affects repeat-call risk
        if response_style == "vague":
            # Vague responses lead to confusion and repeat calls
            expected_wait_time = 7.0
            repeat_call_risk = "High"
        elif response_style == "clarifying":
            # Clarifying reduces repeat calls
            expected_wait_time = 4.0
            repeat_call_risk = "Low"
        else:
            # Direct response
            expected_wait_time = 5.0
            repeat_call_risk = "Medium"
        
        congestion_risk = "Low"  # Response style doesn't directly affect congestion
        
        option_name = f"Response: {response_style.title()}"
        
        return {
            "option": option_name,
            "expected_wait_time": round(expected_wait_time, 1),
            "congestion_risk": congestion_risk,
            "repeat_call_risk": repeat_call_risk
        }
    
    def _estimate_travel_time(self, driver_loc: Dict[str, float], 
                            station_loc: Dict[str, float]) -> float:
        """
        Estimate travel time using simple distance calculation.
        Uses Haversine formula for distance, then estimates time.
        """
        # Haversine distance calculation
        R = 6371  # Earth radius in km
        
        lat1 = math.radians(driver_loc["lat"])
        lat2 = math.radians(station_loc["lat"])
        dlat = math.radians(station_loc["lat"] - driver_loc["lat"])
        dlon = math.radians(station_loc["lon"] - driver_loc["lon"])
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance_km = R * c
        
        # Estimate travel time: assume average speed of 40 km/h in city
        # Cap travel time at 15 minutes for realistic city scenarios
        travel_time_minutes = min((distance_km / 40) * 60, 15.0)
        
        return travel_time_minutes
    
    def get_alternative_stations(self, current_station_id: str, 
                                driver_location: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Get alternative stations sorted by estimated wait time"""
        alternatives = []
        
        for station_id, station in self.stations.items():
            if station_id == current_station_id:
                continue
            
            # Create a decision for this station
            decision = {
                "decision_type": "station_routing",
                "station_id": station_id
            }
            
            # Simulate this station
            result = self._simulate_routing(decision, driver_location)
            alternatives.append({
                "station_id": station_id,
                "station_name": station.get("name", f"Station {station_id}"),
                **result
            })
        
        # Sort by expected wait time
        alternatives.sort(key=lambda x: x["expected_wait_time"])
        
        return alternatives
