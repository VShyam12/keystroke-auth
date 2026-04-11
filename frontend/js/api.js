const BASE_URL = 'http://127.0.0.1:5000/api';

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + sessionStorage.getItem('auth_token')
    };
}

function getToken() {
    return sessionStorage.getItem('auth_token');
}

function getUserId() {
    return sessionStorage.getItem('user_id');
}

function isLoggedIn() {
    const token = sessionStorage.getItem('auth_token');
    return !!token && token !== 'null' && 
           token !== 'undefined' && token !== '';
}

function checkAuth(previewBypass) {
    if (previewBypass) {
        const params = new URLSearchParams(window.location.search);
        if (params.get('preview') === 'true') return;
    }
    if (!isLoggedIn()) {
        window.location.replace('login.html');
    }
}

function logout() {
    sessionStorage.clear();
    window.location.replace('login.html');
}

async function apiGet(endpoint) {
    try {
        const response = await fetch(BASE_URL + endpoint, {
            method: 'GET',
            headers: getAuthHeaders()
        });
        if (response.status === 401) return null;
        if (!response.ok) return null;
        return await response.json();
    } catch (e) {
        console.warn('apiGet failed:', endpoint, e.message);
        return null;
    }
}

async function apiPost(endpoint, body) {
    try {
        const response = await fetch(BASE_URL + endpoint, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(body)
        });
        if (response.status === 401) return null;
        if (!response.ok) return null;
        return await response.json();
    } catch (e) {
        console.warn('apiPost failed:', endpoint, e.message);
        return null;
    }
}

function generateSessionId() {
    let id = sessionStorage.getItem('session_id');
    if (id) return id;
    id = 'sess_' + Date.now() + '_' + 
         Math.random().toString(36).substr(2, 9);
    sessionStorage.setItem('session_id', id);
    return id;
}

async function logEvent(eventType, eventDetail) {
    try {
        const token = sessionStorage.getItem('auth_token');
        const userId = sessionStorage.getItem('user_id');
        if (!token || !userId || token === 'null' || 
            token === 'undefined') return;
        await fetch(BASE_URL + '/session/event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token.trim()
            },
            body: JSON.stringify({
                session_id: generateSessionId(),
                event_type: String(eventType),
                event_detail: String(eventDetail || '')
            })
        });
    } catch (e) {
        // silent fail - never break UI
    }
}
