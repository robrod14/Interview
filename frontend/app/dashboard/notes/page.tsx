"use client";
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface Note {
    id: number;
    title: string;
    content: string;
    is_secret: boolean;
}

export default function NotesPage() {
    const [notes, setNotes] = useState<Note[]>([]);
    const [title, setTitle] = useState("");
    const [content, setContent] = useState("");
    const [isSecret, setIsSecret] = useState(false);

    useEffect(() => {
        fetchNotes();
    }, []);

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
