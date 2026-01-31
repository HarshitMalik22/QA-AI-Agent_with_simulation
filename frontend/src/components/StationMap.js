
import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css';
import 'leaflet-defaulticon-compatibility';
import L from 'leaflet';

// Custom Icons to make it look premium
// Driver Icon (Car or Person) - Violet
// Driver Icon (EV Rickshaw)
const driverIcon = new L.Icon({
    iconUrl: '/ev-marker.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [40, 40], // Slightly larger for the detailed icon
    iconAnchor: [20, 40],
    popupAnchor: [0, -40],
    shadowSize: [41, 41]
});

// Station Icons based on color
const getStationIcon = (color) => new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Component to fly to the driver's location when it changes
const RecenterMap = ({ location }) => {
    const map = useMap();
    const hasCentered = React.useRef(false);

    useEffect(() => {
        if (location && location.lat && location.lon && !hasCentered.current) {
            // Set view once when we get first valid location
            map.setView([location.lat, location.lon], 14, { animate: true });
            hasCentered.current = true;
        }
    }, [location, map]);
    return null;
};

const StationMap = ({ stations, driverLocation, recommendedStationId }) => {
    // Default center if no driver location (New Delhi)
    const center = driverLocation && driverLocation.lat
        ? [driverLocation.lat, driverLocation.lon]
        : [28.6139, 77.2090];

    // Find recommended station to draw path
    const recStation = stations.find(s => s.id === recommendedStationId);

    return (
        <div className="map-container" style={{ height: '400px', width: '100%', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
            <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                />

                {/* Driver Marker */}
                {driverLocation && driverLocation.lat && (
                    <Marker position={[driverLocation.lat, driverLocation.lon]} icon={driverIcon}>
                        <Popup>
                            <strong>You are here</strong><br />
                            Driver Tracking Active
                        </Popup>
                    </Marker>
                )}

                {/* Station Markers */}
                {stations.map(stn => {
                    const isRec = stn.id === recommendedStationId;
                    const load = stn.current_load / stn.capacity;

                    // Determine Color
                    let color = 'green';
                    if (load > 0.8) color = 'red';
                    else if (load > 0.5) color = 'orange';

                    // Highlight recommended
                    if (isRec) color = 'blue';

                    return (
                        <Marker
                            key={stn.id}
                            position={[stn.location.lat, stn.location.lon]}
                            icon={getStationIcon(color)}
                        >
                            <Popup>
                                <div style={{ textAlign: 'center' }}>
                                    <strong>{stn.name}</strong>
                                    <br />
                                    <div style={{ marginTop: '5px' }}>
                                        <span className={`risk-badge ${color === 'red' ? 'high' : color === 'orange' ? 'medium' : 'low'}`}
                                            style={{ display: 'inline-block', padding: '2px 6px', borderRadius: '4px', fontSize: '0.8rem', color: 'white', backgroundColor: color === 'blue' ? '#3B82F6' : color }}>
                                            {color === 'blue' ? 'Recommended' : `${Math.round(load * 100)}% Load`}
                                        </span>
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '4px' }}>
                                        Wait: ~{stn.avg_service_time} min
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    )
                })}

                {/* Path Line if recommended */}
                {driverLocation && driverLocation.lat && recStation && (
                    <Polyline
                        positions={[
                            [driverLocation.lat, driverLocation.lon],
                            [recStation.location.lat, recStation.location.lon]
                        ]}
                        color="#3B82F6"
                        dashArray="5, 10"
                        weight={3}
                        opacity={0.7}
                    />
                )}

                <RecenterMap location={driverLocation} />
            </MapContainer>
        </div>
    );
};

export default StationMap;
