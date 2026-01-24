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

    const toggleCall = () => {
        if (isSessionActive) {
            vapi.stop();
        } else {
            vapi.start({
                transcriber: {
                    provider: "deepgram",
                    model: "nova-2",
                    language: "hi"
                },
                model: {
                    provider: "openai",
                    model: "gpt-4o",
                    messages: [
                        {
                            role: "system",
                            content: `You are a helpful Support Agent for 'Battery Smart', India's largest battery swapping network for e-rickshaws.
                            
                            **Data Context (Live)**:
                            - **Tilak Nagar (Stn A)**: OVERLOADED (Waittime: 20 mins).
                            - **Rajouri Garden (Stn B)**: FREE (Waittime: 2 mins). Distance: 3km from Tilak Nagar.
                            
                            **Agent Guidelines**:
                            1. **Language & Tone**: Speak natural **Hinglish** (Hindi + English mix).
                               - *Strict Rule*: Do NOT use complex English words. Use simple phonetic Hindi.
                               - *Bad*: "It will take output", "Surf 3 kilometers".
                               - *Good*: "Sir, wahan mat jao", "Sirf 3 kilometer door hai".
                            
                            2. **Scenarios & Actions**:
                               - **High Wait Time / Traffic**: IF driver is at Tilak Nagar OR complains about waiting, SUGGEST Rajouri Garden.
                                 *Example*: "Sir, Tilak Nagar mein 20 min ki waiting hai. Aap Rajouri chale jao, wahan sirf 2 min lagenge."
                               
                               - **Battery/Lock Issue**: IF driver says "Battery stuck" or "Lock nahi khul raha", ADVISE against force and promise a technician.
                                 *Example*: "Zor mat lagaiye sir, lock kharab ho jayega. Main technician bhej raha hoon."
                               
                               - **Payment/Balance**: IF driver asks about balance, say "Check kar raha hoon... Sir, minimum balance maintain rakhna zaroori hai."
                               
                               - **General**: If they just say "Hello" or "Namaste", greet them back warmly in Hinglish. "Namaste sir, kahiye kya seva karoon?"

                            3. **Constraint**: Keep responses short and conversational. Do NOT hallucinate words.`
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
