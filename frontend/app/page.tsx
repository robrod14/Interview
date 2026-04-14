"use client";
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function Home() {
  const [candidateName, setCandidateName] = useState("");
  const [started, setStarted] = useState(false);

  useEffect(() => {
    // Check if session already exists
    if (localStorage.getItem('candidate_session_id')) {
        window.location.href = '/login';
    }
  }, []);

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!candidateName) return;

    try {
        const res = await api.fetch('/session/start', {
            method: 'POST',
            body: JSON.stringify({ candidate_name: candidateName })
        }); // Use relative path? api.fetch prepends /api
        // Wait, api.fetch prepends /api.
        // But in api.fetch, I used `${API_BASE}${endpoint}`.
        // So I should pass `/session/start`.
        
        if (res.ok) {
            const data = await res.json();
            localStorage.setItem('candidate_session_id', data.session_id);
            localStorage.setItem('candidate_name', data.candidate_name);
            setStarted(true);
            window.location.href = '/login';
        }
    } catch (err) {
        console.error(err);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900 text-white">
      <div className="z-10 max-w-5xl w-full items-center justify-center font-mono text-sm lg:flex">
        <div className="bg-gray-800 p-8 rounded-lg shadow-lg w-full max-w-md">
            <h1 className="text-3xl font-bold mb-6 text-center text-blue-400">Interview Lab</h1>
            <p className="mb-8 text-gray-300 text-center">Enter your name/ID to begin the assessment session.</p>
            
            <form onSubmit={handleStart} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium mb-1">Candidate Name</label>
                    <input 
                        type="text" 
                        className="w-full p-3 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none"
                        value={candidateName}
                        onChange={(e) => setCandidateName(e.target.value)}
                        placeholder="John Doe"
                    />
                </div>
                <button 
                    type="submit"
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded transition duration-200"
                >
                    Start Session
                </button>
            </form>
        </div>
      </div>
    </main>
  );
}
