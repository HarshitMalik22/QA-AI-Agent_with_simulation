import React, { useState, useEffect } from 'react';

const AICoach = ({ message }) => {
    const [displayedText, setDisplayedText] = useState('');

    useEffect(() => {
        setDisplayedText('');
        let i = 0;

        // Typing animation
        const intervalId = setInterval(() => {
            setDisplayedText((prev) => {
                if (i >= message.length) {
                    clearInterval(intervalId);
                    return prev;
                }
                i++;
                return message.slice(0, i);
            });
        }, 20);

        // Text-to-Speech Logic
        if (message) {
            const utterance = new SpeechSynthesisUtterance(message);
            utterance.rate = 1.1;
            utterance.pitch = 1.0;

            // Try to find a good English voice
            const voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(v => v.name.includes('Google US English') || v.name.includes('Samantha'));
            if (preferredVoice) utterance.voice = preferredVoice;

            // Cancel any previous speech
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utterance);
        }

        return () => {
            clearInterval(intervalId);
            window.speechSynthesis.cancel();
        };
    }, [message]);

    return (
        <div className="coach-container">
            <div className="coach-avatar">
                🤖
            </div>
            <div className="coach-content">
                <h4>AI Performance Coach</h4>
                <div className="coach-message">
                    {displayedText}
                    <span className="animate-pulse">|</span>
                </div>
            </div>
        </div>
    );
};

export default AICoach;
