
import time
import math
from data.mock_data import MOCK_STATIONS
from modules.assistant_tools import geocode_location

class DriverSimulation:
    def __init__(self):
        self.stations = MOCK_STATIONS
        self.current_station_idx = 0
        self.next_station_idx = 1
        self.speed_factor = 0.0001  # degrees per tick
        
        start_station = self.stations[self.current_station_idx]['location']
        self.current_lat = start_station['lat']
        self.current_lon = start_station['lon']
        self.last_update = time.time()

    def get_location(self):
        try:
            self._update_position()
        except Exception:
            pass # Fallback or ignore errors during update
        
        return {
            "lat": self.current_lat,
            "lon": self.current_lon,
            "heading": self._calculate_heading()
        }

    def _update_position(self):
        now = time.time()
        time_delta = now - self.last_update
        self.last_update = now
        
        # Simple movement: Move towards next station
        # Speed: 0.0001 deg/sec is roughly 11 meters/sec (40 km/h)
        speed = 0.0002 
        
        target = self.stations[self.next_station_idx]['location']
        
        lat_diff = target['lat'] - self.current_lat
        lon_diff = target['lon'] - self.current_lon
        
        distance = math.sqrt(lat_diff**2 + lon_diff**2)
        
        # Calculate max distance we can travel this tick
        travel_dist = speed * time_delta
        
        if distance < travel_dist:
            # Arrived, switch target
            self.current_station_idx = self.next_station_idx
            self.next_station_idx = (self.next_station_idx + 1) % len(self.stations)
            # Snap to station
            self.current_lat = target['lat']
            self.current_lon = target['lon']
        else:
            # Move
            ratio = travel_dist / distance
            self.current_lat += lat_diff * ratio
            self.current_lon += lon_diff * ratio

    def _calculate_heading(self):
        target = self.stations[self.next_station_idx]['location']
        lat_diff = target['lat'] - self.current_lat
        lon_diff = target['lon'] - self.current_lon
        return math.degrees(math.atan2(lon_diff, lat_diff))

    def set_location_by_name(self, location_name):
        """Teleport driver to a location using geocoding."""
        print(f"Teleporting driver to: {location_name}")
        lat, lon = geocode_location(location_name)
        if lat and lon:
            self.current_lat = lat
            self.current_lon = lon
            return {"status": "success", "location": {"lat": lat, "lon": lon}}
        return {"status": "error", "message": "Location not found"}

# Singleton instance
driver_sim = DriverSimulation()

