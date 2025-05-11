import React from 'react';
import PropTypes from 'prop-types';
import './MemoryCard.css';

// Helper to format date
const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
        return new Date(dateString).toLocaleDateString(undefined, {
            year: 'numeric', month: 'short', day: 'numeric'
        });
    } catch (e) {
        return "Invalid Date";
    }
};

// Check if attachment URL points to an image
const isImageUrl = (url) => {
    if (typeof url !== 'string') return false;
    return /\.(jpe?g|png|gif|webp|svg)$/i.test(url);
};

// Truncate text with ellipsis
const truncateText = (text, maxLength) => {
    if (!text) return '';
    return text.length > maxLength ? `${text.substring(0, maxLength - 3)}...` : text;
};

function MemoryCard({ memory, onDelete, onEdit }) {
    // Handle missing memory data
    if (!memory || !memory.id) {
        return (
            <div className="memory-card memory-card-error">
                <p>Memory data is unavailable.</p>
            </div>
        );
    }

    const {
        id, title, description, significance, tags, attachments, created_at,
    } = memory;

    const handleDeleteClick = (e) => {
        e.stopPropagation();
        if (id && window.confirm(`Are you sure you want to delete "${title || 'this memory'}"?`)) {
            onDelete(id);
        }
    };

    const handleEditClick = (e) => {
        e.stopPropagation();
        if (memory && memory.id) {
            onEdit(memory);
        }
    };

    const hasTags = tags && Array.isArray(tags) && tags.length > 0;
    const hasAttachments = attachments && Array.isArray(attachments) && attachments.length > 0;

    return (
        <div className="memory-card">
            <div className="memory-card-content">
                <div className="memory-card-header">
                    <h3 className="memory-card-title">{title || "Untitled Memory"}</h3>
                    {significance !== undefined && (
                        <div className="memory-card-significance" title={`Significance: ${significance}/5`}>
                            {Array.from({ length: 5 }, (_, i) => (
                                <span
                                    key={`star-${id}-${i}`}
                                    className={i < significance ? 'star-filled' : 'star-empty'}
                                >
                                    ★
                                </span>
                            ))}
                        </div>
                    )}
                </div>

                <p className="memory-card-description">
                    {description ? truncateText(description, 150) : <em>No description provided.</em>}
                </p>

                {hasTags && (
                    <div className="memory-card-tags">
                        {tags.map((tag, index) => (
                            <span key={`tag-${id}-${index}`} className="tag-chip">
                                {tag}
                            </span>
                        ))}
                    </div>
                )}

                {hasAttachments && (
                    <div className="memory-card-attachments">
                        <strong>Attachments:</strong>
                        <ul className="attachments-list">
                            {attachments.map((attachmentUrl, index) => {
                                const attachmentName = typeof attachmentUrl === 'string' 
                                    ? attachmentUrl.split('/').pop() 
                                    : `attachment-${index}`;
                                
                                return (
                                    <li key={`attachment-${id}-${index}`} className="attachment-list-item">
                                        {isImageUrl(attachmentUrl) ? (
                                            <a 
                                                href={attachmentUrl} 
                                                target="_blank" 
                                                rel="noopener noreferrer" 
                                                title={`View ${attachmentName}`}
                                            >
                                                <img 
                                                    src={attachmentUrl} 
                                                    alt={attachmentName || 'Attachment'} 
                                                    className="attachment-thumbnail" 
                                                />
                                            </a>
                                        ) : (
                                            <a 
                                                href={attachmentUrl || '#'} 
                                                target="_blank" 
                                                rel="noopener noreferrer" 
                                                className="attachment-link"
                                            >
                                                {attachmentName}
                                            </a>
                                        )}
                                    </li>
                                );
                            })}
                        </ul>
                    </div>
                )}
            </div>

            <div className="memory-card-footer">
                <small className="memory-card-date">
                    Created: {formatDate(created_at)}
                </small>
                <div className="memory-card-actions">
                    <button onClick={handleEditClick} className="button-edit">Edit</button>
                    <button onClick={handleDeleteClick} className="button-delete">Delete</button>
                </div>
            </div>
        </div>
    );
}

MemoryCard.propTypes = {
    memory: PropTypes.shape({
        id: PropTypes.string.isRequired,
        title: PropTypes.string,
        description: PropTypes.string,
        significance: PropTypes.number,
        tags: PropTypes.arrayOf(PropTypes.string),
        attachments: PropTypes.arrayOf(PropTypes.string),
        created_at: PropTypes.string,
    }).isRequired,
    onDelete: PropTypes.func.isRequired,
    onEdit: PropTypes.func.isRequired,
};

export default MemoryCard;