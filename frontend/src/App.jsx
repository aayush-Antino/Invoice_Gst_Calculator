import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Bot, Database, FileText, Zap, AlertCircle } from 'lucide-react';

const API_URL = '/api/query';

function App() {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(null); // 'invoice' or 'gst'
    const messagesEndRef = useRef(null);
    const invoiceInputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading('invoice');
        const formData = new FormData();
        formData.append('file', file);

        const endpoint = '/api/upload-invoice';

        try {
            const response = await axios.post(endpoint, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            const content = `Successfully uploaded invoice: ${response.data.data.invoice_id}`;

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: content,
                data: { query_type: 'SYSTEM', reasoning: 'Invoice Processed Successfully' }
            }]);
        } catch (error) {
            console.error("Upload Error:", error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                error: true,
                data: { reasoning: `Upload Failed: ${error.response?.data?.detail || error.message}` }
            }]);
        } finally {
            setUploading(null);
            e.target.value = null; // Reset input
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await axios.post(API_URL, { query: userMessage.content });
            const aiMessage = { role: 'assistant', data: response.data };
            setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
            console.error("Error:", error);
            const errorMessage = {
                role: 'assistant',
                error: true,
                data: { reasoning: "System Error. Please ensure backend is running." }
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app-container">
            <header className="header">
                <div className="header-brand">
                    <Bot className="text-accent" size={28} color="#eda435ff" />
                    <h1>GST & Invoice Intelligence</h1>
                </div>
                <div className="header-controls">
                    <input
                        type="file"
                        ref={invoiceInputRef}
                        onChange={(e) => handleFileUpload(e)}
                        style={{ display: 'none' }}
                        accept="image/*,.pdf"
                    />
                    <button
                        className="upload-btn"
                        onClick={() => invoiceInputRef.current.click()}
                        disabled={uploading === 'invoice'}
                    >
                        <Zap size={16} />
                        {uploading === 'invoice' ? 'Processing...' : 'Upload Invoice'}
                    </button>
                    {/* Placeholder for second button if needed, duplicate removed to be minimal */}
                </div>
            </header>

            <div className="chat-area">
                {messages.length === 0 && (
                    <div className="empty-state">
                        <Bot size={48} strokeWidth={1.5} style={{ marginBottom: '1rem', color: '#cbd5e1' }} />
                        <p>Ready to analyze invoices and GST rules.</p>
                        <p style={{ fontSize: '0.85rem', marginTop: '0.5rem', color: '#94a3b8' }}>
                            Try asking about tax totals or penalty rules.
                        </p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role === 'user' ? 'user' : 'ai'}`}>
                        <div className="message-bubble">
                            {msg.role === 'assistant' && !msg.error ? (
                                <ResultDisplay data={msg.data} />
                            ) : (
                                <p style={{ margin: 0 }}>{msg.content || msg.data?.reasoning}</p>
                            )}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="message ai">
                        <div className="message-bubble">
                            <div className="typing-dots">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
                <form onSubmit={handleSubmit} className="input-wrapper">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask a question..."
                        disabled={loading}
                    />
                    <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
                        <Send size={18} />
                    </button>
                </form>
            </div>
        </div>
    );
}

const ResultDisplay = ({ data }) => {
    const { query_type, reasoning, sql_query, rag_answer, hybrid_analysis, error } = data;

    const getIcon = () => {
        switch (query_type) {
            case 'STRUCTURED_QUERY': return <Database size={14} />;
            case 'UNSTRUCTURED_QUERY': return <FileText size={14} />;
            case 'HYBRID_QUERY': return <Zap size={14} />;
            default: return null;
        }
    };

    if (error) {
        return (
            <div className="result-content">
                <div className="tag-container">
                    <span className="tag ERROR">
                        <AlertCircle size={14} /> Error
                    </span>
                </div>
                <div className="reasoning-text" style={{ color: 'var(--error-text)' }}>
                    {error}
                </div>
            </div>
        );
    }

    return (
        <div className="result-content">
            <div className="tag-container">
                <span className={`tag ${query_type}`}>
                    {getIcon()} {query_type?.replace('_', ' ')}
                </span>
            </div>

            {reasoning && (
                <div className="reasoning-text">
                    {reasoning}
                </div>
            )}

            {query_type === 'STRUCTURED_QUERY' && (
                <>
                    {data.structured_answer && (
                        <div className="answer-box">
                            <div className="answer-label">Answer</div>
                            <div className="answer-value">{data.structured_answer}</div>
                        </div>
                    )}

                    {sql_query && (
                        <div className="debug-box">
                            <div className="debug-label">SQL QUERY</div>
                            <div className="code-snippet">{sql_query}</div>
                        </div>
                    )}
                </>
            )}

            {query_type === 'UNSTRUCTURED_QUERY' && rag_answer && (
                <div className="prose">
                    <p>{rag_answer}</p>
                </div>
            )}

            {query_type === 'HYBRID_QUERY' && hybrid_analysis && (
                <div className="result-content">
                    {hybrid_analysis.sql_used && (
                        <div className="debug-box">
                            <div className="debug-label">STEP 1: SQL RETRIEVAL</div>
                            <div className="code-snippet">{hybrid_analysis.sql_used}</div>
                        </div>
                    )}

                    {hybrid_analysis.gst_rule_applied && (
                        <div className="debug-box">
                            <div className="debug-label">STEP 2: GST CONTEXT</div>
                            <div className="code-snippet" style={{ fontFamily: 'inherit' }}>{hybrid_analysis.gst_rule_applied}</div>
                        </div>
                    )}

                    <div className="answer-box" style={{ borderColor: 'var(--accent-secondary)' }}>
                        <div className="answer-label" style={{ color: 'var(--accent-primary)' }}>Final Analysis</div>
                        <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{hybrid_analysis.final_result}</p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default App;
