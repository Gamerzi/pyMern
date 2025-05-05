import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
// Corrected line:
import { useAuth } from '../context/AuthContext'; // Changed contexts to context

function Layout() {
    const { currentUser, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login'); // Redirect to login after logout
    };

    // Basic Navbar Styling
    const navStyle = {
        backgroundColor: '#f0f0f0',
        padding: '10px 20px',
        marginBottom: '20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid #ccc'
    };

    const navLinksStyle = {
        display: 'flex',
        gap: '15px',
    };

    const linkStyle = {
        textDecoration: 'none',
        color: '#333',
        fontWeight: 'bold',
    };

    const userInfoStyle = {
        display: 'flex',
        alignItems: 'center',
        gap: '15px'
    };

    const buttonStyle = {
        padding: '5px 10px',
        cursor: 'pointer'
    };

    return (
        <div>
            <nav style={navStyle}>
                <div style={navLinksStyle}>
                    <Link to="/" style={linkStyle}>Home</Link>
                    <Link to="/memories" style={linkStyle}>Memories</Link>
                    <Link to="/conversation" style={linkStyle}>Conversation</Link>
                </div>
                <div style={userInfoStyle}>
                    {currentUser && <span>Welcome, {currentUser.username}!</span>}
                    <button onClick={handleLogout} style={buttonStyle}>Logout</button>
                </div>
            </nav>
            <main style={{ padding: '0 20px' }}>
                {/* Child routes are rendered here */}
                <Outlet />
            </main>
            {/* Optional Footer */}
            {/* <footer style={{ marginTop: '40px', textAlign: 'center', padding: '10px', borderTop: '1px solid #eee' }}>
                FutureSelf App © 2024
            </footer> */}
        </div>
    );
}

export default Layout;