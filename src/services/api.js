/**
 * API Service to handle all backend communications
 */

const API_BASE_URL = 'https://chennai-hospitals-backend-production.up.railway.app';

export const submitQuery = async (queryData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/queries`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(queryData),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to submit query');
        return data;
    } catch (error) {
        console.error('API Error (submitQuery):', error);
        throw error;
    }
};

export const requestAppointment = async (appointmentData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/appointments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(appointmentData),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to request appointment');
        return data;
    } catch (error) {
        console.error('API Error (requestAppointment):', error);
        throw error;
    }
};

export const login = async (credentials) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Login failed');
        return data;
    } catch (error) {
        console.error('API Error (login):', error);
        throw error;
    }
};

export const signup = async (userData) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Signup failed');
        return data;
    } catch (error) {
        console.error('API Error (signup):', error);
        throw error;
    }
};

export const fetchHospitals = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/hospitals`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to fetch hospitals');
        return data;
    } catch (error) {
        console.error('API Error (fetchHospitals):', error);
        throw error;
    }
};

export const fetchDoctors = async (hospitalId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/hospitals/${hospitalId}/doctors`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to fetch doctors');
        return data;
    } catch (error) {
        console.error('API Error (fetchDoctors):', error);
        throw error;
    }
};

export const fetchUserActivity = async (userId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/user/${userId}/activity`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to fetch activity');
        return data;
    } catch (error) {
        console.error('API Error (fetchUserActivity):', error);
        throw error;
    }
};

export const checkHealth = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return await response.json();
    } catch (error) {
        return { status: 'offline', error: error.message };
    }
};
