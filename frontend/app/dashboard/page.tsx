"use client";
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function DashboardPage() {
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        // Since we don't have a /me endpoint that returns full user info easily without vuln,
        // we can assume the user is logged in if we are here (protected by layout logic or api error handling)
        // But let's fetch something.
        // Actually, we can decode the token to get username.
        // But let's just show a welcome message.
    }, []);

    return (
        <div>
            <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gray-800 p-6 rounded-lg shadow">
                    <h2 className="text-xl font-bold mb-2">Invoices</h2>
                    <p className="text-gray-400">Manage your billing and payments.</p>
                </div>
                <div className="bg-gray-800 p-6 rounded-lg shadow">
                    <h2 className="text-xl font-bold mb-2">Notes</h2>
                    <p className="text-gray-400">Secure notes for your team.</p>
                </div>
                <div className="bg-gray-800 p-6 rounded-lg shadow">
                    <h2 className="text-xl font-bold mb-2">Profile</h2>
                    <p className="text-gray-400">Update your avatar and settings.</p>
                </div>
            </div>
            
            <div className="mt-8 bg-gray-800 p-6 rounded-lg shadow border border-yellow-600/30">
                <h3 className="text-lg font-bold text-yellow-500 mb-2">Security Notice</h3>
                <p className="text-gray-300">
                    This application is currently undergoing a security audit. 
                    If you find any vulnerabilities, please report them to the admin.
                </p>
            </div>
        </div>
    );
}
