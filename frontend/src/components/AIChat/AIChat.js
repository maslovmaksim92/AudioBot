import React, { useEffect, useRef, useState } from 'react';
import './AIChat.css';

const BACKEND_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.REACT_APP_BACKEND_URL) || process.env.REACT_APP_BACKEND_URL;

const AIChat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [debugMode, setDebugMode] = useState(false);
  const messagesEndRef = useRef(null);
  // Используем первого пользователя из БД (Маслов Максим)
  const userId = '7be8f89e-f2bd-4f24-9798-286fddc58358';

  // Автоскролл вниз при новых сообщениях
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Загрузка истории чата при монтировании
  useEffect(() => {
    loadChatHistory();
  }, []);

  const loadChatHistory = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/ai/history?user_id=${userId}&limit=50`);
      if (res.ok) {
        const data = await res.json();
        const formattedMessages = data.messages.map(msg => ({
          role: msg.role,
          text: msg.content,
          timestamp: new Date(msg.created_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
        }));
        setMessages(formattedMessages);
      }
    } catch (e) {
      console.error('Error loading chat history:', e);
    } finally {
      setHistoryLoading(false);
    }
  };

  const send = async () => {
    const q = input.trim();
    if (!q) return;

    const userMessage = {
      role: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Используем новый endpoint для AI чата с GPT-5
      const res = await fetch(`${BACKEND_URL}/api/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: q,
          user_id: userId
        })
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data = await res.json();
      const text = data.message || 'Нет ответа.';
      
      const assistantMessage = {
        role: 'assistant',
        text,
        timestamp: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }),
        function_calls: data.function_calls || []
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (e) {
      console.error('AI Chat error:', e);
      const errorMessage = {
        role: 'assistant',
        text: `Ошибка ответа: ${e.message}. Попробуйте ещё раз.`,
        timestamp: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="ai-chat-container">
      <div className="ai-chat-header">
        <h1 className="ai-chat-title">🤖 AI Помощник VasDom</h1>
        <p className="ai-chat-subtitle">
          Задайте вопрос о домах, графиках уборки, контактах и прайс-листах
        </p>
      </div>

      <div className="ai-chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">💬</div>
            <div className="empty-state-text">Начните диалог с AI помощником</div>
            <div className="empty-state-subtext">
              Примеры: "Когда уборка Билибина 6?", "Контакты старшего Кубяка 5"
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`ai-chat-message ${m.role}`}>
            <div className={`message-avatar ${m.role}`}>
              {m.role === 'user' ? '👤' : '🤖'}
            </div>
            <div>
              <div className={`message-bubble ${m.role}`}>
                {m.text}
              </div>
              <div className="message-time">{m.timestamp}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="ai-chat-message assistant">
            <div className="message-avatar assistant">🤖</div>
            <div className="message-bubble assistant">
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="ai-chat-input-container">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Напишите сообщение..."
          className="ai-chat-input"
        />
        <button 
          onClick={send} 
          disabled={loading || !input.trim()} 
          className="ai-chat-send-btn"
        >
          {loading ? '⏳' : '📤'} {loading ? 'Загрузка...' : 'Отправить'}
        </button>
      </div>
    </div>
  );
};

export default AIChat;