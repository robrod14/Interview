"use client";
import { Suspense, useState } from 'react';
import { api } from '@/lib/api';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const res = await api.fetch('/auth/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (res.ok) {
            const data = await res.json();
            api.setToken(data.access_token);

            // VULNERABILITY: Open Redirect
            // The ?next= parameter is passed to the backend redirect endpoint
            // with zero validation. An attacker who crafts:
            //   /login?next=https://evil.com
            // will redirect the victim to their phishing site after login.
            const nextUrl = searchParams.get('next') || '/dashboard';
            const redirectRes = await api.fetch(
                `/auth/redirect?next=${encodeURIComponent(nextUrl)}`
            );
            const redirectData = await redirectRes.json();
            window.location.href = redirectData.redirect_to;
        } else {
            setError("Invalid credentials");
        }
    } catch (err) {
        setError("Login failed");
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900 text-white">
      <div className="w-full max-w-md">
        <div className="bg-gray-800 p-8 rounded-lg shadow-lg">
            <h1 className="text-3xl font-bold mb-6 text-center text-blue-400">SaaS Login</h1>
            
            {error && (
                <div className="bg-red-500/20 border border-red-500 text-red-200 p-3 rounded mb-4 text-sm">
                    {error}
                </div>
            )}
            
            <form onSubmit={handleLogin} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium mb-1">Username</label>
                    <input 
                        type="text" 
                        className="w-full p-3 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium mb-1">Password</label>
                    <input 
                        type="password" 
                        className="w-full p-3 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>
                <button 
                    type="submit"
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded transition duration-200"
                >
                    Sign In
                </button>
            </form>

            <div className="mt-4 text-center">
                <Link
                    href="/forgot-password"
                    className="text-sm text-blue-400 hover:text-blue-300 underline"
                >
                    Forgot your password?
                </Link>
            </div>
        </div>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-gray-900 text-white">Loading...</div>}>
      <LoginForm />
    </Suspense>
  );
}
