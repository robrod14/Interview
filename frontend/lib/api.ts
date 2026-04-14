import Cookies from 'js-cookie';

const API_BASE = '/api'; // Using Next.js rewrites

export const api = {
    setToken(token: string) {
        Cookies.set('token', token);
    },

    getToken() {
        return Cookies.get('token');
    },

    clearToken() {
        Cookies.remove('token');
    },

    async fetch(endpoint: string, options: RequestInit = {}) {
        const token = this.getToken();
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string>),
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Pass candidate session ID if exists (from localStorage)
        if (typeof window !== 'undefined') {
             const sessionId = localStorage.getItem('candidate_session_id');
             if (sessionId) {
                 headers['X-Candidate-ID'] = sessionId;
             }
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
        });

        if (response.status === 401) {
            // Redirect to login if not already there
            if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        }

        return response;
    }
};
