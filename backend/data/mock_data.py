"""
Mock Data for Digital Twin Simulation

Realistic but simplified data for demo purposes.
"""

MOCK_STATIONS = [
    {
        "id": "A",
        "name": "Station A - Tilak Nagar",
        "capacity": 10,
        "current_load": 9, 
        "avg_service_time": 5.0,
        "location": {"lat": 28.6366, "lon": 77.0965}
    },
    {
        "id": "B",
        "name": "Station B - Rajouri Garden",
        "capacity": 12,
        "current_load": 2, 
        "avg_service_time": 4.5,
        "location": {"lat": 28.6415, "lon": 77.1209}
    },
    {
        "id": "C",
        "name": "Station C - Okhla Phase 3",
        "capacity": 8,
        "current_load": 6,
        "avg_service_time": 5.5,
        "location": {"lat": 28.5272, "lon": 77.2644}
    },
    {
        "id": "D",
        "name": "Station D - Mayapuri",
        "capacity": 15,
        "current_load": 4,
        "avg_service_time": 4.0,
        "location": {"lat": 28.6289, "lon": 77.1132}
    }
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
