// frontend/src/services/apiService.js
// This code includes the necessary exports for all functions, including uploadMemoryAttachment.

import axios from 'axios';

// Use the backend URL provided by Vite's environment variables or default
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create an axios instance
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// --- Request Interceptor ---
// Automatically add the auth token to requests if it exists
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('authToken'); // Or get from context/sessionStorage
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// --- Authentication API Calls ---
export const loginUser = async (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    try {
        const response = await apiClient.post('/auth/token', params, {
             headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        return response.data;
    } catch (error) {
        console.error("Login error:", error.response?.data || error.message);
        throw error.response?.data || new Error("Login failed");
    }
};

export const registerUser = async (userData) => {
    try {
        const response = await apiClient.post('/auth/register', userData);
        return response.data;
    } catch (error) {
        console.error("Registration error:", error.response?.data || error.message);
        throw error.response?.data || new Error("Registration failed");
    }
};

export const getCurrentUser = async () => {
    try {
        const response = await apiClient.get('/auth/users/me');
        return response.data;
    } catch (error) {
        console.error("Get user error:", error.response?.data || error.message);
        return null; // Indicate failure without throwing usually
    }
};


// --- Memory API Calls ---
export const getMemories = async (skip = 0, limit = 20) => {
    try {
        const response = await apiClient.get(`/memories/?skip=${skip}&limit=${limit}`);
        return response.data;
    } catch (error) {
        console.error("Get memories error:", error.response?.data || error.message);
        throw error.response?.data || new Error("Failed to fetch memories");
    }
};

export const createMemory = async (memoryData) => {
    try {
        const response = await apiClient.post('/memories/', memoryData);
        return response.data;
    } catch (error) {
        console.error("Create memory error:", error.response?.data || error.message);
        throw error.response?.data || new Error("Failed to create memory");
    }
};

export const updateMemory = async (memoryId, memoryData) => {
    try {
        const response = await apiClient.patch(`/memories/${memoryId}`, memoryData);
        return response.data;
    } catch (error) {
        console.error("Update memory error:", error.response?.data || error.message);
        throw error.response?.data || new Error("Failed to update memory");
    }
};

export const deleteMemory = async (memoryId) => {
    try {
        await apiClient.delete(`/memories/${memoryId}`);
        return true;
    } catch (error) {
        console.error("Delete memory error:", error.response?.data || error.message);
        throw error.response?.data || new Error("Failed to delete memory");
    }
};

// Correctly exported function
export const uploadMemoryAttachment = async (memoryId, file) => {
    const formData = new FormData();
    formData.append('file', file); // 'file' must match backend parameter name

    try {
        // NOTE: Backend endpoint /upload doesn't exist yet! This call will fail until backend is updated.
        const response = await apiClient.post(`/memories/${memoryId}/upload`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data', // Important for file uploads
            },
        });
        return response.data; // Expect backend to return updated memory or attachment info
    } catch (error) {
         console.error("Upload attachment error:", error.response?.data || error.message);
         // Add specific user feedback if possible (e.g., file too large)
        throw error.response?.data || new Error("Failed to upload attachment");
    }
};

// --- Conversation API Calls ---
export const startConversation = async (initialMessage) => {
     try {
        const response = await apiClient.post('/conversations/', { initial_message: initialMessage });
        return response.data;
    } catch (error) {
        console.error("Start conversation error:", error.response?.data || error.message);
        throw error.response?.data || new Error("Failed to start conversation");
    }
};

export const sendMessage = async (conversationId, messageContent) => {
    try {
        const response = await apiClient.post(`/conversations/${conversationId}/messages`, { content: messageContent });
        return response.data;
    } catch (error) {
        console.error("Send message error:", error.response?.data || error.message);
        throw error.response?.data || new Error("Failed to send message");
    }
};

// Optional: export the configured client if needed elsewhere
export default apiClient;