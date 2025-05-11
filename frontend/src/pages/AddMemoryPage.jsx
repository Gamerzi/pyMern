// frontend/src/pages/AddMemoryPage.jsx
// This code includes the necessary frontend fixes.
// Errors are likely originating from the backend or apiService.js.

import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { createMemory } from '../services/apiService'; // Ensure this service is correct
import './AddMemoryPage.css'; // Styles remain unchanged

function AddMemoryPage() {
    const navigate = useNavigate();
    // --- State Variables (Unchanged) ---
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [significance, setSignificance] = useState(3);
    const [tags, setTags] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [files, setFiles] = useState([]);
    const [previewUrls, setPreviewUrls] = useState([]);
    const fileInputRef = useRef(null);
    // -----------------------------

    // handleFileChange and removeFile remain unchanged
    const handleFileChange = (e) => {
        const selectedFiles = Array.from(e.target.files);
        setFiles(prevFiles => [...prevFiles, ...selectedFiles]);
        const newPreviewUrls = selectedFiles.map(file => {
            if (file.type.startsWith('image/')) {
                return URL.createObjectURL(file);
            }
            return null;
        });
        setPreviewUrls(prevUrls => [...prevUrls, ...newPreviewUrls]);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const removeFile = (index) => {
        const updatedFiles = [...files];
        const updatedPreviews = [...previewUrls];
        if (updatedPreviews[index]) {
            URL.revokeObjectURL(updatedPreviews[index]);
        }
        updatedFiles.splice(index, 1);
        updatedPreviews.splice(index, 1);
        setFiles(updatedFiles);
        setPreviewUrls(updatedPreviews);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        console.log("--- Add Memory Submit Triggered ---");
        setError('');
        setLoading(true);

        try {
            console.log("1. Creating FormData...");
            const formData = new FormData();
            formData.append('title', title);
            formData.append('description', description);
            formData.append('significance', String(significance)); // Send as string

            const tagsList = tags.split(',').map(tag => tag.trim()).filter(tag => tag !== '');
            const tagsJsonString = JSON.stringify(tagsList);
            formData.append('tags', tagsJsonString); // Send tags as JSON string

            console.log(" appending tags:", tagsJsonString);

            // Append files correctly
            if (files && files.length > 0) {
                console.log(`2. Appending ${files.length} files under key 'files'...`);
                files.forEach((file, index) => {
                    formData.append('files', file); // Key MUST match backend (e.g., files: List[UploadFile]...)
                    console.log(`   - Appended file ${index}: ${file.name}`);
                });
            } else {
                console.log("2. No files selected to append.");
            }

            // Optional: Log FormData entries for verification (files won't show content)
            console.log("3. FormData Content (Keys & Values):");
            for (let [key, value] of formData.entries()) {
                console.log(`   ${key}:`, value instanceof File ? `File(${value.name}, ${value.size} bytes)` : value);
            }

            console.log("4. Calling createMemory API...");
            // Ensure apiService.js->createMemory sets 'Content-Type': 'multipart/form-data'
            const createdMemory = await createMemory(formData);
            console.log("5. API Call Successful:", createdMemory); // Log success response

            console.log("6. Navigating to /memories...");
            navigate('/memories', { replace: true }); // Navigate on success

        } catch (err) {
            console.error("--- ERROR During Memory Creation ---");
            console.error("Error object:", err);
            // Log details from Axios error response if available
            if (err.response) {
                console.error("Error Response Status:", err.response.status);
                console.error("Error Response Data:", err.response.data);
            } else {
                console.error("Error Message:", err.message);
            }

            // Extract and set user-friendly error message
            let detailedError = "Failed to save memory. Check console for details.";
            if (err.response?.data?.detail) {
                 if (Array.isArray(err.response.data.detail)) {
                     detailedError = err.response.data.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join('; ');
                 } else if (typeof err.response.data.detail === 'string') {
                     detailedError = err.response.data.detail;
                 }
                 console.error("Detailed Backend Error:", detailedError);
            } else if (err.message) {
                detailedError = err.message;
            }

            setError(detailedError); // Update the UI with the error message
            setLoading(false); // Ensure loading is stopped on error
            console.log("--------------------------------------");
        }
         // Removed finally block as setLoading(false) is in catch
    };

    // --- JSX Structure (Unchanged - Assuming class names are correct for styling) ---
    return (
        <div className="add-memory-page">
            <div className="add-memory-container">
                <h2 className="add-memory-header">Add New Memory</h2>
                <form onSubmit={handleSubmit} className="add-memory-form">
                    {/* Input Group: Title */}
                    <div className="input-group">
                        <label htmlFor="title">Title:</label>
                        <input type="text" id="title" value={title} onChange={e => setTitle(e.target.value)} required disabled={loading} placeholder="Enter memory title" />
                    </div>
                    {/* Input Group: Description */}
                    <div className="input-group">
                        <label htmlFor="description">Description:</label>
                        <textarea id="description" value={description} onChange={e => setDescription(e.target.value)} required disabled={loading} placeholder="Describe your memory" />
                    </div>
                    {/* Input Group: Significance */}
                    <div className="input-group">
                        <label htmlFor="significance">Significance (1-5):</label>
                        <div className="significance-slider-container">
                             <input type="range" id="significance" value={significance} onChange={e => setSignificance(e.target.value)} required min="1" max="5" step="1" disabled={loading} className="significance-slider" />
                            <div className="significance-value">{significance}</div>
                        </div>
                    </div>
                    {/* Input Group: Tags */}
                    <div className="input-group">
                        <label htmlFor="tags">Tags (comma-separated):</label>
                        <input type="text" id="tags" value={tags} onChange={e => setTags(e.target.value)} disabled={loading} placeholder="family, achievement, learning, etc." />
                    </div>
                    {/* Input Group: File Upload */}
                    <div className="input-group file-upload-group">
                        <label>Upload Files (Optional):</label>
                        <div className="file-upload-container">
                            <button type="button" className="file-upload-button secondary-button" onClick={() => fileInputRef.current?.click()} disabled={loading}> Choose Files </button>
                            <input type="file" ref={fileInputRef} onChange={handleFileChange} multiple style={{ display: 'none' }} disabled={loading} accept="image/*,application/pdf,.doc,.docx,.txt" />
                            <span className="file-upload-info"> {files.length > 0 ? `${files.length} file(s) selected` : 'No files selected'} </span>
                        </div>
                        {/* Image Previews */}
                        {previewUrls.length > 0 && (
                            <div className="file-previews">
                                {previewUrls.map((url, index) => ( url && ( <div key={`preview-${index}`} className="file-preview-item"> <img src={url} alt={`Preview ${index + 1}`} /> <button type="button" className="remove-file-button" title="Remove this file" onClick={() => removeFile(index)} disabled={loading}> × </button> </div> )))}
                            </div>
                        )}
                        {/* Non-Image File List */}
                        <div className="file-list">
                             {files.map((file, index) => ( !file.type.startsWith('image/') && ( <div key={`file-${index}`} className="file-list-item"> <span className="file-list-name">{file.name}</span> ({Math.round(file.size / 1024)} KB) <button type="button" className="remove-file-button" title="Remove this file" onClick={() => removeFile(index)} disabled={loading}> × </button> </div> )))}
                        </div>
                    </div>
                    {/* Error Message Display */}
                    {error && <div className="error-message">{error}</div>}
                    {/* Form Action Buttons */}
                    <div className="button-container">
                        <button type="submit" disabled={loading} className="primary-button"> {loading ? 'Saving...' : 'Save Memory'} </button>
                        <button type="button" onClick={() => navigate('/memories')} className="secondary-button" disabled={loading}> Cancel </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default AddMemoryPage;