import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
// Corrected line:
import { useAuth } from '../context/AuthContext'; // Changed contexts to context

const ProtectedRoute = () => {
    const { authToken, isLoading } = useAuth();

    if (isLoading) {
        // Optional: Show a loading spinner while checking auth status
        return <div>Loading...</div>;
    }

    // If done loading and still no token, redirect to login
    if (!authToken) {
        return <Navigate to="/login" replace />;
    }

    // If authenticated, render the child route component
    return <Outlet />;
};

export default ProtectedRoute;