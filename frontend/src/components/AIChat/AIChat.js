import React, { useEffect, useRef, useState } from 'react';
import './AIChat.css';

const BACKEND_URL = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.REACT_APP_BACKEND_URL) || process.env.REACT_APP_BACKEND_URL;

const AIChat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [debugMode, setDebugMode] = useState(false);
  const [expandedDebug, setExpandedDebug] = useState({}); // Track expanded debug for each message
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
          user_id: userId,
          debug: debugMode
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
        function_calls: data.function_calls || [],
        debug: data.debug || null,
        sources: data.sources || null,
        rule: data.rule || null
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

      <div className="ai-chat-admin-controls" style={{display:'flex',alignItems:'center',gap:8,margin:'8px 0 4px 0'}}>
        <label style={{display:'flex',alignItems:'center',gap:6,cursor:'pointer'}}>
          <input type="checkbox" checked={debugMode} onChange={(e)=>setDebugMode(e.target.checked)} />
          <span>Debug режим (правило/время/источник)</span>
        </label>
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
            <div style={{flex: 1}}>
              <div className={`message-bubble ${m.role}`}>
                {/* Основной текст с поддержкой переносов строк */}
                <div style={{whiteSpace: 'pre-wrap'}}>{m.text}</div>
                
                {/* Бейджи источников данных (только для assistant с debug данными) */}
                {m.role === 'assistant' && (m.sources || m.rule || m.debug) && (
                  <div style={{marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center'}}>
                    {/* Правило/резолвер */}
                    {m.rule && (
                      <span style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: 12,
                        background: '#e3f2fd',
                        color: '#1976d2',
                        fontWeight: 500
                      }}>
                        📋 {m.rule}
                      </span>
                    )}
                    
                    {/* Источник данных */}
                    {m.sources && Object.keys(m.sources).length > 0 && (
                      <>
                        {m.sources.elder?.cache === 'hit' || m.sources.houses?.cache === 'hit' || m.sources.finance?.cache === 'hit' ? (
                          <span style={{
                            fontSize: '11px',
                            padding: '2px 8px',
                            borderRadius: 12,
                            background: '#f3e5f5',
                            color: '#7b1fa2',
                            fontWeight: 500
                          }}>
                            ⚡ Кэш
                          </span>
                        ) : null}
                        
                        {m.sources.elder?.cache === 'miss' || m.sources.houses?.cache === 'miss' ? (
                          <span style={{
                            fontSize: '11px',
                            padding: '2px 8px',
                            borderRadius: 12,
                            background: '#fff3e0',
                            color: '#f57c00',
                            fontWeight: 500
                          }}>
                            🔗 Bitrix24
                          </span>
                        ) : null}
                        
                        {m.sources.db ? (
                          <span style={{
                            fontSize: '11px',
                            padding: '2px 8px',
                            borderRadius: 12,
                            background: '#e8f5e9',
                            color: '#388e3c',
                            fontWeight: 500
                          }}>
                            💾 База данных
                          </span>
                        ) : null}
                      </>
                    )}
                    
                    {/* Время выполнения */}
                    {m.debug?.elapsed_ms !== undefined && (
                      <span style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: 12,
                        background: '#fce4ec',
                        color: '#c2185b',
                        fontWeight: 500
                      }}>
                        ⏱️ {m.debug.elapsed_ms}ms
                      </span>
                    )}
                    
                    {/* Иконка раскрытия debug */}
                    {m.debug && (
                      <button
                        onClick={() => setExpandedDebug(prev => ({...prev, [i]: !prev[i]}))}
                        style={{
                          fontSize: '14px',
                          padding: '2px 6px',
                          borderRadius: 12,
                          background: 'transparent',
                          border: '1px solid #bdbdbd',
                          color: '#616161',
                          cursor: 'pointer',
                          transition: 'all 0.2s'
                        }}
                        title="Показать/скрыть debug информацию"
                      >
                        ℹ️
                      </button>
                    )}
                  </div>
                )}
                
                {/* Развёрнутая debug информация */}
                {m.role === 'assistant' && expandedDebug[i] && m.debug && (
                  <div style={{
                    marginTop: 12,
                    padding: 12,
                    background: '#f5f5f5',
                    borderRadius: 8,
                    fontSize: '12px',
                    fontFamily: 'monospace',
                    color: '#424242'
                  }}>
                    <div style={{fontWeight: 'bold', marginBottom: 8, color: '#1976d2'}}>
                      🔍 Debug информация:
                    </div>
                    
                    {/* Matched rule */}
                    {m.debug.matched_rule && (
                      <div style={{marginBottom: 4}}>
                        <strong>Правило:</strong> {m.debug.matched_rule}
                      </div>
                    )}
                    
                    {/* Elapsed time */}
                    {m.debug.elapsed_ms !== undefined && (
                      <div style={{marginBottom: 4}}>
                        <strong>Время:</strong> {m.debug.elapsed_ms}ms
                      </div>
                    )}
                    
                    {/* Sources */}
                    {m.sources && Object.keys(m.sources).length > 0 && (
                      <div style={{marginBottom: 4}}>
                        <strong>Источники:</strong>
                        <pre style={{
                          marginTop: 4,
                          padding: 8,
                          background: '#fff',
                          borderRadius: 4,
                          overflow: 'auto',
                          maxHeight: 200
                        }}>
                          {JSON.stringify(m.sources, null, 2)}
                        </pre>
                      </div>
                    )}
                    
                    {/* Trace */}
                    {m.debug.trace && m.debug.trace.length > 0 && (
                      <div>
                        <strong>Трейс:</strong>
                        <div style={{marginTop: 4}}>
                          {m.debug.trace.map((t, idx) => (
                            <div key={idx} style={{
                              padding: '4px 8px',
                              marginBottom: 2,
                              background: t.status === 'hit' ? '#e8f5e9' : '#ffebee',
                              borderRadius: 4
                            }}>
                              {t.rule} → {t.status} ({t.elapsed_ms}ms)
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
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