import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Mic, 
  Bot, 
  User, 
  Volume2, 
  Square,
  Loader2,
  Sparkles
} from 'lucide-react';

const AIChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Привет! Я AI-консультант VasDom. Могу помочь с вопросами по уборке, графикам, домам и сотрудникам. Что вас интересует?",
      isBot: true,
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceOnline, setVoiceOnline] = useState(false);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

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
      isBot: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          user_id: 'user123'
        })
      });

      const data = await response.json();
      
      const botMessage = {
        id: Date.now() + 1,
        text: data.response || 'Извините, произошла ошибка при обработке запроса.',
        isBot: true,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
      
    } catch (error) {
      console.error('AI Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Извините, сейчас я временно недоступен. Попробуйте позже.',
        isBot: true,
        timestamp: new Date()
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

  const startRecording = () => {
    setIsRecording(true);
    // Здесь будет логика записи голоса
    setTimeout(() => {
      setIsRecording(false);
      setInputMessage('Пример голосового сообщения: "Какие дома убирает бригада номер 3?"');
    }, 2000);
  };

  const speakMessage = (text) => {
    if ('speechSynthesis' in window) {
      setIsSpeaking(true);
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ru-RU';
      utterance.onend = () => setIsSpeaking(false);
      speechSynthesis.speak(utterance);
    }
  };

  const quickQuestions = [
    "Сколько домов в системе?",
    "Какие бригады сегодня работают?",
    "Покажи статистику уборок",
    "Как связаться с управляющей компанией?",
    "График уборки на эту неделю"
  ];

  return (
    <div className="p-8 max-w-4xl mx-auto h-screen flex flex-col">
      {/* Header */}
      <div className="mb-6 text-center animate-fade-scale">
        <div className="flex items-center justify-center space-x-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center">
            <Bot className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold gradient-text">AI Консультант</h1>
            <p className="text-gray-600">Диалог с голосовым помощником VasDom</p>
          </div>
        </div>
        
        <div className="flex items-center justify-center space-x-2 text-sm">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-green-600 font-medium">AI готов к диалогу</span>
        </div>
      </div>

      {/* Quick Questions */}
      <div className="mb-6 animate-slide-up">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Быстрые вопросы:</h3>
        <div className="flex flex-wrap gap-2">
          {quickQuestions.map((question, index) => (
            <button
              key={index}
              onClick={() => setInputMessage(question)}
              className="px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-sm transition-colors"
            >
              {question}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 bg-white rounded-xl shadow-elegant p-6 mb-6 overflow-y-auto animate-slide-up">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.isBot ? 'justify-start' : 'justify-end'} animate-fade-scale`}
            >
              <div className={`flex items-start space-x-3 max-w-xs lg:max-w-md ${message.isBot ? '' : 'flex-row-reverse space-x-reverse'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  message.isBot 
                    ? 'bg-gradient-to-br from-purple-500 to-pink-600' 
                    : 'bg-gradient-to-br from-blue-500 to-cyan-500'
                }`}>
                  {message.isBot ? 
                    <Bot className="w-4 h-4 text-white" /> : 
                    <User className="w-4 h-4 text-white" />
                  }
                </div>
                
                <div className={`rounded-2xl px-4 py-3 ${
                  message.isBot 
                    ? 'bg-gray-100 text-gray-900' 
                    : 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white'
                }`}>
                  <p className="text-sm">{message.text}</p>
                  <div className="flex items-center justify-between mt-2">
                    <p className={`text-xs ${
                      message.isBot ? 'text-gray-500' : 'text-blue-100'
                    }`}>
                      {message.timestamp.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                    
                    {message.isBot && (
                      <button
                        onClick={() => speakMessage(message.text)}
                        disabled={isSpeaking}
                        className="ml-2 p-1 hover:bg-gray-200 rounded-full transition-colors"
                      >
                        <Volume2 className="w-3 h-3 text-gray-600" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start animate-fade-scale">
              <div className="flex items-start space-x-3 max-w-xs lg:max-w-md">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-gray-100 rounded-2xl px-4 py-3">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin text-gray-600" />
                    <span className="text-sm text-gray-600">AI печатает...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white rounded-xl shadow-elegant p-4 animate-slide-up">
        <div className="flex items-center space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Задайте вопрос AI консультанту..."
              className="w-full p-3 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
              rows="1"
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
            <div className="absolute right-3 top-3 flex items-center space-x-1">
              <Sparkles className="w-4 h-4 text-purple-500" />
            </div>
          </div>
          
          <button
            onClick={() => setVoiceOnline(v => !v)}
            className={`p-3 rounded-xl transition-all duration-200 ${voiceOnline ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            title="Разговор онлайн"
          >
            {voiceOnline ? 'Онлайн' : 'Онлайн-голос'}
          </button>

          <button
            onClick={startRecording}
            disabled={isRecording}
            className={`p-3 rounded-xl transition-all duration-200 ${
              isRecording 
                ? 'bg-red-500 text-white animate-pulse' 
                : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
            }`}
          >
            {isRecording ? <Square className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>
          
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="btn-primary p-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        
        <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
          <div className="flex items-center space-x-2">
            <span>Нажмите Enter для отправки</span>
          </div>
          <div className="flex items-center space-x-1">
            <Bot className="w-3 h-3" />
            <span>Powered by Emergent LLM</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIChat;