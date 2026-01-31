"""
Mock Data for Digital Twin Simulation

Realistic but simplified data for demo purposes.
"""

import pandas as pd
import os

# Load Partner Data from CSV
# File: Partners.xlsx - result.csv
# Columns: id, latitude, longitude, isActiveDsk

csv_path = os.path.join(os.path.dirname(__file__), "Partners.xlsx - result.csv")

try:
    df = pd.read_csv(csv_path)
    
    # Transform to MOCK_STATIONS format
    MOCK_STATIONS = []
    
    for _, row in df.iterrows():
        try:
            # Handle potential non-numeric lat/long
            lat = float(row['latitude'])
            lon = float(row['longitude'])
            
            # Skip invalid coordinates (0,0 or incomplete)
            if lat == 0 or lon == 0 or (lat == 26 and lon == 80): 
                 continue
            
            MOCK_STATIONS.append({
                "id": str(row['id']),
                "name": f"Station {row['id']}", 
                "capacity": 20, # Default capacity
                "current_load": 5, # Default load
                "avg_service_time": 4.0, # Default time
                "location": {"lat": lat, "lon": lon},
                "is_dsk": bool(row.get('isActiveDsk', False))
            })
        except ValueError:
            continue
            
    print(f"Loaded {len(MOCK_STATIONS)} stations from CSV.")

except Exception as e:
    print(f"Error loading CSV: {e}. Falling back to mock data.")
    MOCK_STATIONS = [
        {
            "id": "BS-001",
            "name": "Tilak Nagar - Main Market",
            "capacity": 15,
            "current_load": 12, 
            "avg_service_time": 4.5,
            "location": {"lat": 28.6366, "lon": 77.0965}
        },
        # ... (Fallback if needed, or kept minimal)
    ]


MOCK_TRANSCRIPTS = [
    {
        "call_id": "BS-1024",
        "transcript": """
        Agent: Battery Smart Support, Priya speaking.
        Driver: Hello madam, my rickshaw is at 12% charge. I am near Tilak Nagar metro. The app shows the main market station is red, but I am very close to it. Should I go there?
        Agent: Yes bhaiyya, just go to the Tilak Nagar market station. It is the closest one to you.
        Driver: Are you sure? Last time I got stuck there for 20 minutes. My passenger is in a hurry.
        Agent: It's okay, the line moves fast. Just go there, it will be fine.
        Driver: Okay madam, if you say so. I am going.
        """,
        "driver_location": {"lat": 28.6366, "lon": 77.0965}  # Near Tilak Nagar
    },
    {
        "call_id": "BS-1025",
        "transcript": """
        Agent: Battery Smart Helpdesk.
        Driver: Arre sir, the battery is stuck inside the dock! I put my old battery in, but the new one is not coming out. Station ID is 402 near Okhla Phase 3.
        Agent: Okay, don't worry. I am raising a ticket for the field technician. He will come and check the locking mechanism.
        Driver: Technician? How long will that take? I have school duty in 30 minutes!
        Agent: It might take 1-2 hours for him to reach. Please wait there.
        Driver: 2 hours?! My whole day is wasted! Is there no other way?
        Agent: Sorry, we have to wait for the technician for safety reasons.
        """,
        "driver_location": {"lat": 28.5272, "lon": 77.2644}  # Okhla
    },
    {
        "call_id": "BS-1026",
        "transcript": """
        Agent: Namaste, Battery Smart support.
        Driver: Madam, I am at the Mayapuri crossing. My meter shows 8km range left. The app is confusing me. Where should I go?
        Agent: Okay, I see you. Station A is 2km away but has a queue of 4 rickshaws. Station B is 3.5km away towards Rajouri, but it is completely empty.
        Driver: 3.5km... will I make it?
        Agent: Yes, you have 8km range. If you go to Station A, you will wait 15 minutes. If you go to Station B, you will reach in 10 minutes and swap immediately.
        Driver: Okay, that sounds better. I will go to Rajouri.
        Agent: Perfect. Driving specifically to Station B will save you time.
        """,
        "driver_location": {"lat": 28.6289, "lon": 77.1132}  # Mayapuri
    },
    {
        "call_id": "BS-1027",
        "transcript": """
        Agent: Battery Smart Support.
        Driver: Sir, I reached the station but the QR code scanner is not working on my app. I cannot start the swap.
        Agent: Try cleaning the camera lens.
        Driver: I did that, it's still black screen.
        Agent: Okay, maybe... just try restarting your phone? Or I don't know, maybe go to another station?
        Driver: Sir, I am already here. Can't you do something from your side?
        Agent: I think it's your phone issue. Just try properly.
        """,
        "driver_location": {"lat": 28.6139, "lon": 77.2090}
    }
]

# Pricing Constants
BASE_SWAP_PRICE = 170
SECONDARY_SWAP_PRICE = 70
LEAVE_PENALTY_TOTAL = 120
LEAVE_PENALTY_PER_SWAP = 60
SERVICE_CHARGE = 40
ALLOWED_LEAVES_PER_MONTH = 4

MOCK_SUBSCRIPTION_PLANS = {
    "basic": {"name": "Basic Plan", "price": 499, "validity_days": 28, "swaps": 10},
    "smart_saver": {"name": "Smart Saver", "price": 999, "validity_days": 28, "swaps": 25},
    "unlimited": {"name": "Unlimited Power", "price": 1999, "validity_days": 28, "swaps": 999}
}

MOCK_DRIVERS = {
    "+919876543210": {
        "id": "D121604",
        "name": "Ramesh Kumar",
        "plan": "smart_saver",
        "plan_expiry": "2024-02-15",
        "balance": 450,
        "leaves_taken": 2,
        "pending_penalty": 0,
        "home_station": "BS-001"
    },
    "+918595789129": {
        "id": "D998877",
        "name": "Suresh Verma",
        "plan": "unlimited",
        "plan_expiry": "2024-02-20",
        "balance": 680,
        "leaves_taken": 1,
        "pending_penalty": 0,
        "home_station": "BS-002"
    },
    "+11234567890": {
        "id": "D000000",
        "name": "Test Driver",
        "plan": "basic",
        "plan_expiry": "2024-02-10",
        "balance": 100,
        "leaves_taken": 5,
        "pending_penalty": 120,
        "home_station": "BS-002"
    }
}

MOCK_SWAP_HISTORY = {
    "+11234567890": [
        {"date": "2024-01-25", "station": "Station A", "units": 1.2, "amount": 210, "status": "Success"},
        {"date": "2024-01-23", "station": "Station B", "units": 1.1, "amount": 110, "status": "Success"},
        {"date": "2024-01-20", "station": "Station A", "units": 1.3, "amount": 210, "status": "failed"}
    ],
    "+919876543210": [
        {"date": "2024-01-30", "station": "Tilak Nagar - Main Market", "units": 1.5, "amount": 210, "status": "Success"},
        {"date": "2024-01-28", "station": "Janakpuri DSK", "units": 1.1, "amount": 210, "status": "Success"}
    ]
}

MOCK_DSK_CENTERS = [
    {
        "name": "DSK Janakpuri",
        "address": "B-12, Community Centre, Janakpuri",
        "phone": "+91-11-25550101",
        "location": {"lat": 28.6219, "lon": 77.0878}
    },
    {
        "name": "DSK Dwarka",
        "address": "Sector 12, Market Complex, Dwarka",
        "phone": "+91-11-28030202",
        "location": {"lat": 28.5921, "lon": 77.0460}
    },
    {
        "name": "DSK Uttam Nagar",
        "address": "Near East Metro Station, Uttam Nagar",
        "phone": "+91-9810098100",
        "location": {"lat": 28.6273, "lon": 77.0565}
    }
]

# KNOWN_LOCATIONS removed - using geocoding API instead
