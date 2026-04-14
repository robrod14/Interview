"use client";
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface Vulnerability {
    id: string;
    name: string;
    category: string;
    points: number;
    difficulty: string;
    severity: string;
    found: boolean;
}

interface ScoreboardData {
    candidate_name: string;
    total_points: number;
    found_vulns: Vulnerability[];
}

export default function ScoreboardPage() {
    const [data, setData] = useState<ScoreboardData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchScoreboard();
        
        // Poll every 5 seconds to keep it updated (in case of other tab activity)
        const interval = setInterval(fetchScoreboard, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchScoreboard = async () => {
        const sessionId = localStorage.getItem('candidate_session_id');
        if (!sessionId) {
            setLoading(false);
            return;
        }

        try {
            const res = await api.fetch(`/scoreboard/${sessionId}`);
            if (res.ok) {
                const scoreboardData = await res.json();
                setData(scoreboardData);
            } else if (res.status === 404) {
                // Session is invalid/expired
                localStorage.removeItem('candidate_session_id');
                localStorage.removeItem('candidate_name');
                setData(null);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="text-white p-8">Loading scoreboard...</div>;
    if (!data) return (
        <div className="text-white p-8">
            <h2 className="text-xl font-bold mb-4">No Active Session Found</h2>
            <p className="mb-4">It looks like your session has expired or the lab was reset.</p>
            <button 
                onClick={() => {
                    localStorage.removeItem('candidate_session_id');
                    localStorage.removeItem('candidate_name');
                    window.location.href = '/';
                }}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            >
                Start New Session
            </button>
        </div>
    );

    return (
        <div className="max-w-4xl mx-auto">
            <div className="bg-gray-800 rounded-lg p-8 mb-8 shadow-lg border border-gray-700">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Candidate Scoreboard</h1>
                        <p className="text-gray-400">Candidate: <span className="text-blue-400 font-semibold">{data.candidate_name}</span></p>
                    </div>
                    <div className="text-right">
                        <p className="text-sm text-gray-400 uppercase tracking-wider">Total Score</p>
                        <p className="text-5xl font-bold text-green-400">{data.total_points}</p>
                    </div>
                </div>

                <div className="w-full bg-gray-700 rounded-full h-4 mb-2">
                    <div 
                        className="bg-green-500 h-4 rounded-full transition-all duration-1000"
                        style={{ width: `${Math.min((data.total_points / 1000) * 100, 100)}%` }} // Assuming ~1000 max points
                    ></div>
                </div>
                <p className="text-xs text-right text-gray-500">Progress to Goal</p>
            </div>

            <h2 className="text-2xl font-bold text-white mb-4">Vulnerabilities Discovered</h2>
            
            <div className="grid gap-4">
                {data.found_vulns.length === 0 ? (
                    <div className="bg-gray-800/50 border border-dashed border-gray-700 rounded-lg p-12 text-center text-gray-500">
                        No vulnerabilities discovered yet. Keep hunting!
                    </div>
                ) : (
                    data.found_vulns.map((vuln) => (
                        <div key={vuln.id} className="bg-gray-800 rounded-lg p-6 border border-gray-700 flex items-center justify-between shadow-md hover:border-green-500/50 transition-colors">
                            <div>
                                <div className="flex items-center gap-3 mb-1">
                                    <h3 className="text-xl font-bold text-white">{vuln.name}</h3>
                                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                                        vuln.severity === 'Critical' ? 'bg-red-900/50 text-red-400' :
                                        vuln.severity === 'High' ? 'bg-orange-900/50 text-orange-400' :
                                        'bg-blue-900/50 text-blue-400'
                                    }`}>
                                        {vuln.severity}
                                    </span>
                                </div>
                                <p className="text-gray-400 text-sm">{vuln.category}</p>
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="text-right">
                                    <span className="block text-2xl font-bold text-green-400">+{vuln.points}</span>
                                    <span className="text-xs text-gray-500">POINTS</span>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
