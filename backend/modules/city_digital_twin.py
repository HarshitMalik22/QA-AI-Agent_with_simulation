
from typing import Dict, Any, List, Optional
import math
import random
import copy
import os
import json

class CityDigitalTwin:
    """
    City-Scale Digital Twin Simulator.
    Simulates a network of stations over a time period (e.g., 24 hours).
    Enables "what-if" analysis for network optimization.
    """

    def __init__(self, stations_data: List[Dict[str, Any]]):
        """
        Initialize the city network.
        
        stations_data expected format:
        [
            {
                "id": "BS-001",
                "name": "Station A",
                "total_slots": 20,
                "chargers": 15,
                "initial_inventory": 18, (charged batteries)
                "location": {"lat": 28.6, "lon": 77.1}
            },
            ...
        ]
        """
        self.initial_state = copy.deepcopy(stations_data)
        self.stations = {s["id"]: self._init_station_state(s) for s in stations_data}
        self.global_demand_modifier = 1.0
        self.simulation_duration_hours = 24
        
        # Load Real Data Config
        self.config = self._load_simulation_config()
        
        # Simulation Constants
        self.CHARGE_TIME_MINUTES = self.config.get("avg_charge_time_minutes", 60)
        self.SWAP_TIME_MINUTES = 3
        
        # Demand Curve (normalized 0-1 probability per hour)
        self.demand_curve = self.config.get("demand_curve_hourly", [])
        
    def _load_simulation_config(self) -> Dict[str, Any]:
        """Load calibrated parameters from JSON"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "simulation_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load simulation config: {e}")
        return {} # Fallback to defaults

    def _init_station_state(self, station_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize dynamic state for a single station"""
        s = copy.deepcopy(station_data)
        # Default defaults if missing
        s.setdefault("total_slots", 15)
        s.setdefault("chargers", 12) # Increased default
        s.setdefault("initial_inventory", 10)
        
        # Dynamic State
        s["inventory_ready"] = s["initial_inventory"]
        s["inventory_charging"] = [] 
        s["queue_length"] = 0
        
        # Metrics Accumulators
        s["metrics"] = {
            "total_swaps_fulfilled": 0,
            "lost_swaps": 0,
            "total_wait_time_minutes": 0,
            "idle_inventory_minutes": 0,
            "charger_utilization_minutes": 0
        }
        return s

    def run_simulation(self, interventions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Run the 24-hour simulation with optional interventions.
        
        Interventions format:
        [
            {"type": "add_station", "data": {...}},
            {"type": "modify_chargers", "station_id": "BS-001", "count": 20},
            {"type": "shift_demand", "factor": 1.2, "window": (18, 20)} # +20% during 6-8 PM
        ]
        """
        # 1. Reset State
        self.stations = {s["id"]: self._init_station_state(s) for s in self.initial_state}
        self.global_demand_modifier = 1.0
        
        # 2. Apply Static Interventions (Topology changes)
        if interventions:
            self._apply_static_interventions(interventions)
            
        # 3. Time-Step Loop (Minute by Minute)
        # We simulate 24 hours = 1440 minutes
        minutes_total = self.simulation_duration_hours * 60
        
        for minute in range(minutes_total):
            current_hour = minute / 60.0
            
            # Apply Dynamic Interventions (Demand shifts)
            demand_mod = self._get_current_demand_modifier(current_hour, interventions)
            
            for station_id, station in self.stations.items():
                self._simulate_station_step(station, minute, current_hour, demand_mod)
                
        # 4. Aggregated Results
        return self._generate_report()

    def _apply_static_interventions(self, interventions: List[Dict[str, Any]]):
        """Apply structural changes before sim starts"""
        for action in interventions:
            if action["type"] == "add_station":
                data = action["data"]
                self.stations[data["id"]] = self._init_station_state(data)
                
            elif action["type"] == "remove_station":
                sid = action.get("station_id")
                if sid in self.stations:
                    del self.stations[sid]
                    
            elif action["type"] == "modify_chargers":
                sid = action.get("station_id")
                if sid in self.stations:
                    self.stations[sid]["chargers"] = action["count"]

    def _get_current_demand_modifier(self, hour: float, interventions: Optional[List[Dict[str, Any]]]) -> float:
        """Calculate demand multiplier for current time"""
        base_mod = 1.0
        
        if interventions:
            for action in interventions:
                if action["type"] == "shift_demand":
                    start, end = action.get("window", (0, 24))
                    if start <= hour < end:
                        base_mod *= action.get("factor", 1.0)
                        
        return base_mod

    def _simulate_station_step(self, station: Dict[str, Any], minute: int, hour: float, demand_mod: float):
        """Simulate one minute for one station"""
        
        # 1. Process Charging
        chargers_available = station["chargers"]
        active_charging_count = 0
        
        # Sort charging batteries: those closest to done get priority if chargers limited
        # (Though in reality chargers are 1:1 usually, let's assume smart allocation)
        station["inventory_charging"].sort()
        
        next_charging_state = []
        for time_left in station["inventory_charging"]:
            if chargers_available > 0:
                chargers_available -= 1
                active_charging_count += 1
                new_time = time_left - 1
                
                if new_time <= 0:
                    station["inventory_ready"] += 1
                else:
                    next_charging_state.append(new_time)
            else:
                next_charging_state.append(time_left)
                
        station["inventory_charging"] = next_charging_state
        station["metrics"]["charger_utilization_minutes"] += active_charging_count
        
        # Track Idle Inventory
        if station["inventory_ready"] > 0:
            station["metrics"]["idle_inventory_minutes"] += station["inventory_ready"]

        # 2. Process Arrivals
        arrival_prob = self._get_arrival_probability(station, hour) * demand_mod
        
        if random.random() < arrival_prob:
            # Check capacity before joining queue
            # If Queue is huge (e.g. > 10 vehicles) OR (Queue > 5 AND No Batteries Ready) -> Lost Swap
            if station["queue_length"] > 10 or (station["queue_length"] > 5 and station["inventory_ready"] == 0):
                station["metrics"]["lost_swaps"] += 1
            else:
                station["queue_length"] += 1

        # 3. Process Service (Swaps)
        # Service rate: assume station can do X swaps per minute concurrently (bays)
        # 4 bays standard
        bays_free = 4
        
        while bays_free > 0 and station["queue_length"] > 0:
            if station["inventory_ready"] > 0:
                # Swap happens
                station["inventory_ready"] -= 1
                station["queue_length"] -= 1
                station["metrics"]["total_swaps_fulfilled"] += 1
                
                # Add drained battery to charging
                station["inventory_charging"].append(self.CHARGE_TIME_MINUTES)
                bays_free -= 1
            else:
                # Bays free but no batteries -> Wait
                # Break loop, can't serve anyone else this minute
                break
        
        # Accumulate wait time for everyone still in queue
        station["metrics"]["total_wait_time_minutes"] += station["queue_length"]

    def _get_arrival_probability(self, station: Dict[str, Any], hour: float) -> float:
        """
        Get arrival probability into this minute.
        """
        # If we have real data curve, use it
        if self.demand_curve:
            hour_idx = int(hour) % 24
            # Config curve is normalized 0-1. 
            # We need to map it to a realistic probability per minute.
            # Let's assume Peak Hour = 0.4 arrivals/min (24 swaps/hour) for a busy station
            base_peak_rate = 0.4 
            
            prob = self.demand_curve[hour_idx] * base_peak_rate
            return prob
            
        # Fallback: Standard Double-Hump Profile
        base_rate = 0.05 
        morning_peak = math.exp(-0.5 * ((hour - 9) / 2) ** 2) * 0.2
        evening_peak = math.exp(-0.5 * ((hour - 18) / 2) ** 2) * 0.25
        
        return base_rate + morning_peak + evening_peak

    def _generate_report(self) -> Dict[str, Any]:
        """Compile final simulation statistics"""
        
        network_summary = {
            "total_swaps": 0,
            "lost_swaps": 0,
            "avg_wait_time": 0.0,
            "stations": {}
        }
        
        total_wait_mins = 0
        total_swaps = 0
        
        for sid, st in self.stations.items():
            m = st["metrics"]
            
            # Derived Metrics
            swaps = m["total_swaps_fulfilled"]
            avg_wait = (m["total_wait_time_minutes"] / swaps) if swaps > 0 else 0
            
            # Avoid div by zero for utilization
            total_charger_minutes = st["chargers"] * self.simulation_duration_hours * 60
            utilization_pct = (m["charger_utilization_minutes"] / total_charger_minutes * 100) if total_charger_minutes > 0 else 0
            
            st_report = {
                "swaps": swaps,
                "lost_swaps": m["lost_swaps"],
                "avg_wait_time_min": round(avg_wait, 1),
                "charger_utilization_pct": round(utilization_pct, 1),
                "idle_inventory_min": m["idle_inventory_minutes"]
            }
            
            network_summary["stations"][sid] = st_report
            
            network_summary["total_swaps"] += swaps
            network_summary["lost_swaps"] += m["lost_swaps"]
            total_wait_mins += m["total_wait_time_minutes"]
            total_swaps += swaps
            
        if total_swaps > 0:
            network_summary["avg_wait_time"] = round(total_wait_mins / total_swaps, 1)
            
        return network_summary
