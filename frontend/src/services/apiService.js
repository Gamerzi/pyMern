// frontend/src/services/apiService.js
import axios from 'axios';

// Use the backend URL provided by Vite's environment variables or default
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create an axios instance
const apiClient = axios.create({
    baseURL: API_BASE_URL,
});

// --- Request Interceptor ---
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('authToken');
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
        if (response.data.access_token) {
             localStorage.setItem('authToken', response.data.access_token);
        }
        return response.data;
    } catch (error) {
        console.error("Login error:", error.response?.data || error.message);
        localStorage.removeItem('authToken');
        throw error.response?.data || new Error("Login failed");
    }
};

export const registerUser = async (userData) => {
    try {
        const response = await apiClient.post('/auth/register', userData, {
             headers: { 'Content-Type': 'application/json' }
        });
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
        if (error.response?.status === 401) {
            console.warn("Unauthorized access attempt or token expired.");
            localStorage.removeItem('authToken');
        } else {
            console.error("Get user error:", error.response?.data || error.message);
        }
        return null;
    }
};

// --- Memory API Calls ---
export const getMemories = async (skip = 0, limit = 20) => {
    try {
        // FIXED: Removed trailing slash before query parameters
        const response = await apiClient.get(`/memories?skip=${skip}&limit=${limit}`);
        console.log("apiService.getMemories - Response Data:", response.data); // Log received data
        return response.data;
    } catch (error) {
        console.error("apiService.js Get memories error:", error.response?.data || error.message, error);
        throw error.response?.data || new Error("Failed to fetch memories");
    }
};

export const createMemory = async (formData) => {
    if (!(formData instanceof FormData)) {
         console.error("createMemory expects FormData as input when sending files.");
         throw new Error("Invalid data format for createMemory");
    }
    try {
        // FIXED: Removed trailing slash from URL
        const response = await apiClient.post('/memories', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        console.error("Create memory error in apiService:", error.response?.data || error.message);
        if (error.response) {
            console.error("Error details from createMemory:", error.response);
        }
        throw error.response?.data || new Error("Failed to create memory");
    }
};

export const updateMemory = async (memoryId, memoryData) => {
    try {
        // Ensure memoryId is not undefined before making the call
        if (memoryId === undefined || memoryId === null) {
            console.error("updateMemory: memoryId is undefined or null.");
            throw new Error("Memory ID is required for update.");
        }
        // FIXED: Removed trailing slash from URL
        const response = await apiClient.patch(`/memories/${memoryId}`, memoryData, {
             headers: { 'Content-Type': 'application/json' }
        });
        return response.data;
    } catch (error) {
        console.error("Update memory error in apiService:", error.response?.data || error.message, error);
        throw error.response?.data || new Error("Failed to update memory");
    }
};

export const deleteMemory = async (memoryId) => {
    try {
        // Ensure memoryId is not undefined before making the call
        if (memoryId === undefined || memoryId === null) {
            console.error("deleteMemory: memoryId is undefined or null. URL would be invalid.");
            throw new Error("Memory ID is required for deletion."); // Prevent call with /undefined
        }
        // FIXED: Removed trailing slash from URL
        const response = await apiClient.delete(`/memories/${memoryId}`);
        // For DELETE, a 204 No Content is common, response.data might be empty or undefined
        // Return a success indicator or rely on status code handling in the calling component
        return { success: true, status: response.status };
    } catch (error) {
        console.error("Delete memory error in apiService:", error.response?.data || error.message, error);
        throw error.response?.data || new Error("Failed to delete memory");
    }
};

export const uploadMemoryAttachment = async (memoryId, file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
        if (memoryId === undefined || memoryId === null) {
            console.error("uploadMemoryAttachment: memoryId is undefined or null.");
            throw new Error("Memory ID is required for attachment upload.");
        }
        // FIXED: Removed trailing slash and ensured endpoint matches backend if it's like "/memories/{id}/upload-attachment"
        // Assuming backend endpoint is /memories/{memoryId}/upload-attachment
        const response = await apiClient.post(`/memories/${memoryId}/upload-attachment`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
         console.error("Upload attachment error in apiService:", error.response?.data || error.message, error);
        throw error.response?.data || new Error("Failed to upload attachment");
    }
};

// --- Conversation API Calls ---
export const startConversation = async (initialMessage) => {
     try {
        // FIXED: Removed trailing slash from URL
        const response = await apiClient.post('/conversations', { initial_message: initialMessage }, {
             headers: { 'Content-Type': 'application/json' }
        });
        return response.data;
    } catch (error) {
        console.error("Start conversation error:", error.response?.data || error.message);
        throw error.response?.data || new Error("Failed to start conversation");
    }
};

export const sendMessage = async (conversationId, messageContent) => {
    try {
        // FIXED: Removed trailing slash from URL
        const response = await apiClient.post(`/conversations/${conversationId}/messages`, { content: messageContent }, {
             headers: { 'Content-Type': 'application/json' }
        });
        return response.data;
    } catch (error) {
        console.error("Send message error:", error.response?.data || error.message);
        throw error.response?.data || new Error("Failed to send message");
    }
};

export default apiClient;