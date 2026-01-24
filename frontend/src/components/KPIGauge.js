import React from 'react';

const KPIGauge = ({ value, label, unit, type = 'neutral' }) => {
    // Simple color logic
    const getColor = () => {
        if (type === 'risk') {
            if (value === 'High') return '#EF4444';
            if (value === 'Medium') return '#F59E0B';
            return '#10B981';
        }
        // For numeric wait times
        if (parseFloat(value) < 5) return '#10B981';
        if (parseFloat(value) < 10) return '#F59E0B';
        return '#EF4444';
    };

    const color = getColor();

    return (
        <div className="kpi-item">
            <div className="relative inline-flex items-center justify-center">
                <svg className="w-24 h-24 transform -rotate-90">
                    <circle
                        cx="48"
                        cy="48"
                        r="40"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="transparent"
                        className="text-gray-200"
                        style={{ color: '#E2E8F0' }}
                    />
                    <circle
                        cx="48"
                        cy="48"
                        r="40"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="transparent"
                        strokeDasharray={251.2}
                        strokeDashoffset={251.2 - (251.2 * 0.75)} // Just a static filled amount for visual flair
                        style={{ color: color, transition: 'stroke-dashoffset 1s ease-in-out' }}
                    />
                </svg>
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center'
                }}>
                    <span className="kpi-value" style={{ color: color }}>
                        {value}
                    </span>
                    {unit && <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>{unit}</span>}
                </div>
            </div>
            <div className="kpi-label" style={{ marginTop: '0.5rem' }}>{label}</div>
        </div>
    );
};

export default KPIGauge;
