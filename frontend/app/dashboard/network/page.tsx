"use client";
import { useState } from 'react';
import { api } from '@/lib/api';

interface PingResult {
    host: string;
    stdout?: string;
    stderr?: string;
    exit_code?: number;
    error?: string;
}

export default function NetworkPage() {
    const [host, setHost] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<PingResult | null>(null);

    const handlePing = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);

        try {
            const res = await api.fetch('/misc/ping', {
                method: 'POST',
                body: JSON.stringify({ host }),
            });
            const data = await res.json();
            setResult(data);
        } catch {
            setResult({ host, error: 'Request failed.' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h1 className="text-3xl font-bold mb-2">Network Diagnostics</h1>
            <p className="text-gray-400 mb-8 text-sm">
                Internal network utility. Use this tool to verify connectivity to hosts
                from the server.
            </p>

            {/* Ping Tool */}
            <div className="bg-gray-800 p-6 rounded-lg shadow max-w-2xl">
                <h2 className="text-xl font-bold mb-1">Ping</h2>
                <p className="text-gray-400 text-sm mb-4">
                    Enter a hostname or IP address to ping from the server.
                </p>

                <form onSubmit={handlePing} className="flex gap-2">
                    <input
                        type="text"
                        className="flex-1 p-3 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none font-mono"
                        placeholder="e.g. 127.0.0.1 or google.com"
                        value={host}
                        onChange={(e) => setHost(e.target.value)}
                        required
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded disabled:opacity-50"
                    >
                        {loading ? 'Running...' : 'Ping'}
                    </button>
                </form>

                {result && (
                    <div className="mt-6">
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-gray-400 text-sm">Host:</span>
                            <span className="font-mono text-blue-300 text-sm">{result.host}</span>
                            {result.exit_code !== undefined && (
                                <span className={`ml-auto text-xs px-2 py-0.5 rounded font-bold ${
                                    result.exit_code === 0
                                        ? 'bg-green-900/60 text-green-400'
                                        : 'bg-red-900/60 text-red-400'
                                }`}>
                                    exit {result.exit_code}
                                </span>
                            )}
                        </div>

                        <div className="bg-black rounded border border-gray-700 p-4 font-mono text-xs overflow-x-auto">
                            {result.error ? (
                                <pre className="text-red-400 whitespace-pre-wrap">{result.error}</pre>
                            ) : (
                                <>
                                    {result.stdout && (
                                        <pre className="text-green-300 whitespace-pre-wrap">{result.stdout}</pre>
                                    )}
                                    {result.stderr && (
                                        <pre className="text-yellow-400 whitespace-pre-wrap">{result.stderr}</pre>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                )}
            </div>

            <div className="mt-6 bg-gray-800/50 border border-yellow-600/30 rounded-lg p-4 max-w-2xl">
                <p className="text-yellow-500 text-sm font-medium mb-1">Admin Notice</p>
                <p className="text-gray-400 text-xs">
                    This tool executes on the application server. Ensure only trusted
                    users have access to this page.
                </p>
            </div>
        </div>
    );
}
