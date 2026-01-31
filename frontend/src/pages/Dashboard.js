import React, { useState, useEffect } from 'react';
import '../App.css';
import axios from 'axios';

// Components
import PipelineFlow from '../components/PipelineFlow';
import StationMap from '../components/StationMap';
import KPIGauge from '../components/KPIGauge';
import AICoach from '../components/AICoach';
import VapiAssistant from '../components/VapiAssistant';

const API_BASE_URL = 'http://localhost:8000';

function Dashboard() {
    const [transcript, setTranscript] = useState('');
    const [callId, setCallId] = useState('');
    const [driverLocation, setDriverLocation] = useState({ lat: '', lon: '' });
    const [analysis, setAnalysis] = useState(null);
    const [loading, setLoading] = useState(false);
    const [currentPipelineStep, setCurrentPipelineStep] = useState('input');
    const [error, setError] = useState(null);
    const [sampleTranscripts, setSampleTranscripts] = useState([]);
    const [stations, setStations] = useState([]);

    // Speech Recognition Setup
    // Handled by VapiAssistant component

    useEffect(() => {
        // Load sample transcripts and stations
        const fetchData = async () => {
            try {
                const [transcriptsRes, stationsRes] = await Promise.all([
                    axios.get(`${API_BASE_URL}/api/transcripts`),
                    axios.get(`${API_BASE_URL}/api/stations`)
                ]);
                setSampleTranscripts(transcriptsRes.data.transcripts || []);
                setStations(stationsRes.data.stations || []);
            } catch (err) {
                console.error('Error loading initial data:', err);
            }
        };
        fetchData();
    }, []);

    // Poll for Vapi Phone Call Updates
    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                const res = await axios.get(`${API_BASE_URL}/api/analysis/latest`);
                if (res.data && res.data.call_id) {
                    setAnalysis(prev => {
                        if (!prev || prev.call_id !== res.data.call_id) {
                            console.log("New Analysis Detected:", res.data);
                            setCallId(res.data.call_id);
                            if (res.data.transcript) {
                                setTranscript(res.data.transcript);
                            }
                            setLoading(false);
                            setCurrentPipelineStep('complete');
                            return res.data;
                        }
                        return prev;
                    });
                }
            } catch (err) {
                // Silent fail on poll
            }
        }, 2000);
        return () => clearInterval(interval);
    }, []);

    // Poll for Live Driver Simulation
    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                const res = await axios.get(`${API_BASE_URL}/api/simulation/live`);
                if (res.data) {
                    setDriverLocation(prev => ({
                        ...prev, // Keep other props if any
                        lat: res.data.lat,
                        lon: res.data.lon
                    }));
                }
            } catch (err) {
                // console.error("Simulation poll failed", err);
            }
        }, 1000); // 1 update per second
        return () => clearInterval(interval);
    }, []);

    const loadSample = (sample) => {
        setTranscript(sample.transcript);
        setCallId(sample.call_id);
        setAnalysis(null);
        setCurrentPipelineStep('input');
        if (sample.driver_location) {
            setDriverLocation({
                lat: sample.driver_location.lat.toString(),
                lon: sample.driver_location.lon.toString()
            });
        }
    };

    const handleAnalyze = async () => {
        if (!transcript.trim()) {
            setError('Please provide a transcript');
            return;
        }

        setLoading(true);
        setError(null);
        setAnalysis(null);

        // Simulate pipeline animation
        const steps = ['input', 'qa', 'decision', 'twin', 'compare', 'insight', 'complete'];
        let stepIndex = 0;

        // Start animation loop
        const interval = setInterval(() => {
            if (stepIndex < steps.length - 1) {
                stepIndex++;
                setCurrentPipelineStep(steps[stepIndex]);
            }
        }, 800);

        try {
            const payload = {
                transcript: transcript.trim(),
                call_id: callId.trim() || 'custom',
                driver_location: driverLocation.lat ? {
                    lat: parseFloat(driverLocation.lat),
                    lon: parseFloat(driverLocation.lon)
                } : null
            };

            const response = await axios.post(`${API_BASE_URL}/api/analyze`, payload);

            // Wait for at least the animation time
            setTimeout(() => {
                clearInterval(interval);
                setCurrentPipelineStep('complete');
                setAnalysis(response.data);
                setLoading(false);
            }, 4000);

        } catch (err) {
            clearInterval(interval);
            setError('Analysis failed. Please check backend connection.');
            setLoading(false);
            setCurrentPipelineStep('input');
        }
    };

    return (
        <div className="Dashboard">
            <header className="App-header">
                <h1>QA-Driven Digital Twin</h1>
                <p>Counterfactual Decision Intelligence for Customer Support</p>
            </header>

            <PipelineFlow currentStep={currentPipelineStep} />

            <main className="dashboard-grid">
                {/* Left Column: Input & Controls */}
                <section className="input-section">
                    <div className="card">
                        <h3 style={{ marginTop: 0, marginBottom: '1rem', color: 'var(--text-secondary)' }}>Input Call Data</h3>

                        <div className="sample-pills">
                            {sampleTranscripts.map((sample, idx) => (
                                <div
                                    key={idx}
                                    className={`pill ${callId === sample.call_id ? 'active' : ''}`}
                                    onClick={() => loadSample(sample)}
                                >
                                    Call #{sample.call_id}
                                </div>
                            ))}
                        </div>

                        <div className="form-group" style={{ position: 'relative' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                <label style={{ marginBottom: 0 }}>Live Transcript</label>
                                <VapiAssistant
                                    onTranscriptUpdate={(text) => setTranscript(text)}
                                    onCallStateChange={(state) => {
                                        if (state === 'active') setTranscript(''); // Clear on start
                                    }}
                                />
                            </div>
                            <textarea
                                value={transcript}
                                onChange={(e) => setTranscript(e.target.value)}
                                placeholder="Start the Voice Agent to converse..."
                                rows="8"
                                style={{
                                    borderColor: '#E2E8F0',
                                    boxShadow: 'none'
                                }}
                            />
                        </div>

                        <button
                            className="btn btn-primary"
                            style={{ width: '100%' }}
                            onClick={handleAnalyze}
                            disabled={loading}
                        >
                            {loading ? 'Running Simulation...' : 'Run Simulation & Analysis'}
                        </button>

                        {error && <div style={{ color: 'var(--danger)', marginTop: '1rem' }}>{error}</div>}
                    </div>
                </section>

                {/* Right Column: Visualization & Results */}
                <section className="results-section">
                    {!analysis ? (
                        // Placeholder for Analysis Results Only
                        <div className="card glass-card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-tertiary)' }}>
                            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🤖</div>
                            <h3>Waiting for Call...</h3>
                            <p>Simulate a call to see counterfactual analysis here.</p>
                        </div>
                    ) : (
                        <>
                            {/* Live Map - Visible only after analysis */}
                            <div className="card" style={{ marginBottom: '1.5rem' }}>
                                <h4 style={{ marginTop: 0, color: 'var(--text-secondary)' }}>Live Network Map (Real-Time)</h4>
                                <StationMap
                                    stations={stations}
                                    driverLocation={driverLocation.lat ? {
                                        lat: parseFloat(driverLocation.lat),
                                        lon: parseFloat(driverLocation.lon)
                                    } : null}
                                    recommendedStationId={analysis?.insights?.recommendation?.includes('Station') ?
                                        analysis.insights.recommendation.split('Station ')[1] : null}
                                />
                            </div>

                            {/* KPIs */}
                            <div className="card" style={{ marginBottom: '1.5rem' }}>
                                <h4 style={{ marginTop: 0, color: 'var(--text-secondary)' }}>Impact Simulation</h4>
                                <div className="kpi-container">
                                    <KPIGauge
                                        value={analysis.alternatives.find(a => !a.is_actual)?.expected_wait_time || '0'}
                                        label={analysis.actual_decision?.decision_type === 'technical_safety' ? 'Technician ETA' : 'Exp. Wait'}
                                        unit="min"
                                        type="time"
                                    />
                                    <KPIGauge
                                        value={analysis.alternatives.find(a => !a.is_actual)?.congestion_risk || 'Low'}
                                        label={analysis.actual_decision?.decision_type === 'technical_safety' ? 'Safety Risk' : 'Congestion'}
                                        type="risk"
                                    />
                                </div>
                            </div>

                            {/* Middle Row: Comparison Table */}
                            <div className="card" style={{ marginBottom: '1.5rem' }}>
                                <div className="analysis-header">
                                    <h3 style={{ margin: 0 }}>Counterfactual Analysis</h3>
                                    <div className={`risk-badge ${analysis.qa_result.issue_detected ? 'high' : 'low'}`}>
                                        {analysis.qa_result.issue_detected ? 'Optimization Opportunity' : 'Optimal Decision'}
                                    </div>
                                </div>

                                <div className="table-container">
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>Scenario</th>
                                                <th>Context</th>
                                                <th>Wait Time</th>
                                                <th>Congestion</th>
                                                <th>Repeat Risk</th>
                                                <th>Impact</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {analysis.alternatives.map((alt, idx) => (
                                                <tr key={idx} className={alt.is_actual ? 'actual-row' : ''}>
                                                    <td>
                                                        <div style={{ fontWeight: 600 }}>
                                                            {alt.is_actual ? 'Original Decision' : 'Simulation'}
                                                        </div>
                                                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                                            {alt.option}
                                                        </div>
                                                    </td>
                                                    <td style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                                                        {alt.description}
                                                    </td>
                                                    <td>{alt.expected_wait_time} min</td>
                                                    <td>
                                                        <span className={`risk-badge ${alt.congestion_risk.toLowerCase()}`}>
                                                            {alt.congestion_risk}
                                                        </span>
                                                    </td>
                                                    <td>{alt.repeat_call_risk}</td>
                                                    <td>
                                                        {alt.improvement?.wait_time_reduction_pct > 0 && (
                                                            <span style={{ color: 'var(--success)', fontWeight: 600 }}>
                                                                ↓ {alt.improvement.wait_time_reduction_pct}% wait
                                                            </span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Bottom Row: AI Coach */}
                            <AICoach
                                message={analysis.insights.recommendation + ". " + analysis.insights.impact_summary}
                            />
                        </>
                    )}
                </section>
            </main>
        </div>
    );
}

export default Dashboard;
