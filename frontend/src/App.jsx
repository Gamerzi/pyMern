import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// Corrected line:
import { AuthProvider } from './context/AuthContext'; // Changed contexts to context

import Layout from './components/Layout'; // Optional Layout wrapper
import ProtectedRoute from './components/ProtectedRoute';

// Import Pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import MemoriesPage from './pages/MemoriesPage';
import ConversationPage from './pages/ConversationPage';
// Import AddMemoryPage if you create it

import './index.css'; // Include global styles

function App() {
    return (
        <AuthProvider> {/* Wrap everything in AuthProvider */}
            <Router>
                <Routes>
                    {/* Public Routes */}
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />

                    {/* Protected Routes */}
                    <Route element={<ProtectedRoute />}> {/* Routes requiring login */}
                         <Route element={<Layout />}> {/* Optional: Wrap protected pages in a Layout */}
                            <Route path="/" element={<HomePage />} />
                            <Route path="/memories" element={<MemoriesPage />} />
                            <Route path="/conversation" element={<ConversationPage />} />
                             {/* <Route path="/memories/add" element={<AddMemoryPage />} /> */}
                             {/* Add other protected routes here */}
                         </Route>
                    </Route>

                    {/* Optional: Add a 404 Not Found Route */}
                    <Route path="*" element={<div>404 Not Found</div>} />
                </Routes>
            </Router>
        </AuthProvider>
    );
}

export default App;