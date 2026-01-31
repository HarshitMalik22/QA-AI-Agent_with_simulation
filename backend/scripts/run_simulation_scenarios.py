import requests
import json
import time

BASE_URL = "http://localhost:8000/api/simulation/run"

def run_scenario(name, interventions):
    print(f"\n🚀 Running Scenario: {name}...")
    start_time = time.time()
    
    try:
        response = requests.post(BASE_URL, json={"interventions": interventions})
        response.raise_for_status()
        data = response.json()
        
        duration = time.time() - start_time
        print(f"✅ Completed in {duration:.2f}s")
        
        # specific metrics
        print(f"   - Total Swaps: {data['total_swaps']}")
        print(f"   - Lost Swaps:  {data['lost_swaps']}")
        print(f"   - Avg Wait:    {data['avg_wait_time']} mins")
        
        return data
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("🔋 Battery Smart Digital Twin - Scenario Runner 🔋")
    print("================================================")

    # 1. Baseline
    base_data = run_scenario("1. Baseline (Normal Day)", [])

    # 2. Demand Surge
    surge_interventions = [
        {"type": "shift_demand", "factor": 1.5, "window": [8, 22]} # 50% more demand all day
    ]
    surge_data = run_scenario("2. Festival Surge (+50% Demand)", surge_interventions)

    # 3. Mitigation Strategy (Add Chargers)
    # Let's see which stations struggled in Scenario 2 and upgrade them
    # For simplicity, we just upgrade ALL stations or a few key ones
    mitigation_interventions = surge_interventions + [
        {"type": "modify_chargers", "station_id": "BS-001", "count": 30},
        {"type": "modify_chargers", "station_id": "BS-002", "count": 30}
    ]
    mitigation_data = run_scenario("3. Mitigation (Surge + Added Chargers)", mitigation_interventions)

    # Comparison
    print("\n📊 Impact Analysis")
    print("================================================")
    
    if base_data and surge_data and mitigation_data:
        # Calculate Delta
        lost_swaps_increase = surge_data['lost_swaps'] - base_data['lost_swaps']
        wait_time_increase = surge_data['avg_wait_time'] - base_data['avg_wait_time']
        
        mitigated_lost = surge_data['lost_swaps'] - mitigation_data['lost_swaps']
        
        print(f"📉 Impact of Surge:")
        print(f"   - Lost Swaps: +{lost_swaps_increase} (Revenue Risk!)")
        print(f"   - Wait Time:  +{wait_time_increase:.1f} mins")
        
        print(f"\n🛠 Impact of Upgrade:")
        print(f"   - Recovered Swaps: {mitigated_lost}")
        print(f"   - Wait Time Reduced: {surge_data['avg_wait_time'] - mitigation_data['avg_wait_time']:.1f} mins")

if __name__ == "__main__":
    main()
