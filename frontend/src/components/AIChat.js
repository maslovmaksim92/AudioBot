import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AIChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/voice/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          session_id: `chat_${Date.now()}`
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const aiMessage = {
        id: Date.now() + 1,
        text: data.response || 'Извините, произошла ошибка при получении ответа.',
        sender: 'ai',
        timestamp: new Date(),
        log_id: data.log_id
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Извините, произошла ошибка при отправке сообщения. Проверьте подключение и попробуйте снова.',
        sender: 'ai',
        timestamp: new Date(),
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-sm border-b border-white/10 p-6">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
            <Bot className="text-white" size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">AI Чат</h1>
            <p className="text-gray-400">Интеллектуальный помощник для клининговой компании</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-12">
            <Bot size={48} className="mx-auto mb-4 opacity-50" />
            <p className="text-lg">Начните разговор с AI помощником</p>
            <p className="text-sm mt-2">Задайте любой вопрос о клининговых услугах</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl flex items-start space-x-3 ${
                message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.sender === 'user'
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                    : message.isError
                    ? 'bg-gradient-to-r from-red-500 to-pink-500'
                    : 'bg-gradient-to-r from-blue-500 to-purple-500'
                }`}
              >
                {message.sender === 'user' ? (
                  <User className="text-white" size={20} />
                ) : (
                  <Bot className="text-white" size={20} />
                )}
              </div>

              <div
                className={`px-6 py-4 rounded-xl max-w-full ${
                  message.sender === 'user'
                    ? 'bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30'
                    : message.isError
                    ? 'bg-gradient-to-r from-red-500/20 to-pink-500/20 border border-red-500/30'
                    : 'bg-black/20 border border-white/10'
                }`}
              >
                <p className="text-white whitespace-pre-wrap leading-relaxed">
                  {message.text}
                </p>
                <p className="text-xs text-gray-400 mt-2">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="flex items-start space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                <Bot className="text-white" size={20} />
              </div>
              <div className="bg-black/20 border border-white/10 px-6 py-4 rounded-xl">
                <div className="flex items-center space-x-2">
                  <Loader2 className="animate-spin text-blue-400" size={16} />
                  <span className="text-gray-300">AI думает...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-white/10 p-6">
        <div className="flex space-x-4">
          <div className="flex-1 relative">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Напишите ваше сообщение..."
              className="w-full bg-black/20 border border-white/10 rounded-xl px-6 py-4 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500/50 resize-none"
              rows={1}
              style={{ minHeight: '60px', maxHeight: '120px' }}
            />
          </div>
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 py-4 rounded-xl transition-all flex items-center justify-center min-w-[80px]"
          >
            {isLoading ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <Send size={20} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIChat;