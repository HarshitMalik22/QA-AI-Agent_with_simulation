import React, { useState, useEffect } from 'react';
import Vapi from '@vapi-ai/web';

const vapi = new Vapi(process.env.REACT_APP_VAPI_PUBLIC_KEY);

const VapiAssistant = ({ onTranscriptUpdate, onCallStateChange }) => {
    const [isSessionActive, setIsSessionActive] = useState(false);
    const [isSpeechActive, setIsSpeechActive] = useState(false);

    useEffect(() => {
        // Event Listeners
        vapi.on('call-start', () => {
            setIsSessionActive(true);
            onCallStateChange && onCallStateChange('active');
        });

        vapi.on('call-end', () => {
            setIsSessionActive(false);
            onCallStateChange && onCallStateChange('inactive');
        });

        vapi.on('speech-start', () => {
            setIsSpeechActive(true);
        });

        vapi.on('speech-end', () => {
            setIsSpeechActive(false);
        });

        vapi.on('message', (message) => {
            if (message.type === 'transcript' && message.transcriptType === 'final') {
                // Pass transcript back to parent for analysis
                onTranscriptUpdate && onTranscriptUpdate(message.transcript);
            }
        });

        return () => {
            // Cleanup? Vapi instance is global usually
        };
    }, [onTranscriptUpdate, onCallStateChange]);

    const toggleCall = () => {
        if (isSessionActive) {
            vapi.stop();
        } else {
            vapi.start({
                model: {
                    provider: "openai",
                    model: "gpt-3.5-turbo",
                    messages: [
                        {
                            role: "system",
                            content: `You are a helpful Support Agent for 'Battery Smart', India's largest battery swapping network for e-rickshaws.
                            
                            Context Data (Live Status - Delhi):
                            - Tilak Nagar (Stn A): OVERLOADED (9/10 rickshaws). Wait: 20 mins.
                            - Rajouri Garden (Stn B): FREE (2/12 rickshaws). Wait: 2 mins. (Only 3km from Tilak Nagar).
                            - Okhla Phase 3 (Stn C): MODERATE.
                            - Mayapuri (Stn D): MODERATE.
                            
                            Guidelines:
                            1. **LANGUAGE**: You must speak mixed **Hindi + English (Hinglish)**. Example: "Haanji sir, Tilak Nagar mein bahut bheed hai, aap Rajouri chale jao."
                            2. **GOAL**: Route drivers to *Rajouri Garden* if they are near Tilak Nagar because it is faster.
                            3. **TECHNICAL**: If they say "Battery Stuck" or "Lock issue", say: "Arre, jabardasti mat karo! Technician bhej raha hoon." (Don't force it, sending tech).
                            4. **EMPATHY**: Validating their "Range Anxiety" is critical.
                            
                            Be polite, use "Sir" or "Bhaiyya", and keep it natural.`
                        }
                    ]
                },
                voice: {
                    provider: "11labs",
                    voiceId: "burt"
                }
            });
        }
    };

    return (
        <button
            onClick={toggleCall}
            className={`btn ${isSessionActive ? 'btn-danger' : 'btn-success'}`}
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: isSessionActive ? '0 0 15px rgba(239, 68, 68, 0.4)' : 'none',
                transition: 'all 0.3s ease'
            }}
        >
            <span style={{ fontSize: '1.2rem' }}>
                {isSessionActive ? '⏹️' : '📞'}
            </span>
            {isSessionActive ? (
                <span>End Call {isSpeechActive && '(Speaking...)'}</span>
            ) : (
                <span>Start Voice Agent</span>
            )}
        </button>
    );
};

export default VapiAssistant;
