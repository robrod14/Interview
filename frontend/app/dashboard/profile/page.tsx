"use client";
import { useState } from 'react';
import { api } from '@/lib/api';

export default function ProfilePage() {
    const [avatarUrl, setAvatarUrl] = useState("");
    const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [debugInfo, setDebugInfo] = useState<any>(null);

    const handleFetchAvatar = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        setDebugInfo(null);
        setAvatarPreview(null);

        // Get value directly from form data to bypass React state re-render issues
        // allowing the user to modify the input type in DevTools
        const form = e.target as HTMLFormElement;
        const input = form.elements.namedItem('avatar_url') as HTMLInputElement;
        let urlToFetch = input.value;

        // BROWSER FAKEPATH HANDLING:
        // When input type="file", browsers obscure the real path with "C:\fakepath\".
        // The backend expects a URL (SSRF vuln).
        // If the user selects a file normally, we want to simulate a successful "upload" (which is actually just a fetch)
        // by converting it to a fake internal URL or handling it gracefully.
        // BUT, if they changed it to type="text", the value will be the literal string they typed.
        
        // If it starts with C:\fakepath\, it means they used the file picker.
        // We can't actually upload the file because our backend expects a URL string (UrlRequest).
        // To make the "normal" flow look like it works (or at least fail gracefully without crashing requests),
        // we can replace it with a dummy URL or just let the backend handle the error gracefully.
        // The user says "No connection adapters were found for 'C:\\fakepath\\sample.jpeg'".
        // This comes from the backend `requests.get(url)` trying to fetch "C:\fakepath\...".
        
        if (urlToFetch.includes("fakepath")) {
             // Fake a "successful" looking dummy URL to prevent the scary error
             // or just strip it to the filename and pretend to fetch it relative?
             // Actually, let's just prepend http://localhost/ to make it a valid URL format so requests doesn't crash on schema,
             // or handle the error better in the backend. 
             // But simpler: just tell the user "File upload not supported in this demo mode" via the UI?
             // No, the user said "If a user tryies to upload a picture from their machine this should work".
             // "This should work" implies we should actually upload it? 
             // BUT the backend is designed for SSRF (taking a URL).
             // If we want to support file upload, we need multipart/form-data.
             // BUT that ruins the SSRF challenge which relies on `request.url` (string).
             
             // COMPROMISE: If they select a file, we treat it as a "local file URL" that obviously fails 
             // but with a nicer message, OR we just ignore the file and use a placeholder.
             // The user wants it to "work". 
             // "Our server will fetch it and optimize it for you."
             
             // If I select "myimage.png", the browser gives "C:\fakepath\myimage.png".
             // I cannot get the real path or the file content via `input.value` due to browser security.
             // I CAN get the file object via `input.files[0]`.
             
             // To support "real" upload, I would need to change the backend to accept EITHER a URL OR a File.
             // But the vulnerability is in the `fetch_avatar` endpoint which takes `UrlRequest`.
             
             // TRICK: If they pick a file, we can say "Image uploaded successfully" (fake it)
             // without actually calling the backend, OR call the backend with a dummy safe URL.
             // The goal is to not distract them with a python error.
             
             // Let's just catch the "fakepath" case and send a dummy URL that returns a placeholder image.
             // Or better: send a file:// URL that we know exists? No, we don't know their FS.
             
             // Let's prevent the "No connection adapters" error by detecting fakepath here
             // and sending a safe default URL that returns a "Upload Success" message.
             
             // Wait, the user said "If a user tryies to upload a picture from their machine this should work".
             // Maybe "work" means "don't crash".
             // Let's strip the fakepath and treat it as a relative URL, which `requests` might try to fetch from localhost?
             // No, requests needs a schema.
             
             // I will modify the input to be a valid URL if it's a file path.
             // But better: let's handle the `input.files` case!
             
             if (input.files && input.files.length > 0) {
                 // They used the file picker.
                 // We can't send the file content because the API expects { url: string }.
                 // We'll just pretend we uploaded it by sending a dummy URL.
                // We use localhost to ensure it resolves without internet.
                // urlToFetch = "http://127.0.0.1:8000/"; 
                
                // IMPROVEMENT: Render the local file immediately to show it works!
                const file = input.files[0];
                const reader = new FileReader();
                reader.onload = (e) => {
                    setAvatarPreview(e.target?.result as string);
                };
                reader.readAsDataURL(file);
                
                // We still need to send SOMETHING to the backend to avoid errors if they click "Import".
                urlToFetch = "http://127.0.0.1:8000/"; 
             }
        }

        try {
            const res = await api.fetch('/misc/fetch-avatar', {
                method: 'POST',
                body: JSON.stringify({ url: urlToFetch })
            });
            
            const data = await res.json();
            
            if (data.error) {
                setError(data.error);
            } else {
                setDebugInfo(data);
                // In a real app we might display the image, but here we just show what we fetched
                // If it's an image, we could try to render it, but for SSRF demo, showing the text content is better
                // because they might fetch /etc/passwd or internal metadata
            }
        } catch (err) {
            setError("Failed to fetch avatar");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h1 className="text-3xl font-bold mb-6">Profile Settings</h1>
            
            <div className="bg-gray-800 p-8 rounded-lg shadow max-w-2xl">
                <h2 className="text-xl font-bold mb-4">Avatar</h2>
                <p className="text-gray-400 mb-4 text-sm">
                    Browse your computer for an avatar of your choosing.
                    Our server will fetch it and optimize it for you.
                </p>

                {/* 
                  Using dangerouslySetInnerHTML to render the form inputs.
                  This "ejects" the inputs from React's Virtual DOM reconciliation.
                  Why? Because in this CTF challenge, we WANT the user to be able to use DevTools
                  to change type="file" to type="text". 
                  If we use standard JSX, React will re-render and revert the DOM change 
                  whenever any parent component updates or if React decides to reconcile.
                */}
                <form onSubmit={handleFetchAvatar} className="space-y-4">
                    <div dangerouslySetInnerHTML={{ __html: `
                        <div class="flex gap-2">
                            <input 
                                name="avatar_url"
                                type="file" 
                                class="flex-1 p-3 rounded bg-gray-700 border border-gray-600 focus:border-blue-500 focus:outline-none text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"
                                placeholder="Select image"
                            />
                            <button 
                                type="submit"
                                class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded disabled:opacity-50"
                            >
                                Import
                            </button>
                        </div>
                    `}} />
                </form>

                {error && (
                    <div className="mt-4 bg-red-500/20 border border-red-500 text-red-200 p-3 rounded">
                        {error}
                    </div>
                )}

                {/* 
                  If we have a local preview (file upload), show it.
                  OR if the backend returned an image (SSRF to external image), show that!
                */}
                {(avatarPreview || debugInfo?.is_image) && (
                    <div className="mt-6 text-center">
                        <h3 className="font-bold mb-2 text-blue-400">Avatar Preview:</h3>
                        <img 
                            src={avatarPreview || debugInfo?.image_data} 
                            alt="Avatar Preview" 
                            className="w-32 h-32 rounded-full mx-auto border-4 border-blue-500 shadow-lg object-cover"
                        />
                    </div>
                )}

                {debugInfo && !avatarPreview && !debugInfo.is_image && (
                    <div className="mt-6">
                        <h3 className="font-bold mb-2 text-green-400">Fetch Result:</h3>
                        <div className="bg-black p-4 rounded font-mono text-xs overflow-x-auto border border-gray-700">
                            <div className="mb-2 text-gray-500">
                                Status: {debugInfo.status} | Size: {debugInfo.content_length} bytes
                            </div>
                            <pre className="text-gray-300 whitespace-pre-wrap">
                                {debugInfo.data}
                            </pre>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
