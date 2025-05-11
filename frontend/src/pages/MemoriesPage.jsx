import React, { useState, useEffect, useCallback } from 'react';
import { getMemories, deleteMemory as apiDeleteMemory, updateMemory as apiUpdateMemory, createMemory as apiCreateMemory } from '../services/apiService';
import MemoryCard from '../components/MemoryCard';
import MemoryFormModal from '../components/MemoryFormModal';
import './MemoriesPage.css'; // Import the new styles

// Placeholder for icons (replace with actual SVG components or library)
const IconPlaceholder = ({ text, className }) => <span className={className}>[{text}]</span>;


function MemoriesPage() {
    const [memories, setMemories] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editingMemory, setEditingMemory] = useState(null); // For editing or creating new
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [isEditMode, setIsEditMode] = useState(false); // To distinguish between create and edit

    const fetchAndSetMemories = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const fetchedData = await getMemories();
            if (Array.isArray(fetchedData)) {
                const transformedMemories = fetchedData.map(mem => {
                    if (mem && mem._id && mem.id === undefined) {
                        return { ...mem, id: mem._id };
                    }
                    if (mem && mem.id !== undefined) {
                        return mem;
                    }
                    return null;
                }).filter(mem => mem !== null);
                setMemories(transformedMemories);
            } else {
                setMemories([]);
            }
        } catch (err) {
            setError(err.message || "Failed to load memories.");
            setMemories([]);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAndSetMemories();
    }, [fetchAndSetMemories]);

    const handleDelete = async (memoryId) => {
        if (!memoryId) return;
        try {
            await apiDeleteMemory(memoryId);
            fetchAndSetMemories();
        } catch (err) {
            setError(err.message || "Failed to delete memory.");
        }
    };

    const handleOpenCreateForm = () => {
        setIsEditMode(false);
        setEditingMemory(null); // Clear any previous editing memory
        setIsFormOpen(true);
    };

    const handleEdit = (memory) => {
        if (memory && memory.id !== undefined) {
            setIsEditMode(true);
            setEditingMemory(memory);
            setIsFormOpen(true);
        } else {
            setError("Cannot edit memory: data is incomplete.");
        }
    };

    const handleFormSave = async (memoryData, isCreatingNew, files) => {
        try {
            if (isCreatingNew) {
                // Create FormData for new memory with files
                const formData = new FormData();
                formData.append('title', memoryData.title);
                formData.append('description', memoryData.description);
                formData.append('significance', memoryData.significance.toString());
                formData.append('tags_json', JSON.stringify(memoryData.tags || []));
                if (files && files.length > 0) {
                    for (let i = 0; i < files.length; i++) {
                        formData.append('files', files[i]);
                    }
                }
                await apiCreateMemory(formData);
            } else if (editingMemory && editingMemory.id) {
                // For updates, send JSON. File updates would be a separate mechanism.
                const payload = {
                    title: memoryData.title,
                    description: memoryData.description,
                    significance: parseInt(memoryData.significance, 10),
                    tags: memoryData.tags || [],
                };
                await apiUpdateMemory(editingMemory.id, payload);
            }
            fetchAndSetMemories();
            setIsFormOpen(false);
            setEditingMemory(null);
        } catch (err) {
            setError(err.message || `Failed to ${isCreatingNew ? 'create' : 'update'} memory.`);
            // Keep form open on error for correction
        }
    };

    const handleFormClose = () => {
        setIsFormOpen(false);
        setEditingMemory(null);
        setError(null); // Clear form-specific errors on close
    };

    return (
        <div className="memories-container">
            <div className="color-blob color-blob-1"></div>
            <div className="color-blob color-blob-2"></div>

            <div className="memories-content">
                <h1 className="memories-title">Your Digital Memories</h1>

                <div className="add-memory-button-container" style={{ marginBottom: '2rem', textAlign: 'center' }}>
                    <button onClick={handleOpenCreateForm} className="primary-button">
                        Add New Memory
                    </button>
                </div>
                
                {isFormOpen && (
                    <MemoryFormModal
                        memoryToEdit={editingMemory}
                        onClose={handleFormClose}
                        onSave={handleFormSave}
                        isEditMode={isEditMode}
                        // Pass existing error to modal if you want to display it there
                        // formError={error}
                    />
                )}

                {isLoading && (
                    <div className="loading-container">
                        <div className="loading-spinner"></div>
                        Loading your memories...
                    </div>
                )}

                {!isLoading && error && !isFormOpen && ( // Display general page error if form is not open
                    <div className="error-message" style={{marginBottom: '2rem'}}>
                        <IconPlaceholder text="!" className="error-icon" />
                        <p>{error}</p>
                    </div>
                )}


                {!isLoading && !error && memories.length === 0 && (
                    <div className="empty-state glass-card">
                        <IconPlaceholder text="o_o" className="empty-icon" />
                        <h2>No Memories Yet</h2>
                        <p>Looks like your memory bank is empty. Click "Add New Memory" to start your collection!</p>
                    </div>
                )}

                {!isLoading && memories.length > 0 && (
                    <div className="memory-grid">
                        {memories.map((memory) => {
                            if (!memory || memory.id === undefined) {
                                console.error("MemoriesPage: Skipping rendering of MemoryCard due to missing memory or id", memory);
                                return null;
                            }
                            return (
                                <MemoryCard
                                    key={memory.id}
                                    memory={memory}
                                    onDelete={handleDelete}
                                    onEdit={handleEdit}
                                />
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}

export default MemoriesPage;