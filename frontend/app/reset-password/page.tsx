"use client";
import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';

function ResetPasswordForm() {
    const searchParams = useSearchParams();
    const prefillUsername = searchParams.get('username') || '';

    const [username, setUsername] = useState(prefillUsername);
    const [token, setToken] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const res = await api.fetch('/auth/reset-password', {
                method: 'POST',
                body: JSON.stringify({
                    username,
                    token,
                    new_password: newPassword,
                }),
            });

            if (res.ok) {
                setSuccess(true);
            } else {
                const data = await res.json();
                setError(data.detail || 'Reset failed. Check your token and try again.');
            }
        } catch {
            setError('Request failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900 text-white">
                <div className="w-full max-w-md">
                    <div className="bg-gray-800 p-8 rounded-lg shadow-lg text-center">
                        <div className="text-5xl mb-4">✅</div>
                        <h1 className="text-2xl font-bold text-green-400 mb-2">Password Reset!</h1>
                        <p className="text-gray-400 mb-6">Your password has been updated successfully.</p>
                        <Link
                            href="/login"
                            className="block w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded"
                        >
                            Back to Login
                        </Link>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900 text-white">
            <div className="w-full max-w-md">
                <div className="bg-gray-800 p-8 rounded-lg shadow-lg">
                    <h1 className="text-3xl font-bold mb-2 text-center text-blue-400">
                        Set New Password
                    </h1>
                    <p className="text-gray-400 text-sm text-center mb-6">
                        Enter the reset token and your new password.
                    </p>

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
                        <div>
                            <label className="block text-sm font-medium mb-1">Reset Token</label>
                            <input
                                type="text"
                                className="w-full p-3 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none font-mono text-sm"
                                placeholder="Paste token from the reset email"
                                value={token}
                                onChange={(e) => setToken(e.target.value)}
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">New Password</label>
                            <input
                                type="password"
                                className="w-full p-3 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded disabled:opacity-50"
                        >
                            {loading ? 'Resetting...' : 'Reset Password'}
                        </button>
                    </form>

                    {error && (
                        <div className="mt-4 bg-red-500/20 border border-red-500 text-red-200 p-3 rounded text-sm">
                            {error}
                        </div>
                    )}

                    <div className="mt-6 text-center">
                        <Link href="/forgot-password" className="text-sm text-gray-400 hover:text-gray-300">
                            ← Request a new token
                        </Link>
                    </div>
                </div>
            </div>
        </main>
    );
}

export default function ResetPasswordPage() {
    return (
        <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-gray-900 text-white">Loading...</div>}>
            <ResetPasswordForm />
        </Suspense>
    );
}
