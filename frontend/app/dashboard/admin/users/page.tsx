"use client";
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function AdminUsersPage() {
    const [users, setUsers] = useState<any[]>([]);
    const [error, setError] = useState("");

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            // This endpoint is protected by admin role
            const res = await api.fetch('/admin/users');
            if (res.ok) {
                const data = await res.json();
                setUsers(data);
            } else {
                setError("Access Denied: You need to be an admin to view this page.");
            }
        } catch (e) {
            setError("Failed to fetch users.");
        }
    };

    return (
        <div>
            <h1 className="text-3xl font-bold mb-6">User Management (Admin)</h1>
            
            {error && (
                <div className="bg-red-500/20 border border-red-500 text-red-200 p-4 rounded mb-6">
                    {error}
                </div>
            )}

            {!error && (
                <div className="bg-gray-800 rounded-lg overflow-hidden">
                    <table className="w-full text-left">
                        <thead className="bg-gray-700">
                            <tr>
                                <th className="p-4">ID</th>
                                <th className="p-4">Username</th>
                                <th className="p-4">Role</th>
                                <th className="p-4">Tenant ID</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.id} className="border-t border-gray-700">
                                    <td className="p-4">{u.id}</td>
                                    <td className="p-4">{u.username}</td>
                                    <td className="p-4">{u.role}</td>
                                    <td className="p-4">{u.tenant_id}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
