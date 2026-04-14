"use client";
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { api } from '@/lib/api';
import { useEffect } from 'react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Scoreboard is the only exception allowing access without a user token
    // so candidates can start a new session or view progress.
    if (pathname === '/dashboard/scoreboard') {
        return;
    }

    const token = api.getToken();
    if (!token) {
        router.push('/login');
    }
  }, [pathname, router]);

  const handleLogout = () => {
    api.clearToken();
    router.push('/login');
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-blue-400">SaaS App</h1>
        </div>
        <nav className="flex-1 px-4 space-y-2">
          <Link href="/dashboard" className="block px-4 py-2 rounded hover:bg-gray-700">Overview</Link>
          <Link href="/dashboard/invoices" className="block px-4 py-2 rounded hover:bg-gray-700">Invoices</Link>
          <Link href="/dashboard/notes" className="block px-4 py-2 rounded hover:bg-gray-700">Notes</Link>
          <Link href="/dashboard/profile" className="block px-4 py-2 rounded hover:bg-gray-700">Profile</Link>
          <div className="border-t border-gray-700 my-2 pt-2">
            <Link href="/dashboard/scoreboard" className="block px-4 py-2 rounded hover:bg-gray-700 text-green-400 font-medium">🏆 Scoreboard</Link>
          </div>
        </nav>
        <div className="p-4 border-t border-gray-700">
          <button onClick={handleLogout} className="w-full text-left px-4 py-2 text-red-400 hover:text-red-300">
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8">
        {children}
      </main>
    </div>
  );
}
