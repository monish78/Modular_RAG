import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, User, Shield, Info, Bot, Sparkles } from 'lucide-react';
import './App.css';

const App = () => {
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Hello! I am your RAG Assistant. Please enter your username and ask me anything.', timestamp: new Date() }
  ]);
  const [input, setInput] = useState('');
  const [username, setUsername] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [strategy, setStrategy] = useState('strategy1');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || !username.trim()) {
      if (!username.trim()) alert("Please enter a username first.");
      return;
    }

    const userMessage = { role: 'user', content: input, username: username, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    const port = strategy === 'strategy1' ? 8000 : 8001;
    const url = `http://localhost:${port}/query`;

    try {
      const response = await axios.post(url, {
        user_name: username,
        user_prompt: input
      });

      const botMessage = {
        role: 'bot',
        content: response.data.response,
        sources: response.data.sources || [],
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error("Error fetching response:", error);
      setMessages(prev => [...prev, {
        role: 'bot',
        content: "Error: Could not connect to the backend server. Make sure " + (strategy === 'strategy1' ? "Strategy 1" : "Strategy 2") + " is running on port " + port + ".",
        timestamp: new Date(),
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="chatbot-wrapper">
        <header className="header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={24} color="#6366f1" />
            <h1>Modular RAG</h1>
          </div>
          <div className="user-config">
            <div className="strategy-selector">
              <button 
                className={`strategy-btn ${strategy === 'strategy1' ? 'active' : ''}`}
                onClick={() => setStrategy('strategy1')}
              >
                Strategy 1
              </button>
              <button 
                className={`strategy-btn ${strategy === 'strategy2' ? 'active' : ''}`}
                onClick={() => setStrategy('strategy2')}
              >
                Strategy 2
              </button>
            </div>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <User size={16} style={{ position: 'absolute', left: '12px', color: '#94a3b8' }} />
              <input
                type="text"
                className="input-field"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={{ paddingLeft: '2.4rem', width: '150px' }}
              />
            </div>
          </div>
        </header>

        <main className="messages-container">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-info">
                {msg.role === 'user' ? (
                  <><User size={12} /> {msg.username}</>
                ) : (
                  <><Bot size={12} /> AI Assistant</>
                )}
                <span style={{ marginLeft: '8px' }}>
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <div className="content">{msg.content}</div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources">
                  <strong>Sources:</strong> {msg.sources.join(', ')}
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="message bot">
              <div className="message-info"><Bot size={12} /> AI Assistant thinking...</div>
              <div className="typing">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </main>

        <footer className="input-area">
          <input
            type="text"
            className="input-field message-input"
            placeholder="Type your message here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            disabled={isLoading}
          />
          <button 
            className="send-button" 
            onClick={handleSend}
            disabled={isLoading || !input.trim() || !username.trim()}
          >
            <Send size={18} />
            Send
          </button>
        </footer>
      </div>
    </div>
  );
};

export default App;
