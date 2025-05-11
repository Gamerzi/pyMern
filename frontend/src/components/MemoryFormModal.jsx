import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
// Removed direct import of MemoriesPage.css, modal will be styled by classes applied
// Its own CSS 'MemoryFormModal.css' (if you created one for modal-specific structure) would be fine too.

// Placeholder for icons
const IconPlaceholder = ({ text, className }) => <span className={className}>[{text}]</span>;

function MemoryFormModal({ memoryToEdit, onClose, onSave, isEditMode, formError }) {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [significance, setSignificance] = useState(3);
    const [tags, setTags] = useState('');
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [isSaving, setIsSaving] = useState(false);
    const [currentError, setCurrentError] = useState(null);

    const fileInputRef = useRef(null);

    useEffect(() => {
        setCurrentError(formError); // Update error if passed as prop
    }, [formError]);

    useEffect(() => {
        if (isEditMode && memoryToEdit) {
            setTitle(memoryToEdit.title || '');
            setDescription(memoryToEdit.description || '');
            setSignificance(memoryToEdit.significance !== undefined ? memoryToEdit.significance : 3);
            setTags(Array.isArray(memoryToEdit.tags) ? memoryToEdit.tags.join(', ') : '');
            setSelectedFiles([]); // File editing is not directly supported here, clear for edit mode
        } else {
            // Reset for new memory form
            setTitle('');
            setDescription('');
            setSignificance(3);
            setTags('');
            setSelectedFiles([]);
        }
        setCurrentError(null); // Clear errors when form data changes
    }, [memoryToEdit, isEditMode]);

    const handleFileChange = (e) => {
        setSelectedFiles(Array.from(e.target.files));
    };

    const triggerFileInput = () => {
        fileInputRef.current?.click();
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setCurrentError(null); // Clear previous errors
        setIsSaving(true);

        const tagsArray = tags.split(',').map(tag => tag.trim()).filter(tag => tag);
        const memoryData = {
            title,
            description,
            significance: parseInt(significance, 10),
            tags: tagsArray,
        };
        try {
            await onSave(memoryData, !isEditMode, selectedFiles); // Pass files only for create
            // onSave in parent will handle closing on success
        } catch (error) {
             // This catch might not be strictly necessary if onSave handles its own errors
             // and parent updates `formError` prop. But can be a fallback.
            setCurrentError(error.message || `Failed to ${!isEditMode ? 'create' : 'save'} memory.`);
        } finally {
            setIsSaving(false);
        }
    };

    // This modal structure uses fixed positioning for overlay
    // The content within `.modal-content-wrapper` will be the glass card
    return (
        <div className="modal-backdrop" onClick={onClose}> {/* Clicking backdrop closes modal */}
            <div className="modal-content-wrapper glass-card memory-form-card" onClick={e => e.stopPropagation()}> {/* Prevent backdrop click from closing when clicking on modal content */}
                <form onSubmit={handleSubmit} className="memory-form">
                    <h2 className="form-title">{isEditMode ? 'Edit Memory' : 'Create New Memory'}</h2>

                    {currentError && (
                        <div className="form-error">
                             <IconPlaceholder text="!" className="error-icon" />
                            <p>{currentError}</p>
                        </div>
                    )}

                    <div className="form-group">
                        <label htmlFor="title">Title:</label>
                        <input
                            type="text"
                            id="title"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="e.g., Trip to the Mountains"
                            required
                            disabled={isSaving}
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="description">Description:</label>
                        <textarea
                            id="description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Describe your memory..."
                            rows="4"
                            required
                            disabled={isSaving}
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="significance">Significance:</label>
                        <div className="significance-slider-container">
                            <input
                                type="range"
                                id="significance"
                                className="significance-slider"
                                value={significance}
                                onChange={(e) => setSignificance(parseInt(e.target.value, 10))}
                                min="1"
                                max="5"
                                step="1"
                                required
                                disabled={isSaving}
                            />
                            <span className="significance-value">{significance}</span>
                        </div>
                    </div>
                    <div className="form-group">
                        <label htmlFor="tags">Tags (comma-separated):</label>
                        <input
                            type="text"
                            id="tags"
                            value={tags}
                            onChange={(e) => setTags(e.target.value)}
                            placeholder="e.g., travel, fun, holiday"
                            disabled={isSaving}
                        />
                    </div>

                    {!isEditMode && ( // Only show file input for new memories
                        <div className="form-group">
                            <label>Attachments:</label>
                            <div className="file-input-wrapper">
                                <input
                                    type="file"
                                    id="attachments"
                                    className="file-input"
                                    ref={fileInputRef}
                                    onChange={handleFileChange}
                                    multiple
                                    disabled={isSaving}
                                />
                                <button type="button" onClick={triggerFileInput} className="file-input-button" disabled={isSaving}>
                                    <IconPlaceholder text="F" className="file-icon" />
                                    Choose Files
                                </button>
                                {selectedFiles.length > 0 && (
                                    <span className="file-name">
                                        {selectedFiles.length} file(s) selected: {selectedFiles.map(f => f.name).join(', ')}
                                    </span>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="form-actions">
                        <button type="button" onClick={onClose} className="secondary-button" disabled={isSaving}>
                            Cancel
                        </button>
                        <button type="submit" className="primary-button" disabled={isSaving}>
                            {isSaving ? (
                                <>
                                    <span className="button-spinner"></span>
                                    {isEditMode ? 'Saving...' : 'Creating...'}
                                </>
                            ) : (
                                isEditMode ? 'Save Changes' : 'Create Memory'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

MemoryFormModal.propTypes = {
    memoryToEdit: PropTypes.object,
    onClose: PropTypes.func.isRequired,
    onSave: PropTypes.func.isRequired,
    isEditMode: PropTypes.bool.isRequired,
    formError: PropTypes.string, // Optional error message from parent
};

export default MemoryFormModal;