import React from 'react';
import { Link } from 'react-router-dom';
// Corrected line:
import { useAuth } from '../context/AuthContext'; // Changed contexts to context

function HomePage() {
    const { currentUser } = useAuth();

    const containerStyle = {
        textAlign: 'center',
        padding: '40px 20px'
    };

    const headingStyle = {
        marginBottom: '30px'
    };

    const linkContainerStyle = {
        display: 'flex',
        justifyContent: 'center',
        gap: '20px',
        marginTop: '20px'
    };

    const linkStyle = {
        padding: '10px 20px',
        border: '1px solid #ccc',
        borderRadius: '5px',
        textDecoration: 'none',
        color: '#333'
    };

    return (
        <div style={containerStyle}>
            <h1 style={headingStyle}>Welcome to FutureSelf, {currentUser?.username || 'User'}!</h1>
            <p>What would you like to do today?</p>
            <div style={linkContainerStyle}>
                <Link to="/memories" style={linkStyle}>View Memories</Link>
                <Link to="/conversation" style={linkStyle}>Chat with Future Self</Link>
            </div>
        </div>
    );
}

export default HomePage;