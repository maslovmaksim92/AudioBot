import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button, LoadingSpinner } from '../UI';

const LiveChat = () => {
  const { actions } = useApp();
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [textInput, setTextInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [wsConnection, setWsConnection] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  useEffect(() => {
    console.log('💬 Live Chat mounted');
    initWebSocket();
    initSpeechRecognition();
    initSpeechSynthesis();
    
    // Приветственное сообщение
    setMessages([{
      type: 'system',
      text: '👋 Привет! Я ваш персональный помощник VasDom. Подключаюсь...',
      timestamp: new Date()
    }]);

    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initSpeechRecognition = () => {
    if ('webkitSpeechRecognition' in window) {
      const recognition = new window.webkitSpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'ru-RU';
      
      recognition.onresult = (event) => {
        let transcript = '';
        let interim = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            transcript = event.results[i][0].transcript;
            console.log('🎤 Voice input:', transcript);
            handleMessage(transcript);
            setCurrentMessage('');
          } else {
            interim = event.results[i][0].transcript;
          }
        }
        
        setCurrentMessage(interim);
      };
      
      recognition.onend = () => {
        setIsListening(false);
        setCurrentMessage('');
      };
      
      recognition.onerror = (event) => {
        console.error('❌ Speech recognition error:', event.error);
        setIsListening(false);
        setCurrentMessage('');
      };
      
      recognitionRef.current = recognition;
    }
  };

  const initSpeechSynthesis = () => {
    if ('speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;
    }
  };

  const speakText = (text) => {
    if (synthRef.current && text && voiceEnabled) {
      synthRef.current.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ru-RU';
      utterance.rate = 0.85; // Немного медленнее для естественности
      utterance.pitch = 1.1; // Чуть выше для дружелюбности
      utterance.volume = 0.9;
      
      // Попытаться выбрать женский голос
      const voices = synthRef.current.getVoices();
      const russianVoice = voices.find(voice => 
        voice.lang.includes('ru') && voice.name.toLowerCase().includes('woman')
      ) || voices.find(voice => voice.lang.includes('ru'));
      
      if (russianVoice) {
        utterance.voice = russianVoice;
      }
      
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      
      synthRef.current.speak(utterance);
    }
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setIsListening(true);
      setCurrentMessage('');
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  const initWebSocket = () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const wsUrl = backendUrl.replace('https://', 'wss://').replace('http://', 'ws://');
      const ws = new WebSocket(`${wsUrl}/api/live-chat/ws`);
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setWsConnection(ws);
        
        // Приветственное сообщение при подключении
        setMessages(prev => [...prev, {
          type: 'system',
          text: '✅ Подключение установлено! Теперь вы можете общаться с AI в реальном времени.',
          timestamp: new Date()
        }]);

        // Отправляем начальное сообщение AI
        setTimeout(() => {
          setMessages(prev => [...prev, {
            type: 'ai',
            text: 'Привет! Я VasDom AI в режиме реального времени. Готов к живому общению! У нас 348 домов в управлении, 6 рабочих бригад. О чем поговорим?',
            timestamp: new Date()
          }]);
        }, 1000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message received:', data);
          
          if (data.type === 'ai_response') {
            setMessages(prev => [...prev, {
              type: 'ai',
              text: data.message,
              timestamp: new Date()
            }]);
            setIsProcessing(false);
          }
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
        setWsConnection(null);
        
        setMessages(prev => [...prev, {
          type: 'system',
          text: '🔌 Соединение разорвано. Пытаемся переподключиться...',
          timestamp: new Date()
        }]);

        // Попытка переподключения через 3 секунды
        setTimeout(() => {
          initWebSocket();
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        actions.addNotification({
          type: 'error',
          message: 'Ошибка WebSocket соединения'
        });
      };

    } catch (error) {
      console.error('❌ WebSocket initialization error:', error);
      
      // Fallback сообщение
      setMessages(prev => [...prev, {
        type: 'system',
        text: '⚠️ WebSocket недоступен. Используйте обычный AI Чат для общения.',
        timestamp: new Date()
      }]);
    }
  };

  const handleMessage = async (text) => {
    if (!text?.trim()) return;

    // Add user message
    const userMessage = {
      type: 'user',
      text: text.trim(),
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);

    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      // Отправляем через WebSocket
      wsConnection.send(JSON.stringify({
        type: 'user_message',
        message: text.trim(),
        user_id: 'live_chat_user'
      }));
    } else {
      // Fallback к обычному API если WebSocket недоступен
      try {
        console.log('🔄 WebSocket unavailable, using fallback API');
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/voice/process`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: text.trim(),
            user_id: 'live_chat_user'
          })
        });

        const data = await response.json();
        
        if (data && data.response) {
          setMessages(prev => [...prev, {
            type: 'ai',
            text: data.response,
            timestamp: new Date()
          }]);
        }
      } catch (error) {
        console.error('❌ Fallback API error:', error);
        setMessages(prev => [...prev, {
          type: 'ai',
          text: 'Извините, произошла ошибка. Попробуйте еще раз.',
          timestamp: new Date(),
          isError: true
        }]);
      }
      setIsProcessing(false);
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (textInput.trim()) {
      handleMessage(textInput);
      setTextInput('');
    }
  };

  const clearChat = () => {
    setMessages([{
      type: 'system',
      text: 'Чат очищен. Продолжаем живое общение!',
      timestamp: new Date()
    }]);
  };

  const reconnectWebSocket = () => {
    if (wsConnection) {
      wsConnection.close();
    }
    initWebSocket();
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Живой разговор</h1>
          <p className="text-gray-600">Real-time общение с VasDom AI через WebSocket</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="secondary" onClick={clearChat}>
            🗑️ Очистить
          </Button>
          <Button 
            variant={isConnected ? "success" : "warning"} 
            onClick={reconnectWebSocket}
            disabled={isConnected}
          >
            {isConnected ? '✅ Подключено' : '🔄 Переподключить'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Chat Messages */}
        <div className="lg:col-span-3">
          <Card className="h-96 flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    message.type === 'user' ? 'justify-end' : 
                    message.type === 'system' ? 'justify-center' : 'justify-start'
                  }`}
                >
                  <div
                    className={`px-4 py-2 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white max-w-xs lg:max-w-md'
                        : message.type === 'system'
                        ? 'bg-yellow-100 text-yellow-800 border border-yellow-200 max-w-md text-center'
                        : message.isError
                        ? 'bg-red-100 text-red-800 border border-red-200 max-w-xs lg:max-w-md'
                        : 'bg-green-100 text-green-800 border border-green-200 max-w-xs lg:max-w-md'
                    }`}
                  >
                    <p className="text-sm">{message.text}</p>
                    <p className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString('ru-RU')}
                    </p>
                  </div>
                </div>
              ))}
              
              {isProcessing && (
                <div className="flex justify-start">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <LoadingSpinner size="sm" text="AI отвечает в реальном времени..." />
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Text Input */}
            <div className="border-t p-4">
              <form onSubmit={handleTextSubmit} className="flex space-x-2">
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Введите сообщение для живого разговора..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  disabled={isProcessing}
                />
                <Button 
                  type="submit" 
                  disabled={!textInput.trim() || isProcessing}
                  variant="success"
                >
                  ⚡ Отправить
                </Button>
              </form>
            </div>
          </Card>
        </div>

        {/* Status Panel */}
        <div className="space-y-4">
          <Card title="🔗 Статус соединения">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">WebSocket:</span>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  isConnected 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {isConnected ? '✅ Активен' : '❌ Отключен'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm">Режим:</span>
                <span className="text-xs text-blue-600 font-semibold">
                  Real-time
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm">AI Модель:</span>
                <span className="text-xs text-purple-600">
                  GPT-4 mini
                </span>
              </div>
            </div>
          </Card>

          <Card title="💡 Возможности">
            <div className="space-y-2 text-sm text-gray-600">
              <p>• <strong>Мгновенные ответы</strong> от AI</p>
              <p>• <strong>Постоянное подключение</strong></p>
              <p>• <strong>Автопереподключение</strong></p>
              <p>• <strong>История разговоров</strong></p>
            </div>
          </Card>

          <Card title="🏢 Контекст VasDom">
            <div className="space-y-2 text-sm text-gray-600">
              <p>• 348 домов в управлении</p>
              <p>• 6 рабочих бригад Калуги</p>
              <p>• Интеграция с Bitrix24</p>
              <p>• Telegram уведомления</p>
            </div>
          </Card>

          <Card title="📊 Статистика чата">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Сообщений:</span>
                <span className="font-semibold">{messages.length}</span>
              </div>
              <div className="flex justify-between">
                <span>Тип чата:</span>
                <span className="text-green-600">💬 Живой</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default LiveChat;