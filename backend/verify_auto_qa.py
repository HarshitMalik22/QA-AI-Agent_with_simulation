import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_analyze():
    print("Testing Analysis Endpoint...")
    payload = {
        "transcript": "Driver: Hello, I am at Paschim Vihar. My battery is low. Agent: Go to station BS-001. It is very busy but you can go. Driver: Okay.",
        "call_id": "test_call_001",
        "driver_location": {"lat": 28.6, "lon": 77.2},
        "agent_id": "AI_TEST_01",
        "city": "Gurgaon"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/analyze", json=payload)
        response.raise_for_status()
        data = response.json()
        print("Analysis Response:", json.dumps(data, indent=2)[:500] + "...")
        print("✅ Analysis Endpoint Works")
    except Exception as e:
        print(f"❌ Analysis Failed: {e}")

def test_aggregated_insights():
    print("\nTesting Aggregated Insights...")
    try:
        response = requests.get(f"{BASE_URL}/api/insights/aggregated")
        response.raise_for_status()
        data = response.json()
        print("Aggregated Data:", json.dumps(data, indent=2))
        print("✅ Aggregated Insights Endpoint Works")
    except Exception as e:
        print(f"❌ Aggregated Insights Failed: {e}")

def test_flags():
    print("\nTesting Supervisor Flags...")
    try:
        response = requests.get(f"{BASE_URL}/api/insights/flags")
        response.raise_for_status()
        data = response.json()
        print("Flags Data:", json.dumps(data, indent=2))
        print("✅ Supervisor Flags Endpoint Works")
    except Exception as e:
        print(f"❌ Supervisor Flags Failed: {e}")

if __name__ == "__main__":
    # Ensure server is running (user already has it running, but we might need to wait if it restarted)
    # Since I edited main.py, uvicorn with reload might be restarting.
    time.sleep(2) 
    
    test_analyze()
    test_aggregated_insights()
    test_flags()
