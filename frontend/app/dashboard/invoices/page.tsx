"use client";
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import Link from 'next/link';

interface Invoice {
    id: number;
    amount: number;
    status: string;
    date: string;
    tenant_id: number;
}

export default function InvoicesPage() {
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

    useEffect(() => {
        fetchInvoices();
    }, []);

    const fetchInvoices = async () => {
        try {
            const res = await api.fetch('/invoices'); // No trailing slash
            if (res.ok) {
                const data = await res.json();
                setInvoices(data);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleViewInvoice = async (id: number) => {
        // IDOR Vuln here: User can try to change ID in other ways, 
        // but here we just show a modal or details.
        // The candidate should notice the API call /api/invoices/{id}
        try {
            const res = await api.fetch(`/invoices/${id}`);
            if (res.ok) {
                const data = await res.json();
                setSelectedInvoice(data);
            }
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div>
            <h1 className="text-3xl font-bold mb-6">Invoices</h1>
            
            <div className="bg-gray-800 rounded-lg overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-700">
                        <tr>
                            <th className="p-4">ID</th>
                            <th className="p-4">Date</th>
                            <th className="p-4">Amount</th>
                            <th className="p-4">Status</th>
                            <th className="p-4">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {invoices.map(inv => (
                            <tr key={inv.id} className="border-t border-gray-700">
                                <td className="p-4">#{inv.id}</td>
                                <td className="p-4">{new Date(inv.date).toLocaleDateString()}</td>
                                <td className="p-4">${inv.amount.toFixed(2)}</td>
                                <td className="p-4">
                                    <span className={`px-2 py-1 rounded text-xs ${inv.status === 'paid' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                                        {inv.status}
                                    </span>
                                </td>
                                <td className="p-4">
                                    <button 
                                        onClick={() => handleViewInvoice(inv.id)}
                                        className="text-blue-400 hover:text-blue-300"
                                    >
                                        View Details
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {selectedInvoice && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
                    <div className="bg-gray-800 p-8 rounded-lg max-w-lg w-full">
                        <h2 className="text-2xl font-bold mb-4">Invoice #{selectedInvoice.id}</h2>
                        <div className="space-y-4">
                            <div className="flex justify-between">
                                <span className="text-gray-400">Amount:</span>
                                <span className="text-xl font-bold">${selectedInvoice.amount.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">Date:</span>
                                <span>{new Date(selectedInvoice.date).toLocaleDateString()}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">Status:</span>
                                <span className="capitalize">{selectedInvoice.status}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-400">Tenant ID:</span>
                                <span>{selectedInvoice.tenant_id}</span>
                            </div>
                        </div>
                        <button 
                            onClick={() => setSelectedInvoice(null)}
                            className="mt-6 w-full bg-gray-700 hover:bg-gray-600 py-2 rounded"
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
