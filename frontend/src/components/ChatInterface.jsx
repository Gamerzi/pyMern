import React, { useState, useEffect, useRef } from 'react';
import { startConversation, sendMessage } from '../services/apiService';

function ChatInterface() {
    const [conversationId, setConversationId] = useState(null);
    const [messages, setMessages] = useState([]); // { id, role, content, timestamp }
    const [newMessage, setNewMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const messagesEndRef = useRef(null); // To auto-scroll

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]); // Scroll when messages change

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!newMessage.trim()) return; // Don't send empty messages

        const userMessage = {
            id: Date.now(), // Temporary ID for UI rendering
            role: 'user',
            content: newMessage,
            timestamp: new Date().toISOString(),
        };

        setMessages(prevMessages => [...prevMessages, userMessage]);
        setNewMessage('');
        setError('');
        setIsLoading(true);

        try {
            let updatedConversation;
            if (!conversationId) {
                // Start a new conversation
                updatedConversation = await startConversation(userMessage.content);
                setConversationId(updatedConversation.id);
            } else {
                // Send message to existing conversation
                updatedConversation = await sendMessage(conversationId, userMessage.content);
            }
            // Update messages state with the full list from the API response
            // This ensures we have the correct IDs and AI response
            setMessages(updatedConversation.messages);
        } catch (err) {
            setError(err.detail || err.message || 'Failed to send message. Please try again.');
            // Optional: remove the optimistic user message if sending failed
            setMessages(prevMessages => prevMessages.filter(msg => msg.id !== userMessage.id));
        } finally {
            setIsLoading(false);
        }
    };

    // Basic Styling
    const chatContainerStyle = {
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 200px)', // Adjust based on layout/navbar height
        border: '1px solid #ccc',
        borderRadius: '8px',
        overflow: 'hidden'
    };
    const messagesAreaStyle = {
        flexGrow: 1,
        overflowY: 'auto',
        padding: '15px',
        backgroundColor: '#f9f9f9'
    };
    const messageStyle = {
        marginBottom: '10px',
        padding: '8px 12px',
        borderRadius: '15px',
        maxWidth: '70%',
        wordWrap: 'break-word',
    };
    const userMessageStyle = {
        ...messageStyle,
        backgroundColor: '#dcf8c6',
        marginLeft: 'auto',
        borderBottomRightRadius: '5px',
    };
    const aiMessageStyle = {
        ...messageStyle,
        backgroundColor: '#fff',
        border: '1px solid #eee',
        marginRight: 'auto',
        borderBottomLeftRadius: '5px',
    };
     const inputAreaStyle = {
        display: 'flex',
        padding: '10px',
        borderTop: '1px solid #ccc'
     };
     const inputStyle = {
        flexGrow: 1,
        padding: '10px',
        border: '1px solid #ccc',
        borderRadius: '20px',
        marginRight: '10px'
     };
     const buttonStyle = {
        padding: '10px 15px',
        borderRadius: '20px',
        cursor: 'pointer',
        backgroundColor: '#007bff',
        color: 'white',
        border: 'none'
     };

    return (
        <div style={chatContainerStyle}>
            <div style={messagesAreaStyle}>
                {messages.length === 0 && !isLoading && <p>Ask your future self anything...</p>}
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        style={msg.role === 'user' ? userMessageStyle : aiMessageStyle}
                    >
                        {msg.content}
                    </div>
                ))}
                {isLoading && <div style={{ textAlign: 'center', padding: '10px' }}>Thinking...</div>}
                {error && <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>}
                {/* Element to scroll to */}
                <div ref={messagesEndRef} />
            </div>
            <form onSubmit={handleSendMessage} style={inputAreaStyle}>
                <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type your message..."
                    disabled={isLoading}
                    style={inputStyle}
                />
                <button type="submit" disabled={isLoading} style={buttonStyle}>
                    Send
                </button>
            </form>
        </div>
    );
}

export default ChatInterface;