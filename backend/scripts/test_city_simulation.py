
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from modules.city_digital_twin import CityDigitalTwin

# 1. Setup Mock Network
stations_data = [
    {
        "id": "S1",
        "name": "Janakpuri Central",
        "total_slots": 20,
        "chargers": 12,
        "initial_inventory": 15,
        "location": {"lat": 28.6219, "lon": 77.0878}
    },
    {
        "id": "S2",
        "name": "Uttam Nagar East",
        "total_slots": 15,
        "chargers": 8,
        "initial_inventory": 8,
        "location": {"lat": 28.6273, "lon": 77.0565}
    }
]

def print_results(title, result):
    print(f"\n--- {title} ---")
    print(f"Total Swaps: {result['total_swaps']}")
    print(f"Lost Swaps: {result['lost_swaps']}")
    print(f"Avg Wait Time: {result['avg_wait_time']} min")
    print("Starions Detail:")
    for sid, data in result["stations"].items():
        print(f"  {sid}: {data['swaps']} swaps, {data['lost_swaps']} lost, Wait: {data['avg_wait_time_min']}m, Util: {data['charger_utilization_pct']}%")

def main():
    print("Initializing City Digital Twin...")
    sim = CityDigitalTwin(stations_data)
    
    # 1. Base Run
    print("\nRunning Base Simulation (24h)...")
    base_result = sim.run_simulation()
    print_results("BASE SCENARIO", base_result)
    
    # 2. Intervention: Add Station
    print("\nRunning Intervention: New Station 'S3'...")
    intervention_add = [
        {
            "type": "add_station", 
            "data": {
                "id": "S3", 
                "name": "Relief Station", 
                "chargers": 10, 
                "initial_inventory": 10
            }
        }
    ]
    interv_result = sim.run_simulation(intervention_add)
    print_results("SCENARIO: ADD STATION S3", interv_result)
    
    # 3. Intervention: Shift Demand
    print("\nRunning Intervention: Festival Surge (+50% Demand)...")
    intervention_surge = [
        {"type": "shift_demand", "factor": 1.5, "window": (8, 22)}
    ]
    surge_result = sim.run_simulation(intervention_surge)
    print_results("SCENARIO: FESTIVAL SURGE", surge_result)

if __name__ == "__main__":
    main()
