"use client";
import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';

interface Note {
    id: number;
    title: string;
    content: string;
    is_secret: boolean;
}

interface SearchResult {
    id: number;
    title: string;
    content: string;
}

interface SearchResponse {
    search_term: string;
    count: number;
    results: SearchResult[];
}

export default function NotesPage() {
    return (
        <Suspense fallback={<div className="text-gray-400">Loading notes...</div>}>
            <NotesPageInner />
        </Suspense>
    );
}

function NotesPageInner() {
    const [notes, setNotes] = useState<Note[]>([]);
    const [title, setTitle] = useState("");
    const [content, setContent] = useState("");
    const [isSecret, setIsSecret] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
    const [isSearching, setIsSearching] = useState(false);
    const searchParams = useSearchParams();
    const router = useRouter();

    useEffect(() => {
        fetchNotes();
        // DOM-Based XSS sink: read ?q= from URL and trigger search on load
        // This allows an attacker to craft a malicious link like:
        //   /dashboard/notes?q=<img src=x onerror=alert(document.cookie)>
        const q = searchParams.get('q');
        if (q) {
            setSearchQuery(q);
            performSearch(q);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const performSearch = async (query: string) => {
        if (!query.trim()) {
            setSearchResponse(null);
            return;
        }
        setIsSearching(true);
        try {
            const res = await api.fetch(`/misc/search?q=${encodeURIComponent(query)}`);
            if (res.ok) {
                const data = await res.json();
                setSearchResponse(data);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setIsSearching(false);
        }
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        // Update the URL so the link is shareable (and exploitable)
        router.push(`/dashboard/notes?q=${encodeURIComponent(searchQuery)}`);
        performSearch(searchQuery);
    };

    const handleClearSearch = () => {
        setSearchQuery("");
        setSearchResponse(null);
        router.push('/dashboard/notes');
    };

    const fetchNotes = async () => {
        try {
            const res = await api.fetch('/notes/');
            if (res.ok) {
                const data = await res.json();
                setNotes(data);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleCreateNote = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await api.fetch('/notes/', {
                method: 'POST',
                body: JSON.stringify({ title, content, is_secret: isSecret })
            });
            if (res.ok) {
                setTitle("");
                setContent("");
                setIsSecret(false);
                fetchNotes();
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleDeleteNote = async (id: number) => {
        if (!confirm("Are you sure you want to delete this note?")) return;
        try {
            const res = await api.fetch(`/notes/${id}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                fetchNotes();
            } else {
                alert("Failed to delete note");
            }
        } catch (e) {
            console.error(e);
        }
    };
    return (
        <div>
            <h1 className="text-3xl font-bold mb-6">Notes</h1>

            {/* Search Bar */}
            <div className="bg-gray-800 p-4 rounded-lg shadow mb-6">
                <form onSubmit={handleSearch} className="flex gap-2">
                    <input
                        type="text"
                        className="flex-1 p-2 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none text-gray-200"
                        placeholder="Search notes..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <button
                        type="submit"
                        className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                    >
                        {isSearching ? 'Searching...' : 'Search'}
                    </button>
                    {searchResponse && (
                        <button
                            type="button"
                            onClick={handleClearSearch}
                            className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded"
                        >
                            Clear
                        </button>
                    )}
                </form>

                {/* VULNERABILITY: DOM-Based XSS */}
                {/* search_term comes from the server, which echoes the raw ?q= URL param */}
                {/* Rendering it with dangerouslySetInnerHTML turns it into an XSS sink */}
                {/* Craft: /dashboard/notes?q=<img src=x onerror=alert(1)> to exploit */}
                {searchResponse && (
                    <div className="mt-3 text-sm text-gray-400">
                        Showing {searchResponse.count} result(s) for:&nbsp;
                        <span
                            className="text-blue-300 font-mono"
                            dangerouslySetInnerHTML={{ __html: searchResponse.search_term }}
                        />
                    </div>
                )}

                {/* Search Results */}
                {searchResponse && searchResponse.results.length > 0 && (
                    <div className="mt-4 space-y-2">
                        {searchResponse.results.map(r => (
                            <div key={r.id} className="bg-gray-700 p-3 rounded border border-gray-600">
                                <p className="font-bold text-white">{r.title}</p>
                                <p className="text-gray-400 text-sm mt-1">{r.content}</p>
                            </div>
                        ))}
                    </div>
                )}

                {searchResponse && searchResponse.results.length === 0 && (
                    <p className="mt-3 text-gray-500 text-sm">No notes matched your search.</p>
                )}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Create Note */}
                <div className="bg-gray-800 p-6 rounded-lg shadow h-fit">
                    <h2 className="text-xl font-bold mb-4">New Note</h2>
                    <form onSubmit={handleCreateNote} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">Title</label>
                            <input 
                                type="text" 
                                className="w-full p-2 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">Content</label>
                            <textarea 
                                className="w-full p-2 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none h-32"
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                                required
                            />
                        </div>
                        <div className="flex items-center">
                            <input 
                                type="checkbox" 
                                id="isSecret" 
                                className="mr-2"
                                checked={isSecret}
                                onChange={(e) => setIsSecret(e.target.checked)}
                            />
                            <label htmlFor="isSecret" className="text-sm">Is Secret?</label>
                        </div>
                        <button 
                            type="submit"
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                        >
                            Save Note
                        </button>
                    </form>
                </div>

                {/* List Notes */}
                <div className="space-y-4">
                    {notes.map(note => (
                        <div key={note.id} className="bg-gray-800 p-6 rounded-lg shadow">
                            <div className="flex justify-between items-start mb-2">
                                <h3 className="text-lg font-bold">{note.title}</h3>
                                <div className="flex items-center space-x-2">
                                    {note.is_secret && (
                                        <span className="bg-red-500/20 text-red-400 text-xs px-2 py-1 rounded">Secret</span>
                                    )}
                                    <button 
                                        onClick={() => handleDeleteNote(note.id)}
                                        className="text-gray-400 hover:text-red-500 transition-colors"
                                        title="Delete Note"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                    </button>
                                </div>
                            </div>
                            {/* VULNERABILITY: Stored XSS */}
                            {/* We dangerouslySetInnerHTML to allow the XSS to execute */}
                            <div 
                                className="text-gray-300 prose prose-invert"
                                dangerouslySetInnerHTML={{ __html: note.content }}
                            />
                        </div>
                    ))}
                    {notes.length === 0 && (
                        <p className="text-gray-500">No notes found.</p>
                    )}
                </div>
            </div>
        </div>
    );
}
