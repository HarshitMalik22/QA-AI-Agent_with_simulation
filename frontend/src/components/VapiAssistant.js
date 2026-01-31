import React, { useState, useEffect } from 'react';
import Vapi from '@vapi-ai/web';

const vapi = new Vapi(process.env.REACT_APP_VAPI_PUBLIC_KEY);

const VapiAssistant = ({ onTranscriptUpdate, onCallStateChange }) => {
    const [isSessionActive, setIsSessionActive] = useState(false);
    const [isSpeechActive, setIsSpeechActive] = useState(false);

    useEffect(() => {
        // Event Handlers
        const onCallStart = () => {
            setIsSessionActive(true);
            onCallStateChange && onCallStateChange('active');
        };

        const onCallEnd = () => {
            setIsSessionActive(false);
            onCallStateChange && onCallStateChange('inactive');
        };

        const onSpeechStart = () => setIsSpeechActive(true);
        const onSpeechEnd = () => setIsSpeechActive(false);

        const onMessage = (message) => {
            if (message.type === 'conversation-update') {
                const formattedTranscript = message.conversation
                    .filter(msg => msg.role !== 'system')
                    .map(msg => {
                        const roleLabel = msg.role === 'assistant' ? 'Agent' : 'Driver';
                        return `${roleLabel}: ${msg.content}`;
                    })
                    .join('\n');

                onTranscriptUpdate && onTranscriptUpdate(formattedTranscript);
            }
        };

        // Attach listeners
        vapi.on('call-start', onCallStart);
        vapi.on('call-end', onCallEnd);
        vapi.on('speech-start', onSpeechStart);
        vapi.on('speech-end', onSpeechEnd);
        vapi.on('message', onMessage);

        // Cleanup
        return () => {
            vapi.off('call-start', onCallStart);
            vapi.off('call-end', onCallEnd);
            vapi.off('speech-start', onSpeechStart);
            vapi.off('speech-end', onSpeechEnd);
            vapi.off('message', onMessage);
        };
    }, [onTranscriptUpdate, onCallStateChange]);

    const toggleCall = async () => {
        if (isSessionActive) {
            vapi.stop();
        } else {
            try {
                // Fetch dynamic configuration from backend
                const response = await fetch('http://localhost:8000/api/vapi/assistant', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: {
                            call: {
                                customer: {
                                    number: "+919876543210" // Default/Test number
                                }
                            }
                        }
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to fetch assistant config');
                }

                const data = await response.json();

                if (data.assistant) {
                    vapi.start(data.assistant);
                } else {
                    console.error("Invalid config received:", data);
                }

            } catch (error) {
                console.error("Error starting call:", error);
                alert("Failed to start call. Check console/backend.");
            }
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
