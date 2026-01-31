import React from 'react';

const Scorecard = ({ qaResult }) => {
    if (!qaResult || !qaResult.scorecard) return null;

    const {
        total_score,
        greeting_score,
        authentication_score,
        solution_score,
        closing_score,
        sentiment_label
    } = qaResult.scorecard;

    const { supervisor_flag, reason } = qaResult;

    // Helper for progress bar color
    const getProgressColor = (score, max) => {
        const pct = (score / max) * 100;
        if (pct >= 80) return '#10B981'; // Emerald
        if (pct >= 50) return '#F59E0B'; // Amber
        return '#EF4444'; // Rose
    };

    return (
        <div className="card" style={{ marginBottom: '1.5rem', fontFamily: 'Inter, sans-serif' }}>
            <div className="analysis-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>QA Scorecard</h3>
                {supervisor_flag && (
                    <span style={{
                        background: '#FEF2F2',
                        color: '#DC2626',
                        padding: '0.25rem 0.75rem',
                        borderRadius: '999px',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        border: '1px solid #FECACA'
                    }}>
                        🚩 SUPERVISOR FLAG
                    </span>
                )}
            </div>

            <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>

                {/* Left: Overall Score Circle */}
                <div style={{ position: 'relative', width: '120px', height: '120px', flexShrink: 0 }}>
                    <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                        <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="#E5E7EB"
                            strokeWidth="3"
                        />
                        <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke={getProgressColor(total_score, 100)}
                            strokeWidth="3"
                            strokeDasharray={`${total_score}, 100`}
                            strokeLinecap="round"
                        />
                    </svg>
                    <div style={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        textAlign: 'center'
                    }}>
                        <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>{total_score}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>OVERALL</div>
                    </div>
                </div>

                {/* Right: Section Breakdown */}
                <div style={{ flex: 1 }}>
                    <div className="score-row" style={{ marginBottom: '0.75rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.9rem', color: '#1F2937' }}>
                            <span>Authentication (Critical)</span>
                            <span style={{ fontWeight: 600 }}>{authentication_score}/30</span>
                        </div>
                        <div style={{ height: '8px', background: '#F3F4F6', borderRadius: '4px', overflow: 'hidden' }}>
                            <div style={{
                                height: '100%',
                                width: `${(authentication_score / 30) * 100}%`,
                                background: getProgressColor(authentication_score, 30),
                                transition: 'width 1s ease'
                            }} />
                        </div>
                    </div>

                    <div className="score-row" style={{ marginBottom: '0.75rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.9rem', color: '#1F2937' }}>
                            <span>Solution Correctness</span>
                            <span style={{ fontWeight: 600 }}>{solution_score}/40</span>
                        </div>
                        <div style={{ height: '8px', background: '#F3F4F6', borderRadius: '4px', overflow: 'hidden' }}>
                            <div style={{
                                height: '100%',
                                width: `${(solution_score / 40) * 100}%`,
                                background: getProgressColor(solution_score, 40),
                                transition: 'width 1s ease'
                            }} />
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.8rem', color: '#4B5563' }}>
                                <span>Greeting</span>
                                <span>{greeting_score}/10</span>
                            </div>
                            <div style={{ height: '6px', background: '#F3F4F6', borderRadius: '3px', overflow: 'hidden' }}>
                                <div style={{ height: '100%', width: `${(greeting_score / 10) * 100}%`, background: getProgressColor(greeting_score, 10) }} />
                            </div>
                        </div>
                        <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.8rem', color: '#4B5563' }}>
                                <span>Closing</span>
                                <span>{closing_score}/20</span>
                            </div>
                            <div style={{ height: '6px', background: '#F3F4F6', borderRadius: '3px', overflow: 'hidden' }}>
                                <div style={{ height: '100%', width: `${(closing_score / 20) * 100}%`, background: getProgressColor(closing_score, 20) }} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Root Cause / Sentiment Footer */}
            <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #F3F4F6', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <span style={{ marginRight: '1rem' }}>
                    🧠 <b>Root Cause:</b> {reason}
                </span>
                <span>
                    mood: <b style={{
                        color: sentiment_label === 'Positive' ? '#10B981' : sentiment_label === 'Negative' ? '#EF4444' : '#6B7280'
                    }}>{sentiment_label}</b>
                </span>
            </div>
        </div>
    );
};

export default Scorecard;
