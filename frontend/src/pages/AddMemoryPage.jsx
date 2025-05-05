// frontend/src/pages/AddMemoryPage.jsx
// (Only create this file if you want a SEPARATE page for adding memories)

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createMemory } from '../services/apiService';

function AddMemoryPage() {
    const navigate = useNavigate();
    // --- Define State Variables ---
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [significance, setSignificance] = useState(3);
    const [tags, setTags] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false); // <-- Define loading state
    // -----------------------------

     // --- Basic Styling (same as embedded form) ---
     const formStyle = { border: '1px solid #eee', padding: '15px', borderRadius: '8px', marginBottom: '20px', maxWidth: '600px', margin: 'auto'};
     const inputGroup = { marginBottom: '10px'};
     const labelStyle = { display: 'block', marginBottom: '5px', fontWeight: 'bold'};
     const inputStyle = { width: '100%', padding: '8px', boxSizing: 'border-box' };
     const textareaStyle = { ...inputStyle, height: '100px', resize: 'vertical'};
     // --------------------------------------------

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true); // <-- Set loading true on submit

        const memoryData = {
            title,
            description,
            significance: Number(significance),
            tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag !== ''),
            // Add event_date if you include a field for it
        };

        try {
            await createMemory(memoryData);
            navigate('/memories'); // Navigate back to memories list on success
        } catch (err) {
            setError(err.detail || err.message || 'Failed to save memory');
            setLoading(false); // <-- Set loading false on error
        }
        // No need for finally if navigating away on success
        // If not navigating away, use finally: finally { setLoading(false); }
    };

    return (
        <div>
            <h2>Add New Memory</h2>
            <form onSubmit={handleSubmit} style={formStyle}>
                 <div style={inputGroup}>
                    <label htmlFor="title" style={labelStyle}>Title:</label>
                    <input type="text" id="title" value={title} onChange={e => setTitle(e.target.value)} required style={inputStyle} disabled={loading} />
                 </div>
                  <div style={inputGroup}>
                    <label htmlFor="description" style={labelStyle}>Description:</label>
                    <textarea id="description" value={description} onChange={e => setDescription(e.target.value)} required style={textareaStyle} disabled={loading}/>
                 </div>
                  <div style={inputGroup}>
                    <label htmlFor="significance" style={labelStyle}>Significance (1-5):</label>
                    <input type="number" id="significance" value={significance} onChange={e => setSignificance(e.target.value)} required min="1" max="5" style={inputStyle} disabled={loading}/>
                 </div>
                  <div style={inputGroup}>
                    <label htmlFor="tags" style={labelStyle}>Tags (comma-separated):</label>
                    <input type="text" id="tags" value={tags} onChange={e => setTags(e.target.value)} style={inputStyle} disabled={loading}/>
                 </div>
                {error && <p style={{ color: 'red' }}>{error}</p>}
                <button type="submit" disabled={loading} style={{ padding: '10px 15px' }}> {/* Use the loading state here */}
                    {loading ? 'Saving...' : 'Save Memory'} {/* Update button text based on loading state */}
                </button>
                <button type="button" onClick={() => navigate('/memories')} style={{ marginLeft: '10px' }} disabled={loading}>
                    Cancel
                </button>
            </form>
        </div>
    );
}

export default AddMemoryPage; // Uncomment if you decide to use this separate page