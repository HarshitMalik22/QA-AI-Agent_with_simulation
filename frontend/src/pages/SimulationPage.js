import React, { useState } from 'react';
import './SimulationPage.css';
import SimulationMap from '../components/SimulationMap';

const SimulationPage = () => {
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [stations, setStations] = useState([]); // Store stations for map

    // Playback State
    const [currentHour, setCurrentHour] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);

    const [config, setConfig] = useState({
        demandSurge: false,
        addStation: false,
        addChargers: false
    });

    const runSimulation = async () => {
        setLoading(true);
        setResults(null);

        // Build Interventions based on Config
        const interventions = [];

        if (config.demandSurge) {
            interventions.push({
                type: "shift_demand",
                factor: 1.5,
                window: [8, 22]
            });
        }

        if (config.addStation) {
            interventions.push({
                type: "add_station",
                data: {
                    id: "BS-NEW-01",
                    name: "New Station (Rajouri Garden)",
                    total_slots: 20,
                    chargers: 15,
                    initial_inventory: 15,
                    location: { lat: 28.64, lon: 77.12 }
                }
            });
        }

        if (config.addChargers) {
            interventions.push({
                type: "modify_chargers",
                station_id: "BS-001",
                count: 25 // Upgrade from default (e.g. 12) to 25
            });
        }

        try {
            const response = await fetch('http://localhost:8000/api/simulation/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ interventions })
            });
            const data = await response.json();
            setResults(data);
        } catch (error) {
            console.error("Simulation failed:", error);
            alert("Simulation failed to run. Check backend.");
        } finally {
            setLoading(false);
        }
    };

    // Load static stations initially (for map)
    React.useEffect(() => {
        fetch('http://localhost:8000/api/stations')
            .then(res => res.json())
            .then(data => setStations(data.stations));
    }, []);

    // Playback Loop
    React.useEffect(() => {
        let interval;
        if (isPlaying && results && results.time_series) {
            interval = setInterval(() => {
                setCurrentHour(prev => {
                    const next = prev + 0.5; // speed multiplier
                    if (next >= 24) {
                        setIsPlaying(false);
                        return 23;
                    }
                    return next;
                });
            }, 500); // Update every 500ms
        }
        return () => clearInterval(interval);
    }, [isPlaying, results]);

    const togglePlay = () => {
        if (!results) return;
        if (currentHour >= 23) setCurrentHour(0);
        setIsPlaying(!isPlaying);
    };

    return (
        <div className="simulation-container">
            <h1 className="page-title">City Digital Twin Simulation</h1>
            <p className="page-subtitle">Run "What-If" scenarios to optimize the network.</p>

            <div className="layout-grid">
                {/* Controls Panel */}
                <div className="controls-panel">
                    <h2 className="section-title">Scenario Configuration</h2>

                    <div className="control-group">
                        <label className="control-item">
                            <input
                                type="checkbox"
                                checked={config.demandSurge}
                                onChange={(e) => setConfig({ ...config, demandSurge: e.target.checked })}
                            />
                            <div>
                                <span className="control-label-main">Festival Surge</span>
                                <span className="control-label-sub">Increase demand by 50% (8AM - 10PM)</span>
                            </div>
                        </label>

                        <label className="control-item">
                            <input
                                type="checkbox"
                                checked={config.addStation}
                                onChange={(e) => setConfig({ ...config, addStation: e.target.checked })}
                            />
                            <div>
                                <span className="control-label-main">Add New Station</span>
                                <span className="control-label-sub">Deploy pop-up station in Rajouri Garden</span>
                            </div>
                        </label>

                        <label className="control-item">
                            <input
                                type="checkbox"
                                checked={config.addChargers}
                                onChange={(e) => setConfig({ ...config, addChargers: e.target.checked })}
                            />
                            <div>
                                <span className="control-label-main">Upgrade Infrastructure</span>
                                <span className="control-label-sub">Add 12 Fast Chargers to busiest hub</span>
                            </div>
                        </label>
                    </div>

                    <button
                        onClick={runSimulation}
                        disabled={loading}
                        className="run-button"
                    >
                        {loading ? 'Simulating 24 Hours...' : 'Run Simulation'}
                    </button>

                    <button
                        onClick={() => window.location.href = "/"}
                        className="back-button"
                    >
                        ← Back to Dashboard
                    </button>
                </div>

                {/* Results Panel */}
                <div className="results-panel">
                    {!results && !loading && (
                        <div className="empty-state">
                            <div className="empty-icon">🏙️</div>
                            <p>Select scenarios and run the simulation to see results.</p>
                        </div>
                    )}

                    {loading && (
                        <div className="loading-state">
                            <div className="spinner"></div>
                            <p style={{ color: '#4f46e5', fontWeight: 600 }}>Consulting Digital Twin...</p>
                        </div>
                    )}

                    {results && (
                        <div className="results-content animate-fade-in">

                            {/* Visual Map Playback */}
                            <div style={{ marginBottom: '2rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                    <h3 style={{ fontSize: '1.2rem', fontWeight: 600 }}>Live Network Visualization</h3>
                                    <button
                                        onClick={togglePlay}
                                        style={{
                                            padding: '0.5rem 1rem',
                                            background: isPlaying ? '#e11d48' : '#4f46e5',
                                            color: 'white',
                                            borderRadius: '6px',
                                            border: 'none',
                                            cursor: 'pointer',
                                            fontWeight: 600
                                        }}
                                    >
                                        {isPlaying ? '⏸ Pause' : '▶ Play 24h Timelapse'}
                                    </button>
                                </div>
                                <SimulationMap
                                    stations={stations}
                                    timeSeries={results.time_series}
                                    currentHour={currentHour}
                                    isPlaying={isPlaying}
                                />
                            </div>

                            {/* KPI Grid */}
                            <div className="kpi-grid">
                                <MetricCard
                                    label="Total Swaps"
                                    value={results.total_swaps}
                                    subtext="Successful operations"
                                    color="emerald"
                                />
                                <MetricCard
                                    label="Lost Swaps"
                                    value={results.lost_swaps}
                                    subtext="Due to congestion/inventory"
                                    color="rose"
                                    alert={results.total_swaps > 0 && (results.lost_swaps / results.total_swaps > 0.1)}
                                />
                                <MetricCard
                                    label="Avg Wait Time"
                                    value={`${results.avg_wait_time}m`}
                                    subtext="Per driver"
                                    color="amber"
                                />
                                <MetricCard
                                    label="Network Load"
                                    value={`${Math.round(Object.values(results.stations).reduce((acc, s) => acc + s.charger_utilization_pct, 0) / Object.keys(results.stations).length)}%`}
                                    subtext="Avg Charger Utilization"
                                    color="blue"
                                />
                            </div>

                            {/* Station Table */}
                            <div className="results-table-container">
                                <div className="table-header">
                                    <h3>Station Performance Breakdown</h3>
                                </div>
                                <div className="table-wrapper">
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>Station ID</th>
                                                <th className="text-right">Swaps</th>
                                                <th className="text-right text-rose">Lost</th>
                                                <th className="text-right">Wait (min)</th>
                                                <th className="text-right">Util (%)</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {Object.entries(results.stations).map(([id, stats]) => (
                                                <tr key={id}>
                                                    <td style={{ fontWeight: 500, color: '#312e81' }}>{id}</td>
                                                    <td className="text-right">{stats.swaps}</td>
                                                    <td className={`text-right font-bold ${stats.lost_swaps > 10 ? 'text-rose' : 'text-slate-400'}`}>
                                                        {stats.lost_swaps}
                                                    </td>
                                                    <td className={`text-right ${stats.avg_wait_time_min > 15 ? 'text-amber font-bold' : ''}`}>
                                                        {stats.avg_wait_time_min}
                                                    </td>
                                                    <td className="text-right">
                                                        <span style={{ marginRight: '0.5rem' }}>{stats.charger_utilization_pct}%</span>
                                                        <div className="progress-bar-bg">
                                                            <div
                                                                className={`progress-bar-fill ${stats.charger_utilization_pct > 80 ? 'bg-rose' : 'bg-emerald'}`}
                                                                style={{ width: `${stats.charger_utilization_pct}%` }}
                                                            ></div>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// UI Helper
const MetricCard = ({ label, value, subtext, color, alert }) => (
    <div className={`metric-card ${alert ? 'alert' : ''}`}>
        <div className="metric-label">{label}</div>
        <div className={`metric-value text-${color}`}>{value}</div>
        <div className="metric-sub">{subtext}</div>
    </div>
);

export default SimulationPage;
