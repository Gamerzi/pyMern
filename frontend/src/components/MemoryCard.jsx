// frontend/src/components/MemoryCard.jsx
import React from 'react';

// Pass onDelete and onEdit props from the parent (MemoriesPage)
function MemoryCard({ memory, onDelete, onEdit }) {
    if (!memory) return null;

    // --- Basic Styling ---
    const cardStyle = {
        border: '1px solid var(--border-light, #ddd)', // Use CSS var
        borderRadius: '8px',
        padding: '15px',
        marginBottom: '15px',
        backgroundColor: 'var(--card-bg-light, #fff)', // Use CSS var
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)', // Softer shadow
        color: 'var(--text-light, #212529)', // Ensure text color uses variable
    };
    const tagStyle = {
        display: 'inline-block',
        backgroundColor: '#e9ecef', // Lighter tag bg
        color: '#495057', // Darker tag text
        padding: '3px 8px',
        borderRadius: '12px',
        marginRight: '5px',
        marginBottom: '5px',
        fontSize: '0.9em'
    };
    const buttonStyle = { // Style for edit/delete buttons
        padding: '4px 8px',
        fontSize: '0.9em',
        marginLeft: '10px',
        cursor: 'pointer',
        border: '1px solid transparent',
        borderRadius: '4px',
    };
    const editButtonStyle = {
         ...buttonStyle,
         backgroundColor: '#cfe2ff', // Light blue accent
         color: '#0a58ca',
         borderColor: '#b6d4fe',
    };
    const deleteButtonStyle = {
         ...buttonStyle,
         backgroundColor: '#f8d7da', // Light red accent
         color: '#842029',
         borderColor: '#f5c2c7',
    };
     const attachmentListStyle = {
        listStyle: 'none',
        padding: 0,
        marginTop: '5px',
    };
    const attachmentItemStyle = {
        fontSize: '0.9em',
        marginBottom: '3px',
    };
    const attachmentLinkStyle = {
        color: 'var(--accent-light, #007bff)', // Use CSS var
        textDecoration: 'none',
    };
    const attachmentImageStyle = {
        maxWidth: '100px',
        maxHeight: '100px',
        marginTop: '5px',
        display: 'block',
        borderRadius: '4px',
    };
    // ---------------------

    const formatDate = (dateString) => {
       // ... (same as before) ...
    }

    const handleDeleteClick = () => {
        if (window.confirm(`Are you sure you want to delete the memory "${memory.title}"?`)) {
            onDelete(memory.id); // Call the prop function passed from parent
        }
    };

    const handleEditClick = () => {
        onEdit(memory); // Pass the whole memory object to the edit handler
    };

    // Simple check if attachment is an image based on common extensions
    const isImage = (filename) => /\.(jpe?g|png|gif|webp|svg)$/i.test(filename);

    return (
        <div style={cardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h3>{memory.title || 'Untitled Memory'}</h3>
                    <p style={{ marginTop: '-0.5em', fontSize: '0.9em', color: '#6c757d' }}>
                        Date: {formatDate(memory.event_date)} | Significance: {'⭐'.repeat(memory.significance || 0)}
                    </p>
                </div>
                {/* Edit/Delete Buttons */}
                <div>
                    <button onClick={handleEditClick} style={editButtonStyle} title="Edit Memory">Edit</button>
                    <button onClick={handleDeleteClick} style={deleteButtonStyle} title="Delete Memory">Delete</button>
                </div>
            </div>

            <p style={{ whiteSpace: 'pre-wrap', marginTop: '10px' }}>{memory.description || 'No description.'}</p>

            {/* Tags */}
            {memory.tags && memory.tags.length > 0 && (
                <div style={{ marginTop: '10px' }}>
                    <strong>Tags:</strong>
                    {memory.tags.map((tag, index) => (
                        <span key={index} style={tagStyle}>{tag}</span>
                    ))}
                </div>
            )}

            {/* Attachments */}
            {memory.attachments && memory.attachments.length > 0 && (
                <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px dashed #eee' }}>
                    <strong>Attachments:</strong>
                    <ul style={attachmentListStyle}>
                        {memory.attachments.map((att, index) => (
                            <li key={index} style={attachmentItemStyle}>
                                {att.url && isImage(att.filename || '') ? (
                                    // Display image thumbnail if it's an image
                                    <a href={att.url} target="_blank" rel="noopener noreferrer" title={`View ${att.filename}`}>
                                        <img src={att.url} alt={att.filename || 'Attachment'} style={attachmentImageStyle} />
                                    </a>
                                ) : (
                                    // Link for non-image files
                                    <a href={att.url || '#'} target="_blank" rel="noopener noreferrer" style={attachmentLinkStyle}>
                                        {att.filename || 'Unnamed File'}
                                    </a>
                                )}
                                {att.size && ` (${Math.round(att.size / 1024)} KB)`}
                             </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

export default MemoryCard;