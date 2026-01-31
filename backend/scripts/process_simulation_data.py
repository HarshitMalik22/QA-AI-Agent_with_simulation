
import pandas as pd
import json
import os
import dateutil.parser

def process_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    battery_logs_path = os.path.join(data_dir, "BatteryLogs.xlsx - result.csv")
    charging_events_path = os.path.join(data_dir, "ChargingEvents.xlsx - result.csv")
    output_path = os.path.join(data_dir, "simulation_config.json")
    
    print("Processing Real Data for Simulation...")
    
    config = {
        "demand_curve_hourly": [0.05] * 24, # Default fallback
        "avg_charge_time_minutes": 60,
        "total_swaps_analyzed": 0
    }
    
    # 1. Process Demand Curve from BatteryLogs
    try:
        print(f"Reading {battery_logs_path}...")
        df_swaps = pd.read_csv(battery_logs_path)
        
        # Parse dates
        # Assuming 'createdAt' is the swap time
        df_swaps['dt'] = pd.to_datetime(df_swaps['createdAt'], errors='coerce')
        df_swaps = df_swaps.dropna(subset=['dt'])
        
        # Extract hour (0-23)
        df_swaps['hour'] = df_swaps['dt'].dt.hour
        
        # Count swaps per hour
        hourly_counts = df_swaps['hour'].value_counts().sort_index()
        
        # Normalize to probability (0.0 to 1.0 scale relative to max peak)
        # But for our sim, we need "Probability of arrival per minute"
        # Let's verify total volume. 
        # If max hourly swaps is 1000 across network, and we have 50 stations, 
        # that's 20 swaps/station/hour = 0.33 swaps/min.
        # Let's normalize to a profile shape (0-1) and let sim scale it by base rate.
        
        if not hourly_counts.empty:
            max_val = hourly_counts.max()
            profile = []
            for h in range(24):
                count = hourly_counts.get(h, 0)
                # Normalize: 1.0 = Peak Hour
                profile.append(round(count / max_val, 3) if max_val > 0 else 0)
            
            config["demand_curve_hourly"] = profile
            config["total_swaps_analyzed"] = int(len(df_swaps))
            print("Successfully generated Demand Curve.")
            
    except Exception as e:
        print(f"Error processing BatteryLogs: {e}")

    # 2. Process Charge Time from ChargingEvents
    try:
        print(f"Reading {charging_events_path}...")
        df_charge = pd.read_csv(charging_events_path)
        
        # We need duration.
        # columns: date,deviceId,ts,lat,lon,soc,discharging_time,charge_start_time
        # 'discharging_time' seems to be a timestamp? Or duration?
        # Let's look at sample: 
        # charge_start_time: 2026-01-30 00:05:10
        # discharging_time: 2026-01-30 09:00:10 
        # This implies 'discharging_time' might be 'charge_end_time' or similar in this CSV context?
        # Let's assume (discharging_time - charge_start_time) = duration
        
        df_charge['start'] = pd.to_datetime(df_charge['charge_start_time'], errors='coerce')
        df_charge['end'] = pd.to_datetime(df_charge['discharging_time'], errors='coerce')
        
        df_charge = df_charge.dropna(subset=['start', 'end'])
        
        # Calculate duration in minutes
        df_charge['duration_min'] = (df_charge['end'] - df_charge['start']).dt.total_seconds() / 60
        
        # Filter realistic values (e.g. 10 min to 300 min) to remove outliers/bugs
        valid_charges = df_charge[
            (df_charge['duration_min'] > 10) & 
            (df_charge['duration_min'] < 300)
        ]
        
        if not valid_charges.empty:
            avg_time = valid_charges['duration_min'].mean()
            config["avg_charge_time_minutes"] = int(avg_time)
            print(f"Calculated Avg Charge Time: {int(avg_time)} minutes")
            
    except Exception as e:
        print(f"Error processing ChargingEvents: {e}")

    # 3. Save
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Saved configuration to {output_path}")

if __name__ == "__main__":
    process_data()
