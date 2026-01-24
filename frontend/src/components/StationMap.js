import React from 'react';

const StationMap = ({ stations, driverLocation, recommendedStationId }) => {
    // Normalize coordinates for display on a 100x100 grid
    // This is a simplified projection for the demo

    // Find bounds
    // Find bounds

    // Mock positions for visual demo if real lat/lon is too close
    const mapPositions = {
        'A': { x: 50, y: 50 },     // Central
        'B': { x: 20, y: 30 },     // Top Left
        'C': { x: 80, y: 70 },     // Bottom Right
        'D': { x: 30, y: 80 },     // Bottom Left
        'driver': { x: 45, y: 45 } // Default driver pos
    };

    // If we have actual station data, use it, otherwise fallback
    const getStationPos = (id) => mapPositions[id] || { x: 50, y: 50 };

    return (
        <div className="map-container">
            <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
                {/* Grid Lines */}
                <defs>
                    <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                        <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#E2E8F0" strokeWidth="0.5" />
                    </pattern>
                </defs>
                <rect width="100" height="100" fill="url(#grid)" />

                {/* Stations */}
                {stations.map(station => {
                    const pos = getStationPos(station.id);
                    const isRec = station.id === recommendedStationId;
                    const loadColor = station.current_load / station.capacity > 0.8 ? '#EF4444' :
                        station.current_load / station.capacity > 0.5 ? '#F59E0B' : '#10B981';

                    return (
                        <g key={station.id} transform={`translate(${pos.x}, ${pos.y})`}>
                            {/* Connection Line to Driver */}
                            {driverLocation && (
                                <line
                                    x1="0" y1="0"
                                    x2={mapPositions.driver.x - pos.x}
                                    y2={mapPositions.driver.y - pos.y}
                                    stroke={isRec ? '#3B82F6' : '#CBD5E1'}
                                    strokeWidth={isRec ? "0.5" : "0.2"}
                                    strokeDasharray={isRec ? "0" : "2,1"}
                                />
                            )}

                            {/* Station Dot */}
                            <circle
                                r="4"
                                fill="white"
                                stroke={isRec ? '#3B82F6' : loadColor}
                                strokeWidth={isRec ? "0.8" : "0.5"}
                                className={isRec ? 'animate-pulse' : ''}
                            />

                            {/* Station Label */}
                            <text y="7" fontSize="3" textAnchor="middle" fill="#64748B" fontWeight="600">
                                Stn {station.id}
                            </text>

                            {/* Load Indicator */}
                            <text y="-5" fontSize="2.5" textAnchor="middle" fill={loadColor}>
                                {Math.round((station.current_load / station.capacity) * 100)}%
                            </text>
                        </g>
                    );
                })}

                {/* Driver */}
                <g transform={`translate(${mapPositions.driver.x}, ${mapPositions.driver.y})`}>
                    <circle r="3" fill="#1A1F2C" stroke="white" strokeWidth="0.5" />
                    <text y="6" fontSize="3" textAnchor="middle" fill="#1A1F2C" fontWeight="700">You</text>
                </g>
            </svg>

            {/* Legend Overlay */}
            <div style={{ position: 'absolute', bottom: 10, right: 10, background: 'rgba(255,255,255,0.8)', padding: 5, borderRadius: 5, fontSize: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 2 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#EF4444', marginRight: 4 }}></span> High Load
                </div>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#10B981', marginRight: 4 }}></span> Low Load
                </div>
            </div>
        </div>
    );
};

export default StationMap;
