import React, { useState, useEffect, useRef } from 'react';
import { startConversation, sendMessage } from '../services/apiService';
import './ConversationPage.css'; // Import the CSS file

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
            setMessages(updatedConversation.messages);
        } catch (err) {
            setError(err.detail || err.message || 'Failed to send message. Please try again.');
            // Optional: remove the optimistic user message if sending failed
            setMessages(prevMessages => prevMessages.filter(msg => msg.id !== userMessage.id));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="chat-container">
            <div className="messages-area">
                {messages.length === 0 && !isLoading && (
                    <p className="empty-state">Ask your future self anything...</p>
                )}
                
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`message ${msg.role === 'user' ? 'message-user' : 'message-ai'}`}
                    >
                        {msg.content}
                        <div className="message-timestamp">
                            {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                    </div>
                ))}
                
                {isLoading && (
                    <div className="loading-indicator">Thinking...</div>
                )}
                
                {error && (
                    <p className="error-message">{error}</p>
                )}
                
                {/* Element to scroll to */}
                <div ref={messagesEndRef} />
            </div>
            
            <form onSubmit={handleSendMessage} className="input-area">
                <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type your message..."
                    disabled={isLoading}
                    className="message-input"
                />
                <button 
                    type="submit" 
                    disabled={isLoading} 
                    className="send-button"
                >
                    Send
                </button>
            </form>
        </div>
    );
}

export default ChatInterface;