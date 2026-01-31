import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

function Home() {
    const navigate = useNavigate();

    const handleDownloadExcel = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/logs/download`, {
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'interaction_logs.xlsx');
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error('Error downloading Excel:', error);
            alert('Failed to download logs. Ensure the backend is running.');
        }
    };

    return (
        <div className="Home">
            {/* Floating Navbar */}
            <nav className="floating-nav">
                <div className="nav-brand">
                    <div className="nav-logo"></div>
                    <span>BatteryGen8</span>
                </div>
                <div className="nav-links">
                    <span className="nav-link" onClick={() => navigate('/dashboard')}>Data</span>
                    <span className="nav-link" onClick={() => window.open('https://t.me/battery_raju_bot', '_blank')}>Bot</span>
                    <span className="nav-link" onClick={handleDownloadExcel}>Reports</span>
                </div>
                <div className="nav-credit">
                    1 Credit
                </div>
                <div style={{ width: 30, height: 30, borderRadius: '50%', background: '#fbbf24', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: 'black' }}>H</div>
            </nav>

            <header className="hero-section">
                <div className="hero-content">
                    <h1>AI Customer Support</h1>
                    <h1 className="hero-subheadline">
                        <span className="underline-red">without limits.</span>
                    </h1>

                    <div className="hero-actions">
                        <button className="btn-outline" onClick={handleDownloadExcel}>Download Reports</button>
                        <button className="btn-glow" onClick={() => navigate('/dashboard')}>
                            Get Started <span style={{ fontSize: '1.2rem' }}>→</span>
                        </button>
                        <div className="hand-drawn-arrow">
                            ⤹ trust me, it's an experience!
                        </div>
                    </div>
                </div>
            </header>

            {/* Tilted Cards Carousel */}
            <main className="features-carousel">

                {/* Card 1: Dashboard */}
                <div
                    className="tilted-card"
                    style={{ backgroundImage: "url('/assets/dashboard.png')" }}
                    onClick={() => navigate('/dashboard')}
                >
                    <div className="card-overlay">
                        <h3>Live Dashboard</h3>
                        <p>Real-time Digital Twin</p>
                    </div>
                </div>

                {/* Card 2: Voice Agent */}
                <div
                    className="tilted-card"
                    style={{ backgroundImage: "url('/assets/voice.png')" }}
                >
                    <div className="card-overlay">
                        <h3>Voice Agent</h3>
                        <p>Call Raju: +1 (786) 321-7290</p>
                    </div>
                </div>

                {/* Card 3: Bot (Center) */}
                <div
                    className="tilted-card"
                    style={{ backgroundImage: "url('/assets/bot.png')" }}
                    onClick={() => window.open('https://t.me/battery_raju_bot', '_blank')}
                >
                    <div className="card-overlay">
                        <h3>Telegram Bot</h3>
                        <p>Chat Support</p>
                    </div>
                </div>

                {/* Card 4: Excel */}
                <div
                    className="tilted-card"
                    style={{ backgroundImage: "url('/assets/excel.png')" }}
                    onClick={handleDownloadExcel}
                >
                    <div className="card-overlay">
                        <h3>Excel Reports</h3>
                        <p>Download Logs</p>
                    </div>
                </div>

                {/* Card 5: Extra */}
                <div
                    className="tilted-card card-bg-4"
                    onClick={() => navigate('/simulation')}
                >
                    <div className="card-overlay">
                        <h3>City Simulation</h3>
                        <p>What-If Analysis</p>
                    </div>
                </div>

            </main>

            <footer className="home-footer">
                Battery Smart AI
            </footer>
        </div>
    );
}

export default Home;
