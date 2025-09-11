import React, { useState, useEffect } from 'react';
import { Card, Button } from '../UI';

const AIChat = () => {
  const [message, setMessage] = useState('');
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://audiobot-qci2.onrender.com';

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = message;
    setMessage('');
    setLoading(true);

    // Add user message to conversation
    setConversations(prev => [...prev, { type: 'user', content: userMessage, timestamp: new Date() }]);

    try {
      const response = await fetch(`${BACKEND_URL}/api/voice/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: 'web-chat-session'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setConversations(prev => [...prev, { 
          type: 'ai', 
          content: data.response, 
          timestamp: new Date(),
          log_id: data.log_id,
          similar_found: data.similar_found
        }]);
      } else {
        throw new Error('Ошибка API');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setConversations(prev => [...prev, { 
        type: 'ai', 
        content: 'Извините, произошла ошибка при обработке вашего сообщения.', 
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Чат</h1>
          <p className="text-gray-600">Голосовой помощник VasDom</p>
        </div>
      </div>

      <Card className="h-96 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {conversations.length === 0 && (
            <div className="text-center text-gray-500">
              <p className="text-lg mb-2">🤖</p>
              <p>Привет! Я AI помощник VasDom.</p>
              <p className="text-sm">Задайте мне вопрос о клининге или управлении домами.</p>
            </div>
          )}
          
          {conversations.map((conv, index) => (
            <div key={index} className={`flex ${conv.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                conv.type === 'user' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-200 text-gray-900'
              }`}>
                <p className="text-sm">{conv.content}</p>
                {conv.similar_found > 0 && (
                  <p className="text-xs mt-1 opacity-75">
                    📚 Использован опыт из {conv.similar_found} похожих случаев
                  </p>
                )}
                <p className="text-xs mt-1 opacity-75">
                  {conv.timestamp.toLocaleTimeString('ru-RU')}
                </p>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-200 text-gray-900 px-4 py-2 rounded-lg max-w-xs">
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                  AI думает...
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="border-t p-4">
          <div className="flex space-x-2">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Введите ваш вопрос..."
              className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="2"
            />
            <Button
              onClick={sendMessage}
              disabled={loading || !message.trim()}
              loading={loading}
              variant="primary"
              className="self-end"
            >
              Отправить
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AIChat;