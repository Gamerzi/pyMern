import React, { createContext, useState, useContext, useEffect } from 'react';
import { loginUser as apiLogin, getCurrentUser } from '../services/apiService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [authToken, setAuthToken] = useState(localStorage.getItem('authToken'));
    const [currentUser, setCurrentUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true); // Indicate initial auth check

    // Effect to fetch user data when token changes or on initial load
    useEffect(() => {
        const fetchUser = async () => {
            if (authToken) {
                try {
                    localStorage.setItem('authToken', authToken); // Ensure it's stored
                    const user = await getCurrentUser();
                    setCurrentUser(user); // Set user if token is valid
                } catch (error) {
                    console.error("Failed to fetch user with token", error);
                    localStorage.removeItem('authToken'); // Clear invalid token
                    setAuthToken(null);
                    setCurrentUser(null);
                }
            } else {
                 localStorage.removeItem('authToken'); // Ensure clean state
                 setCurrentUser(null);
            }
            setIsLoading(false);
        };

        fetchUser();
    }, [authToken]); // Re-run when authToken changes

    const login = async (username, password) => {
        try {
            const data = await apiLogin(username, password);
            setAuthToken(data.access_token); // Trigger useEffect to fetch user
            return true; // Indicate success
        } catch (error) {
            console.error("AuthContext Login error:", error);
            logout(); // Clear any potentially inconsistent state
            throw error; // Re-throw for the login page to handle
        }
    };

    const logout = () => {
        setAuthToken(null);
        setCurrentUser(null);
        localStorage.removeItem('authToken');
        // Optionally redirect using navigate if needed here or in component
    };

    const value = {
        authToken,
        currentUser,
        isLoading, // Expose loading state
        login,
        logout,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

// Custom hook to use the auth context
export const useAuth = () => {
    return useContext(AuthContext);
};