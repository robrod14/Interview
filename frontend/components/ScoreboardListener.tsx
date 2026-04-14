"use client";
import React, { useEffect, useState, useRef } from 'react';

interface Vulnerability {
    vuln_id: string;
    name: string;
    points: number;
}

export function ScoreboardListener() {
    const [notifications, setNotifications] = useState<Vulnerability[]>([]);
    const [connected, setConnected] = useState(false);
    const audioCtxRef = useRef<AudioContext | null>(null);

    // Initialize/Unlock Audio Context on first user interaction
    useEffect(() => {
        const unlockAudio = () => {
            if (!audioCtxRef.current) {
                audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
            }
            if (audioCtxRef.current.state === 'suspended') {
                audioCtxRef.current.resume();
            }
            // Remove listeners once unlocked
            window.removeEventListener('click', unlockAudio);
            window.removeEventListener('keydown', unlockAudio);
        };

        window.addEventListener('click', unlockAudio);
        window.addEventListener('keydown', unlockAudio);
        
        return () => {
            window.removeEventListener('click', unlockAudio);
            window.removeEventListener('keydown', unlockAudio);
        };
    }, []);

    const playSuccessSound = () => {
        try {
            if (!audioCtxRef.current) {
                audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
            }
            
            const ctx = audioCtxRef.current;
            if (ctx.state === 'suspended') {
                ctx.resume();
            }

            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            
            osc.connect(gain);
            gain.connect(ctx.destination);
            
            // "Coin" sound: rapid pitch slide up
            osc.type = 'sine';
            osc.frequency.setValueAtTime(1000, ctx.currentTime); 
            osc.frequency.exponentialRampToValueAtTime(2000, ctx.currentTime + 0.1);
            
            gain.gain.setValueAtTime(0.1, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
            
            osc.start();
            osc.stop(ctx.currentTime + 0.4);
        } catch (e) {
            console.error("Audio play failed", e);
        }
    };

    useEffect(() => {
        let eventSource: EventSource | null = null;
        let retryInterval: NodeJS.Timeout;

        const connect = () => {
            const sessionId = localStorage.getItem('candidate_session_id');
            if (!sessionId) return;

            // If already connected to this session, skip
            if (eventSource?.url.includes(sessionId) && eventSource.readyState !== EventSource.CLOSED) {
                return;
            }

            console.log("Connecting to Scoreboard SSE...", sessionId);
            // Use absolute URL to bypass Next.js proxy buffering issues in dev
            eventSource = new EventSource(`http://127.0.0.1:8000/api/session/events?session_id=${sessionId}`);

            eventSource.onopen = () => {
                console.log("Scoreboard SSE Connected");
                setConnected(true);
            };

            eventSource.onmessage = (event) => {
                console.log("SSE Message:", event.data);
                
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'keepalive') {
                        console.log("SSE Keepalive");
                        return;
                    }

                    if (data.type === 'vuln_found') {
                        const vuln = data.payload;
                        const uniqueId = vuln.vuln_id + "-" + Date.now();
                        
                        setNotifications(prev => [...prev, { ...vuln, vuln_id: uniqueId }]);
                        playSuccessSound();

                        setTimeout(() => {
                            setNotifications(prev => prev.filter(n => n.vuln_id !== uniqueId));
                        }, 5000);
                    }
                } catch (e) {
                    console.error("Error parsing SSE", e);
                }
            };

            eventSource.onerror = (err) => {
                console.error("Scoreboard SSE Error", err);
                setConnected(false);
                eventSource?.close();
                // Retry will happen via interval
            };
        };

        // Check for session ID every 2 seconds if not connected
        retryInterval = setInterval(() => {
            const sessionId = localStorage.getItem('candidate_session_id');
            if (!sessionId) {
                 console.log("ScoreboardListener: No session ID found in localStorage yet.");
            } else if (!eventSource || eventSource.readyState === EventSource.CLOSED) {
                connect();
            }
        }, 2000);

        // Try initial connect
        connect();

        return () => {
            if (eventSource) {
                eventSource.close();
            }
            clearInterval(retryInterval);
        };
    }, []);

    // For debugging, always render the container so we can see the debug dot
    // if (notifications.length === 0) return null;

    return (
        <div className="fixed top-4 right-4 z-[9999] space-y-4 pointer-events-none">
            {notifications.map((n, idx) => (
                <div 
                    key={n.vuln_id || idx}
                    className="bg-green-600 text-white px-6 py-4 rounded shadow-lg transform transition-all duration-500 flex flex-col animate-slide-in-right"
                >
                    <div className="text-lg font-bold">Vulnerability Found!</div>
                    <div className="text-sm">{n.name}</div>
                    <div className="text-xs mt-1 bg-green-700 inline-block px-2 py-1 rounded self-start">+{n.points} Points</div>
                </div>
            ))}
            
            <style jsx global>{`
                @keyframes slide-in-right {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                .animate-slide-in-right {
                    animation: slide-in-right 0.5s ease-out forwards;
                }
            `}</style>
        </div>
    );
}
