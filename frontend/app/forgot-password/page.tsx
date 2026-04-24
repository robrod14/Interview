"use client";
import { useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function ForgotPasswordPage() {
    const [username, setUsername] = useState("");
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState<any>(null);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        setResponse(null);

        try {
            const res = await api.fetch('/auth/forgot-password', {
                method: 'POST',
                body: JSON.stringify({ username }),
            });
            const data = await res.json();
            setResponse(data);
        } catch {
            setError('Request failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900 text-white">
            <div className="w-full max-w-md">
                <div className="bg-gray-800 p-8 rounded-lg shadow-lg">
                    <h1 className="text-3xl font-bold mb-2 text-center text-blue-400">
                        Reset Password
                    </h1>
                    <p className="text-gray-400 text-sm text-center mb-6">
                        Enter your username and we&apos;ll generate a reset token for you.
                    </p>

                    {!response ? (
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Username</label>
                                <input
                                    type="text"
                                    className="w-full p-3 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded disabled:opacity-50"
                            >
                                {loading ? 'Sending...' : 'Send Reset Token'}
                            </button>
                        </form>
                    ) : (
                        <div className="space-y-4">
                            {/* VULNERABILITY: The API response contains the reset token in dev_note.
                                A tester inspecting the network response can grab it and use it
                                to reset any user's password via /reset-password. */}
                            <div className="bg-green-500/20 border border-green-500 text-green-200 p-4 rounded">
                                <p className="font-medium">✓ {response.message}</p>
                                {response.dev_note && (
                                    <p className="mt-2 text-xs text-green-300 font-mono break-all">
                                        {response.dev_note}
                                    </p>
                                )}
                            </div>
                            <p className="text-gray-400 text-sm">
                                Copy your reset token above and use it on the reset page.
                            </p>
                            <Link
                                href={`/reset-password?username=${encodeURIComponent(username)}`}
                                className="block w-full text-center bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded"
                            >
                                Go to Reset Password
                            </Link>
                        </div>
                    )}

                    {error && (
                        <div className="mt-4 bg-red-500/20 border border-red-500 text-red-200 p-3 rounded text-sm">
                            {error}
                        </div>
                    )}

                    <div className="mt-6 text-center">
                        <Link href="/login" className="text-sm text-gray-400 hover:text-gray-300">
                            ← Back to Login
                        </Link>
                    </div>
                </div>
            </div>
        </main>
    );
}
