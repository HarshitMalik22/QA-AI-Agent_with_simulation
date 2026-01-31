import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css';
import 'leaflet-defaulticon-compatibility';
import L from 'leaflet';

// Icons
const getStationIcon = (color) => new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Helper to generate random offset
const randomOffset = (val) => val + (Math.random() - 0.5) * 0.05;

const SimulationMap = ({ stations, timeSeries, currentHour, isPlaying }) => {
    // Agents: { id, lat, lon, targetLat, targetLon, progress }
    const [agents, setAgents] = useState([]);
    const [mapState, setMapState] = useState({}); // Station states by ID

    // 1. Update Map State based on Time
    useEffect(() => {
        if (!timeSeries || !stations) return;

        const hourIdx = Math.floor(currentHour);
        const snapshot = timeSeries.find(s => s.hour === hourIdx);

        if (snapshot) {
            setMapState(snapshot.stations);

            // Spawn Agents Logic:
            // If a station has > 5 queue, spawn incoming drivers
            const newAgents = [];
            stations.forEach(st => {
                const stState = snapshot.stations[st.id];
                if (stState && stState.queue > 0) {
                    // Spawn N agents where N = queue size / 2 (visual scaling)
                    const count = Math.min(stState.queue, 10); // Cap at 10 per station for perf

                    for (let i = 0; i < count; i++) {
                        newAgents.push({
                            id: `${st.id}-${i}-${hourIdx}`,
                            lat: randomOffset(st.location.lat),
                            lon: randomOffset(st.location.lon),
                            targetLat: st.location.lat,
                            targetLon: st.location.lon,
                            speed: 0.002 + Math.random() * 0.002
                        });
                    }
                }
            });
            setAgents(newAgents);
        }
    }, [currentHour, timeSeries, stations]);

    // 2. Animation Loop (Visual Interpolation)
    // We update agents positions every frame to make them move towards targets
    // BUT React state updates might be too slow for 60fps.
    // For this prototype, we'll just render them at fixed positions or rely on CSS transitions if possible.
    // Given the constraints, let's just render the "Snapshot" agents. 
    // Moving them smoothly requires requestAnimationFrame interacting with Leaflet refs.
    // Simplify: Just render the agents at random positions "approaching" the station.

    return (
        <div style={{ height: '500px', width: '100%', borderRadius: '12px', overflow: 'hidden', zIndex: 0, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
            <MapContainer center={[28.6139, 77.2090]} zoom={11} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
                />

                {stations && stations.map(st => {
                    const stState = mapState[st.id] || { queue: 0, load: 0 };

                    // Color Logic
                    let color = 'green';
                    if (stState.queue > 5) color = 'orange';
                    if (stState.queue > 10) color = 'red';

                    return (
                        <Marker
                            key={st.id}
                            position={[st.location.lat, st.location.lon]}
                            icon={getStationIcon(color)}
                        >
                            <Popup>
                                <strong>{st.name}</strong><br />
                                Queue: {stState.queue}<br />
                                Lost: {stState.load}
                            </Popup>
                        </Marker>
                    );
                })}

                {/* Render Agents (Visual Traffic) */}
                {agents.map(agent => (
                    <CircleMarker
                        key={agent.id}
                        center={[agent.lat, agent.lon]}
                        radius={3}
                        pathOptions={{ color: '#818cf8', fillColor: '#818cf8', fillOpacity: 0.8 }}
                    />
                ))}

            </MapContainer>

            {/* HUD Overlay */}
            <div style={{ position: 'absolute', top: 20, right: 20, zIndex: 999, background: 'rgba(0,0,0,0.7)', color: 'white', padding: '10px 20px', borderRadius: '8px', backdropFilter: 'blur(4px)' }}>
                <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px', color: '#94a3b8' }}>Simulation Time</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                    {String(Math.floor(currentHour)).padStart(2, '0')}:00
                </div>
            </div>
        </div>
    );
};

export default SimulationMap;
