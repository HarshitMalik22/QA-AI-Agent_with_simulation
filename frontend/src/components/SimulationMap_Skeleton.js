import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css';
import 'leaflet-defaulticon-compatibility';
import L from 'leaflet';

// Icons
const stationIcon = (color) => new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const driverIcon = new L.Icon({
    iconUrl: '/ev-marker.png', // Ensure this exists in public/
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -10]
});

const SimulationMap = ({ timeSeries, currentHour, isPlaying }) => {
    const [agents, setAgents] = useState([]);

    // Config: Center on Delhi
    const center = [28.6139, 77.2090];

    // Get current state from timeSeries based on hour
    const currentState = timeSeries && timeSeries.find(s => s.hour === Math.floor(currentHour));

    // Ref for animation loop
    const requestRef = useRef();

    // Generate Random Drivers when hour changes significantly
    useEffect(() => {
        if (!currentState) return;

        // Spawn agents based on Station Load
        // Start from random points around the station and move towards it
        const newAgents = [];

        Object.entries(currentState.stations).forEach(([sid, stats]) => {
            // Find station location (we need station list, passing simulated map helps)
            // For now, we'll try to get location from the stats if available, or we just hardcode/pass stations prop
            // Assuming we passed 'stations' prop separately or enriched stats
        });

    }, [Math.floor(currentHour)]);

    // But wait, the timeSeries only has stats, not lat/lon.
    // We need the static station list to know WHERE they are.
    // Let's rely on parent to pass 'stations' with locations.

    return (
        <div style={{ height: '500px', width: '100%', borderRadius: '12px', overflow: 'hidden', zIndex: 0 }}>
            <MapContainer center={center} zoom={11} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
                />

                {/* We need to map stations. Let's assume we pass them or fetch them.
                    For this artifact, I will focus on the structure and ask to update parent first.
                 */}
            </MapContainer>
        </div>
    );
};

export default SimulationMap;
