// frontend/src/pages/MemoriesPage.jsx
import React, { useState, useEffect } from 'react';
// --- FIXED: Ensure uploadMemoryAttachment is imported ---
import {
    getMemories,
    createMemory,
    uploadMemoryAttachment, // Make sure it's listed here
    deleteMemory,
    updateMemory
} from '../services/apiService';
// --------------------------------------------------------
import MemoryCard from '../components/MemoryCard';

// --- Main Page Component ---
function MemoriesPage() {
    // --- State Variables for the Page ---
    const [memories, setMemories] = useState([]);
    const [loading, setLoading] = useState(true); // Loading state for fetching memories
    const [error, setError] = useState('');     // Error state for fetching/operations
    const [editingMemory, setEditingMemory] = useState(null); // Stores the memory being edited, or null
    // -----------------------------------

    // --- Fetch memories on component mount ---
    useEffect(() => {
        const fetchMemories = async () => {
            setLoading(true);
            setError('');
            try {
                console.log("Fetching memories...");
                const data = await getMemories();
                setMemories(data || []);
                console.log("Memories fetched:", data);
            } catch (err) {
                const errorMsg = err.message || 'Failed to fetch memories.';
                setError(errorMsg);
                console.error("Fetch memories error:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchMemories();
    }, []);
    // --------------------------------------

    // --- Handlers for Edit/Delete ---
    const handleDeleteMemory = async (memoryId) => {
        try {
            setError('');
            await deleteMemory(memoryId);
            setMemories(prev => prev.filter(mem => mem.id !== memoryId));
            console.log("Memory deleted:", memoryId);
        } catch (err) {
            setError(`Failed to delete memory: ${err.message || 'Unknown error'}`);
            console.error("Delete memory error:", err);
        }
    };

    const handleEditMemory = (memory) => {
        console.log("Setting memory to edit:", memory);
        setError('');
        setEditingMemory(memory);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const handleCancelEdit = () => {
        console.log("Cancelling edit.");
        setEditingMemory(null);
        setError('');
    };
    // -----------------------------

    // --- JSX Returned by MemoriesPage ---
    return (
        <div>
            <h2>Your Memories</h2>

            <AddEditMemoryForm
                key={editingMemory ? editingMemory.id : 'add'}
                existingMemory={editingMemory}
                onMemoryAdded={(newMemory) => {
                    setMemories(prev => [newMemory, ...prev]);
                    setEditingMemory(null);
                }}
                onMemoryUpdated={(updatedMemory) => {
                    setMemories(prev => prev.map(mem =>
                        mem.id === updatedMemory.id ? updatedMemory : mem
                    ));
                    setEditingMemory(null);
                }}
                onCancelEdit={handleCancelEdit}
            />
            <hr style={{ margin: '20px 0', borderColor: 'var(--border-light, #dee2e6)' }} />

            {loading && <p>Loading memories...</p>}
            {error && !loading && <p style={{ color: 'red' }}>Error: {error}</p>}
            {!loading && !error && memories.length === 0 && <p>You haven't saved any memories yet. Use the form above to add one!</p>}
            {!loading && !error && memories.length > 0 && (
                <div className="memory-list">
                    {memories.map((memory) => (
                        <MemoryCard
                            key={memory.id}
                            memory={memory}
                            onDelete={handleDeleteMemory}
                            onEdit={handleEditMemory}
                        />
                    ))}
                </div>
            )}
        </div>
    );
} // --- End of MemoriesPage Component ---


// =============================================
// --- Add/Edit Memory Form Component ---
// =============================================
function AddEditMemoryForm({ existingMemory, onMemoryAdded, onMemoryUpdated, onCancelEdit }) {
    // --- State FOR THE FORM ---
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [significance, setSignificance] = useState(3);
    const [tags, setTags] = useState('');
    const [attachment, setAttachment] = useState(null);
    const [formError, setFormError] = useState('');
    const [formLoading, setFormLoading] = useState(false);
    // -------------------------

    const isEditing = Boolean(existingMemory);

    // --- Effect to Populate form ---
    useEffect(() => {
        console.log('AddEditMemoryForm effect running. isEditing:', isEditing, 'existingMemory:', existingMemory);
        if (isEditing && existingMemory) {
            setTitle(existingMemory.title || '');
            setDescription(existingMemory.description || '');
            setSignificance(existingMemory.significance || 3);
            setTags((existingMemory.tags || []).join(', '));
            setAttachment(null);
            setFormError('');
        } else {
            setTitle('');
            setDescription('');
            setSignificance(3);
            setTags('');
            setAttachment(null);
            setFormError('');
        }
    }, [existingMemory, isEditing]);
    // -----------------------------

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setAttachment(e.target.files[0]);
        } else {
            setAttachment(null);
        }
    };

    // --- Form Submission Logic ---
    const handleSubmit = async (e) => {
        e.preventDefault();
        setFormError('');
        setFormLoading(true);

        const memoryDetails = {
            title,
            description,
            significance: Number(significance),
            tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag),
        };

        try {
            if (isEditing) {
                // --- UPDATE ---
                const updatedData = {};
                if (title !== existingMemory.title) updatedData.title = title;
                if (description !== existingMemory.description) updatedData.description = description;
                if (Number(significance) !== existingMemory.significance) updatedData.significance = Number(significance);
                updatedData.tags = memoryDetails.tags;

                let memoryAfterUpdate = existingMemory;
                if (Object.keys(updatedData).length > 0) {
                    memoryAfterUpdate = await updateMemory(existingMemory.id, updatedData);
                } else { console.log("No textual changes detected for update."); }

                if (attachment) {
                    console.warn("Attachment upload during edit is not fully implemented. Simulating placeholder.");
                    alert("Attachment upload during edit simulated! Backend endpoint needed.");
                    // Placeholder for future: upload logic and potentially updating memoryAfterUpdate
                }
                onMemoryUpdated(memoryAfterUpdate);

            } else {
                // --- CREATE ---
                const newMemory = await createMemory(memoryDetails);
                let finalMemory = newMemory;
                if (attachment && newMemory?.id) {
                    try {
                        console.log(`Uploading ${attachment.name} for new memory ${newMemory.id}`);
                        alert("Attachment upload simulated! Backend endpoint needed."); // Placeholder
                        // const uploadResult = await uploadMemoryAttachment(newMemory.id, attachment);
                        // finalMemory = uploadResult;
                    } catch (uploadError) {
                        setFormError(`Memory created, but attachment upload failed: ${uploadError.message}`);
                    }
                }
                onMemoryAdded(finalMemory);
                // Reset form fields only after successful ADDITION
                 setTitle(''); setDescription(''); setSignificance(3); setTags(''); setAttachment(null);
                 const fileInput = e.target.elements.namedItem("fileInput");
                 if (fileInput) fileInput.value = null;
            }
        } catch (err) {
            setFormError(err.detail || err.message || `Failed to ${isEditing ? 'update' : 'add'} memory`);
            console.error("Form submission error:", err);
        } finally {
            setFormLoading(false);
        }
    };
    // --------------------------

     // --- Basic Form Styling ---
     const formStyle = { border: '1px solid var(--border-light, #dee2e6)', padding: '15px', borderRadius: '8px', marginBottom: '20px', backgroundColor: 'var(--card-bg-light, #fff)'};
     const inputGroup = { marginBottom: '1rem'};
     const labelStyle = { display: 'block', marginBottom: '0.3rem', fontWeight: '500', fontSize: '0.9em', color: 'var(--text-light)' };
     // --------------------------

    return (
        <form onSubmit={handleSubmit} style={formStyle} name="addEditMemoryForm">
            <h3>{isEditing ? 'Edit Memory' : 'Add New Memory'}</h3>
             <div style={inputGroup}>
                <label htmlFor="title" style={labelStyle}>Title:</label>
                <input type="text" id="title" value={title} onChange={e => setTitle(e.target.value)} required disabled={formLoading} />
             </div>
              <div style={inputGroup}>
                <label htmlFor="description" style={labelStyle}>Description:</label>
                <textarea id="description" value={description} onChange={e => setDescription(e.target.value)} required disabled={formLoading} rows={4}/>
             </div>
              <div style={inputGroup}>
                <label htmlFor="significance" style={labelStyle}>Significance (1-5):</label>
                <input type="number" id="significance" value={significance} onChange={e => setSignificance(e.target.value)} required min="1" max="5" disabled={formLoading}/>
             </div>
              <div style={inputGroup}>
                <label htmlFor="tags" style={labelStyle}>Tags (comma-separated):</label>
                <input type="text" id="tags" value={tags} onChange={e => setTags(e.target.value)} disabled={formLoading}/>
             </div>
             <div style={inputGroup}>
                <label htmlFor="attachment" style={labelStyle}>{isEditing ? 'Upload New Attachment (Optional):': 'Attachment (Optional):'}</label>
                <input type="file" id="attachment" name="fileInput" onChange={handleFileChange} disabled={formLoading} />
                {attachment && <span style={{ marginLeft: '10px', fontSize: '0.9em'}}>Selected: {attachment.name}</span>}
             </div>
             {formError && <p style={{ color: 'red', fontSize: '0.9em', marginTop: '10px' }}>Error: {formError}</p>}
            <button type="submit" disabled={formLoading}>
                 {formLoading ? (isEditing ? 'Updating...' : 'Adding...') : (isEditing ? 'Update Memory' : 'Add Memory')}
            </button>
            {isEditing && (
                <button type="button" onClick={onCancelEdit} style={{ marginLeft: '10px', backgroundColor: '#6c757d', color: 'white', borderColor: '#6c757d' }} disabled={formLoading}>
                    Cancel Edit
                </button>
            )}
        </form>
    );
} // --- End of AddEditMemoryForm ---

export default MemoriesPage;