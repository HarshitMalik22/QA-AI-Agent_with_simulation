import math
import requests
from data.mock_data import MOCK_STATIONS, MOCK_DRIVERS, MOCK_SWAP_HISTORY, MOCK_SUBSCRIPTION_PLANS, MOCK_DSK_CENTERS

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate Haversine distance between two points in km.
    """
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def get_driver_profile(phone_number: str):
    """
    Get driver's profile, plan, and balance.
    """
    driver = MOCK_DRIVERS.get(phone_number)
    if not driver:
        return {"error": "Driver not found", "is_registered": False}
    return {
        "name": driver["name"],
        "plan": driver["plan"],
        "plan_details": MOCK_SUBSCRIPTION_PLANS.get(driver["plan"]),
        "expiry": driver["plan_expiry"],
        "balance": driver["balance"],
        "is_registered": True
    }

def get_swap_history(phone_number: str):
    """
    Get last 3 swaps for the driver.
    """
    history = MOCK_SWAP_HISTORY.get(phone_number, [])
    return {"history": history[:3]}


def geocode_location(location_name: str):
    """
    Use Nominatim (OpenStreetMap) to geocode a location name to coordinates.
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{location_name}, India",
            "format": "json",
            "limit": 1
        }
        headers = {"User-Agent": "BatterySmartBot/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None


def resolve_location(lat, lon, location_name):
    """
    Resolve location from explicit coordinates or by geocoding a text input.
    """
    if lat and lon:
        return lat, lon
    if location_name:
        # Use geocoding API (no hardcoded data)
        return geocode_location(location_name)
    return None, None


def get_nearest_station(lat: float = None, lon: float = None, location_name: str = None):
    """
    Find nearest battery station with availability.
    """
    lat, lon = resolve_location(lat, lon, location_name)
    if not lat:
        return {"error": "Location not found. Please provide a known location name or coordinates."}

    stations_with_dist = []
    for stn in MOCK_STATIONS:
        dist = calculate_distance(lat, lon, stn["location"]["lat"], stn["location"]["lon"])
        stations_with_dist.append({**stn, "distance_km": round(dist, 1)})
    
    # Sort by distance
    stations_with_dist.sort(key=lambda x: x["distance_km"])
    
    # Return top 2
    return {"stations": stations_with_dist[:2]}

def get_nearest_dsk(lat: float = None, lon: float = None, location_name: str = None):
    """
    Find nearest DSK (Distributor/Service) center.
    """
    lat, lon = resolve_location(lat, lon, location_name)
    if not lat:
        return {"error": "Location not found. Please provide a known location name or coordinates."}

    dsks_with_dist = []
    for dsk in MOCK_DSK_CENTERS:
        dist = calculate_distance(lat, lon, dsk["location"]["lat"], dsk["location"]["lon"])
        dsks_with_dist.append({**dsk, "distance_km": round(dist, 1)})
    
    dsks_with_dist.sort(key=lambda x: x["distance_km"])
    return {"dsk_centers": dsks_with_dist[:2]}

def get_plan_details(plan_name: str = None):
    """
    Get details of a specific subscription plan or all plans.
    """
    if plan_name and plan_name in MOCK_SUBSCRIPTION_PLANS:
        return {"plan": MOCK_SUBSCRIPTION_PLANS[plan_name]}
    return {"plans": MOCK_SUBSCRIPTION_PLANS}

# Tool Definitions for Vapi/OpenAI
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_driver_profile",
            "description": "Get driver details including name, current plan, balance and validity. Use this when user asks about their account, balance or validity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "The driver's phone number exactly as appeared in caller ID (e.g. +11234567890)"
                    }
                },
                "required": ["phone_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_swap_history",
            "description": "Get recent battery swap history and invoice details. Use this when user asks about past swaps, deductions or invoices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "The driver's phone number."
                    }
                },
                "required": ["phone_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_nearest_station",
            "description": "Find nearest battery swapping station. Use this when user asks for station location or availability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude of the driver"},
                    "lon": {"type": "number", "description": "Longitude of the driver"},
                    "location_name": {"type": "string", "description": "Name of the location if coordinates are not available (e.g. Tilak Nagar)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_nearest_dsk",
            "description": "Find nearest DSK (Distributor Sales & Service Kit) center for activation or leaving the service. Use this when user wants to join, leave, or contact a distributor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude of the driver"},
                    "lon": {"type": "number", "description": "Longitude of the driver"},
                    "location_name": {"type": "string", "description": "Name of the location if coordinates are not available (e.g. Janakpuri)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_plan_details",
            "description": "Get information about subscription plans, pricing, and benefits. Use this when user asks about plan upgrades or pricing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_name": {
                        "type": "string",
                        "enum": ["basic", "smart_saver", "unlimited"],
                        "description": "Optional specific plan name to query."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_driver_location",
            "description": "Update the driver's current location on the live map. Use this heavily when the user states where they are (e.g., 'I am at Tilak Nagar').",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_name": {
                        "type": "string",
                        "description": "The name of the location the user is at (e.g. Tilak Nagar, Okhla)."
                    }
                },
                "required": ["location_name"]
            }
        }
    }
]
