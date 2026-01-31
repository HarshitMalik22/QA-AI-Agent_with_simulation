import math
import requests
from data.mock_data import MOCK_STATIONS, MOCK_DRIVERS, MOCK_SWAP_HISTORY, MOCK_SUBSCRIPTION_PLANS, MOCK_DSK_CENTERS, ALLOWED_LEAVES_PER_MONTH

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

    return {"plans": MOCK_SUBSCRIPTION_PLANS}

def verify_driver_by_id(driver_id: str, name: str = None):
    """
    INSTANT verification of driver by their Driver ID.
    """
    found_driver = None
    found_phone = None
    for phone, d in MOCK_DRIVERS.items():
        if d.get("id") == driver_id:
            found_driver = d
            found_phone = phone
            break
    
    if found_driver:
        return {"verified": True, "name": found_driver["name"], "phone": found_phone, "details": found_driver}
    return {"verified": False, "error": "Invalid Driver ID"}

def report_issue(issue_type: str, description: str, customer_phone: str = None):
    """
    Report a technical or operational issue.
    """
    ticket_id = f"TKT-{abs(hash(description)) % 10000}"
    print(f"ISSUE REPORTED: {issue_type} - {description} (Ticket: {ticket_id})")
    return {"status": "success", "ticket_id": ticket_id, "message": "Ticket raised successfully"}

def check_penalty_status(phone_number: str):
    """
    Check if the driver has any penalties.
    """
    driver = MOCK_DRIVERS.get(phone_number)
    if not driver:
        return {"error": "Driver not found"}
    
    return {
        "has_penalty": driver.get("pending_penalty", 0) > 0,
        "penalty_amount": driver.get("pending_penalty", 0),
        "leaves_taken": driver.get("leaves_taken", 0),
        "allowed_leaves": ALLOWED_LEAVES_PER_MONTH
    }

def escalate_to_agent(reason: str, customer_phone: str = None):
    """
    Transfer the call to a human agent.
    """
    print(f"ESCALATING CALL: {customer_phone} - Reason: {reason}")
    return {"status": "escalated", "message": "Call transferred to human agent"}

# Tool Definitions for Vapi/OpenAI
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "verify_driver_by_id",
            "description": "INSTANT verification of driver by their Driver ID (e.g., D121604, D998877). Use this IMMEDIATELY when a driver provides their ID. Returns verified status and driver details. Optionally verify name too.",
            "parameters": {
                "type": "object",
                "properties": {
                    "driver_id": {"type": "string", "description": "The Driver ID provided by the user"},
                    "name": {"type": "string", "description": "Optional name to verify against"}
                },
                "required": ["driver_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_driver_profile",
            "description": "Get driver details including name, current plan, balance and validity. Use with caller's phone number for account queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "The driver's phone number exactly as appeared in caller ID (e.g. +11234567890)"
                    },
                    "driver_id": {
                        "type": "string",
                        "description": "Optional driver ID if known"
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
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_agent",
            "description": "Transfer the call to a human agent. Use this ONLY when: 1. User is angry/abusive. 2. User explicitly asks for a human. 3. You cannot solve the query after 2 attempts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Reason for escalation"},
                    "customer_phone": {"type": "string", "description": "Customer's phone number"}
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "report_issue",
            "description": "Report a technical or operational issue (e.g., Less Range, Hardware Broken, Station Closed).",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_type": {"type": "string", "description": "Type of issue"},
                    "description": {"type": "string", "description": "Description of the issue"},
                    "customer_phone": {"type": "string", "description": "Customer's phone number"}
                },
                "required": ["issue_type", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_penalty_status",
            "description": "Check if the driver has any penalties or leave restrictions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {"type": "string", "description": "The driver's phone number."}
                },
                "required": ["phone_number"]
            }
        }
    }
]
