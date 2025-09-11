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
          text: '✨ Отлично! Связь установлена. Теперь мы можем общаться!',
          timestamp: new Date()
        }]);

        // Отправляем приветствие от AI
        setTimeout(() => {
          const welcomeMessage = {
            type: 'ai',
            text: 'Привет! 😊 Меня зовут Алиса, я ваш персональный помощник в VasDom. Готова помочь с любыми вопросами по нашим 348 домам и 6 бригадам. О чем поговорим?',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, welcomeMessage]);
          if (voiceEnabled) {
            speakText(welcomeMessage.text);
          }
        }, 1000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message received:', data);
          
          if (data.type === 'ai_response') {
            const aiMessage = {
              type: 'ai',
              text: data.message,
              timestamp: new Date()
            };
            setMessages(prev => [...prev, aiMessage]);
            
            // Озвучиваем ответ AI человеческим голосом
            if (voiceEnabled) {
              speakText(data.message);
            }
            
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
          text: '😔 Связь прервалась. Пытаюсь восстановить соединение...',
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
        text: '⚠️ Голосовая связь временно недоступна. Используйте текстовый чат.',
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
          const aiMessage = {
            type: 'ai',
            text: data.response,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, aiMessage]);
          
          // Озвучиваем ответ AI
          if (voiceEnabled) {
            speakText(data.response);
          }
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
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
    setMessages([{
      type: 'system',
      text: '🧹 Чат очищен. Продолжаем наше общение!',
      timestamp: new Date()
    }]);
  };

  const reconnectWebSocket = () => {
    if (wsConnection) {
      wsConnection.close();
    }
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
    initWebSocket();
  };

  const toggleVoice = () => {
    setVoiceEnabled(!voiceEnabled);
    if (!voiceEnabled && synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  return (
    <div className="p-6 bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center">
            👋 Живое общение с Алисой
            {isSpeaking && <span className="ml-3 text-xl animate-pulse">🗣️</span>}
          </h1>
          <p className="text-gray-600">Ваш персональный помощник VasDom всегда готов помочь</p>
        </div>
        <div className="flex space-x-2">
          <Button 
            variant="secondary" 
            onClick={toggleVoice}
            className={voiceEnabled ? "bg-green-100 text-green-700" : "bg-gray-100"}
          >
            {voiceEnabled ? '🔊 Голос вкл' : '🔇 Голос выкл'}
          </Button>
          <Button variant="secondary" onClick={clearChat}>
            🧹 Очистить
          </Button>
          <Button 
            variant={isConnected ? "success" : "warning"} 
            onClick={reconnectWebSocket}
            disabled={isConnected}
          >
            {isConnected ? '✨ На связи' : '🔄 Подключить'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Chat Messages */}
        <div className="xl:col-span-3">
          <Card className="h-96 flex flex-col bg-white/80 backdrop-blur-sm shadow-xl border-0">
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    message.type === 'user' ? 'justify-end' : 
                    message.type === 'system' ? 'justify-center' : 'justify-start'
                  }`}
                >
                  <div
                    className={`px-4 py-3 rounded-2xl shadow-sm ${
                      message.type === 'user'
                        ? 'bg-blue-500 text-white max-w-xs lg:max-w-md'
                        : message.type === 'system'
                        ? 'bg-yellow-50 text-yellow-700 border border-yellow-200 max-w-md text-center rounded-full'
                        : message.isError
                        ? 'bg-red-50 text-red-700 border border-red-200 max-w-xs lg:max-w-md'
                        : 'bg-gradient-to-r from-green-50 to-emerald-50 text-gray-800 border border-green-200 max-w-xs lg:max-w-md'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {message.type === 'ai' && <span className="text-sm">🤖</span>}
                      <div>
                        <p className="text-sm leading-relaxed">{message.text}</p>
                        <p className="text-xs opacity-60 mt-1">
                          {message.timestamp.toLocaleTimeString('ru-RU')}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {currentMessage && (
                <div className="flex justify-end">
                  <div className="bg-blue-200 text-blue-800 px-4 py-3 rounded-2xl max-w-xs lg:max-w-md shadow-sm">
                    <div className="flex items-center space-x-2">
                      <span className="animate-pulse">🎤</span>
                      <div>
                        <p className="text-sm">{currentMessage}</p>
                        <p className="text-xs opacity-70">Слушаю вас...</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {isProcessing && (
                <div className="flex justify-start">
                  <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-4 shadow-sm">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
                      <span className="text-sm text-gray-600">Алиса думает...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t bg-gray-50/50 p-4 rounded-b-lg">
              <div className="flex space-x-3">
                <Button
                  onClick={isListening ? stopListening : startListening}
                  variant={isListening ? 'danger' : 'primary'}
                  disabled={isProcessing}
                  className="flex-shrink-0"
                >
                  {isListening ? '⏹️ Стоп' : '🎤 Говорить'}
                </Button>
                <form onSubmit={handleTextSubmit} className="flex-1 flex space-x-2">
                  <input
                    type="text"
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="Напишите сообщение Алисе..."
                    className="flex-1 px-4 py-2 bg-white rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
                    disabled={isProcessing}
                  />
                  <Button 
                    type="submit" 
                    disabled={!textInput.trim() || isProcessing}
                    variant="success"
                    className="rounded-full"
                  >
                    💬 Отправить
                  </Button>
                </form>
              </div>
            </div>
          </Card>
        </div>

        {/* Status Panel */}
        <div className="space-y-4">
          <Card title="💫 Статус Алисы" className="bg-white/80 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Соединение:</span>
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                  isConnected 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-red-100 text-red-700'
                }`}>
                  {isConnected ? '✨ На связи' : '😴 Не активна'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Голос:</span>
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                  voiceEnabled 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'bg-gray-100 text-gray-700'
                }`}>
                  {voiceEnabled ? '🔊 Включен' : '🔇 Выключен'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Режим:</span>
                <span className="text-xs text-purple-600 font-semibold px-3 py-1 bg-purple-100 rounded-full">
                  💬 Живое общение
                </span>
              </div>
              
              {isSpeaking && (
                <div className="flex items-center justify-center p-2 bg-blue-50 rounded-lg">
                  <span className="text-sm text-blue-700 animate-pulse">🗣️ Алиса говорит...</span>
                </div>
              )}
              
              {isListening && (
                <div className="flex items-center justify-center p-2 bg-green-50 rounded-lg">
                  <span className="text-sm text-green-700 animate-pulse">👂 Слушаю вас...</span>
                </div>
              )}
            </div>
          </Card>

          <Card title="🎤 Голосовое управление" className="bg-white/80 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-3">
              <Button
                onClick={isListening ? stopListening : startListening}
                variant={isListening ? 'danger' : 'primary'}
                size="lg"
                className="w-full"
                disabled={isProcessing}
              >
                {isListening ? '⏹️ Перестать говорить' : '🎤 Начать говорить'}
              </Button>
              
              {!('webkitSpeechRecognition' in window) && (
                <p className="text-sm text-red-600 text-center">
                  Голосовое распознавание не поддерживается
                </p>
              )}
              
              <div className="text-xs text-gray-500 text-center">
                Нажмите и говорите с Алисой естественно
              </div>
            </div>
          </Card>

          <Card title="💡 Подсказки для общения" className="bg-white/80 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-2 text-sm text-gray-600">
              <p>💬 "Алиса, как дела с нашими домами?"</p>
              <p>🏢 "Покажи статистику по бригадам"</p>
              <p>📊 "Какие дома требуют внимания?"</p>
              <p>📅 "Как прошли последние планерки?"</p>
              <p>👥 "Расскажи о наших сотрудниках"</p>
            </div>
          </Card>

          <Card title="🏢 О компании VasDom" className="bg-white/80 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex justify-between">
                <span>🏠 Домов в управлении:</span>
                <span className="font-semibold text-blue-600">348</span>
              </div>
              <div className="flex justify-between">
                <span>👥 Сотрудников:</span>
                <span className="font-semibold text-green-600">82</span>
              </div>
              <div className="flex justify-between">
                <span>🚛 Рабочих бригад:</span>
                <span className="font-semibold text-purple-600">6</span>
              </div>
              <div className="flex justify-between">
                <span>📍 Город:</span>
                <span className="font-semibold text-orange-600">Калуга</span>
              </div>
            </div>
          </Card>

          <Card title="📊 Статистика беседы" className="bg-white/80 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Сообщений:</span>
                <span className="font-semibold text-blue-600">{messages.length}</span>
              </div>
              <div className="flex justify-between">
                <span>Помощник:</span>
                <span className="text-green-600 font-medium">👋 Алиса</span>
              </div>
              <div className="flex justify-between">
                <span>Тип чата:</span>
                <span className="text-purple-600 font-medium">💬 Живой</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default LiveChat;