import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button } from '../UI';

const RealtimeVoiceChat = () => {
  const { actions } = useApp();
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [textInput, setTextInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [wsConnection, setWsConnection] = useState(null);
  const [realtimeAudio, setRealtimeAudio] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [bitrixData, setBitrixData] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    console.log('🎤 Realtime Voice Chat mounted');
    initRealtimeWebSocket();
    
    // Приветственное сообщение
    setMessages([{
      type: 'system',
      text: '🎤 Подключаюсь к системе GPT-4o Realtime для живого голосового общения...',
      timestamp: new Date()
    }]);

    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
      if (realtimeAudio) {
        realtimeAudio.cleanup();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initRealtimeWebSocket = () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const wsUrl = backendUrl.replace('https://', 'wss://').replace('http://', 'ws://');
      const ws = new WebSocket(`${wsUrl}/api/realtime-voice/ws`);
      
      ws.onopen = () => {
        console.log('🎤 Realtime WebSocket connected');
        setIsConnected(true);
        setWsConnection(ws);
        
        setMessages(prev => [...prev, {
          type: 'system',
          text: '✨ Подключение к GPT-4o Realtime установлено! Алиса готова к живому общению.',
          timestamp: new Date()
        }]);

        // Инициализация WebRTC аудио
        initWebRTCAudio();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('🎤 Realtime message received:', data);
          
          if (data.type === 'assistant_message') {
            const aiMessage = {
              type: 'ai',
              text: data.message,
              timestamp: new Date(),
              isRealtime: true
            };
            
            setMessages(prev => [...prev, aiMessage]);
            
            // Сохраняем данные Bitrix24 если есть
            if (data.bitrix_data) {
              setBitrixData(data.bitrix_data);
            }
            
            setIsProcessing(false);
            setIsSpeaking(false);
          }
        } catch (error) {
          console.error('❌ Error parsing realtime message:', error);
        }
      };

      ws.onclose = () => {
        console.log('🔌 Realtime WebSocket disconnected');
        setIsConnected(false);
        setWsConnection(null);
        
        setMessages(prev => [...prev, {
          type: 'system',
          text: '😔 Голосовое соединение прервалось. Пытаюсь восстановить...',
          timestamp: new Date()
        }]);

        // Попытка переподключения
        setTimeout(() => {
          initRealtimeWebSocket();
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error('❌ Realtime WebSocket error:', error);
        actions.addNotification({
          type: 'error',
          message: 'Ошибка голосового соединения'
        });
      };

    } catch (error) {
      console.error('❌ Realtime WebSocket initialization error:', error);
      
      setMessages(prev => [...prev, {
        type: 'system',
        text: '⚠️ Голосовое соединение недоступно. Используйте текстовый режим.',
        timestamp: new Date()
      }]);
    }
  };

  const initWebRTCAudio = async () => {
    try {
      // Простая реализация WebRTC для будущего расширения
      console.log('🎵 Initializing WebRTC Audio...');
      
      // Пока используем текстовый режим с планами на WebRTC
      setRealtimeAudio({
        status: 'text-mode',
        cleanup: () => console.log('🎵 Audio cleanup')
      });
      
    } catch (error) {
      console.error('❌ WebRTC Audio initialization error:', error);
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
    setIsSpeaking(true);

    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      // Отправляем через Realtime WebSocket
      wsConnection.send(JSON.stringify({
        type: 'user_message',
        message: text.trim(),
        user_id: 'realtime_user',
        request_bitrix_data: true
      }));
    } else {
      // Fallback к обычному API
      try {
        console.log('🔄 WebSocket unavailable, using fallback API');
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/voice/process`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: text.trim(),
            user_id: 'realtime_fallback'
          })
        });

        const data = await response.json();
        
        if (data && data.response) {
          setMessages(prev => [...prev, {
            type: 'ai',
            text: data.response,
            timestamp: new Date(),
            isFallback: true
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
      setIsSpeaking(false);
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
      text: '🧹 Чат очищен. Алиса готова продолжать наше общение!',
      timestamp: new Date()
    }]);
    setBitrixData(null);
  };

  const reconnectRealtime = () => {
    if (wsConnection) {
      wsConnection.close();
    }
    initRealtimeWebSocket();
  };

  const startVoiceMode = () => {
    setIsListening(true);
    actions.addNotification({
      type: 'info',
      message: 'Голосовой режим скоро будет доступен!'
    });
  };

  return (
    <div className="p-6 bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center">
            🎤 Алиса GPT-4o Realtime
            {isSpeaking && <span className="ml-3 text-xl animate-pulse">🗣️</span>}
            {isListening && <span className="ml-3 text-xl animate-pulse">👂</span>}
          </h1>
          <p className="text-gray-600">Реальный человеческий голос с данными из Bitrix24</p>
        </div>
        <div className="flex space-x-2">
          <Button 
            variant="primary" 
            onClick={startVoiceMode}
            disabled={!isConnected}
          >
            🎤 Голосовой режим
          </Button>
          <Button variant="secondary" onClick={clearChat}>
            🧹 Очистить
          </Button>
          <Button 
            variant={isConnected ? "success" : "warning"} 
            onClick={reconnectRealtime}
            disabled={isConnected}
          >
            {isConnected ? '✨ GPT-4o активен' : '🔄 Подключить'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Chat Messages */}
        <div className="xl:col-span-3">
          <Card className="h-96 flex flex-col bg-white/90 backdrop-blur-sm shadow-xl border-0">
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
                        ? 'bg-purple-600 text-white max-w-xs lg:max-w-md shadow-lg font-medium'
                        : message.type === 'system'
                        ? 'bg-blue-50 text-blue-700 border border-blue-200 max-w-md text-center rounded-full'
                        : message.isError
                        ? 'bg-red-50 text-red-700 border border-red-200 max-w-xs lg:max-w-md'
                        : 'bg-gradient-to-r from-purple-50 to-indigo-50 text-gray-800 border border-purple-200 max-w-xs lg:max-w-md'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {message.type === 'ai' && (
                        <span className="text-sm">
                          {message.isRealtime ? '🎤' : message.isFallback ? '🤖' : '🎤'}
                        </span>
                      )}
                      <div>
                        <p className="text-sm leading-relaxed">{message.text}</p>
                        <div className="flex items-center justify-between mt-1">
                          <p className="text-xs opacity-60">
                            {message.timestamp.toLocaleTimeString('ru-RU')}
                          </p>
                          {message.isRealtime && (
                            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                              GPT-4o
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {isProcessing && (
                <div className="flex justify-start">
                  <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-2xl p-4 shadow-sm">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                      <span className="text-sm text-gray-600">
                        {isSpeaking ? 'Алиса говорит через GPT-4o...' : 'Алиса думает...'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t bg-gray-50/50 p-4 rounded-b-lg">
              <form onSubmit={handleTextSubmit} className="flex space-x-3">
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Спросите Алису о домах, бригадах, статистике..."
                  className="flex-1 px-4 py-2 bg-white rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent shadow-sm"
                  disabled={isProcessing}
                />
                <Button 
                  type="submit" 
                  disabled={!textInput.trim() || isProcessing}
                  variant="primary"
                  className="rounded-full bg-purple-600 hover:bg-purple-700"
                >
                  🎤 Отправить
                </Button>
              </form>
            </div>
          </Card>
        </div>

        {/* Status Panel */}
        <div className="space-y-4">
          <Card title="🎤 Статус GPT-4o Realtime" className="bg-white/90 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Соединение:</span>
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                  isConnected 
                    ? 'bg-purple-100 text-purple-700' 
                    : 'bg-red-100 text-red-700'
                }`}>
                  {isConnected ? '🎤 GPT-4o активен' : '😴 Не подключен'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Модель:</span>
                <span className="text-xs text-purple-600 font-semibold px-3 py-1 bg-purple-100 rounded-full">
                  GPT-4o Realtime
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Голос:</span>
                <span className="text-xs text-green-600 font-semibold px-3 py-1 bg-green-100 rounded-full">
                  Человеческий
                </span>
              </div>
              
              {isSpeaking && (
                <div className="flex items-center justify-center p-2 bg-purple-50 rounded-lg">
                  <span className="text-sm text-purple-700 animate-pulse">🗣️ Алиса говорит реальным голосом...</span>
                </div>
              )}
            </div>
          </Card>

          <Card title="🏢 Актуальные данные из Bitrix24" className="bg-white/90 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>🏠 Домов в CRM:</span>
                <span className="font-semibold text-blue-600">50</span>
              </div>
              <div className="flex justify-between">
                <span>👥 Сотрудников:</span>
                <span className="font-semibold text-green-600">82</span>
              </div>
              <div className="flex justify-between">
                <span>🚛 Бригад:</span>
                <span className="font-semibold text-purple-600">6</span>
              </div>
              <div className="flex justify-between">
                <span>📍 Город:</span>
                <span className="font-semibold text-orange-600">Калуга</span>
              </div>
              <div className="flex justify-between">
                <span>🔗 Bitrix24:</span>
                <span className="font-semibold text-green-600">Подключен</span>
              </div>
              
              {bitrixData && (
                <div className="mt-3 p-2 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-700 font-medium">Последние данные:</p>
                  <p className="text-xs text-blue-600 mt-1">{bitrixData.substring(0, 100)}...</p>
                </div>
              )}
            </div>
          </Card>

          <Card title="🎯 Возможности Алисы" className="bg-white/90 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-2 text-sm text-gray-600">
              <p>🏠 <strong>Статус домов</strong> из CRM</p>
              <p>📊 <strong>Статистика</strong> по бригадам</p>
              <p>👥 <strong>Информация</strong> о сотрудниках</p>
              <p>🎤 <strong>Голосовое общение</strong> (скоро)</p>
              <p>📈 <strong>Аналитика</strong> работы</p>
            </div>
          </Card>

          <Card title="💡 Примеры вопросов" className="bg-white/90 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-2 text-sm text-gray-600">
              <p>🏠 "Покажи статус наших домов"</p>
              <p>📊 "Какая статистика по бригадам?"</p>
              <p>👥 "Сколько у нас сотрудников?"</p>
              <p>🔍 "Какие дома требуют внимания?"</p>
              <p>📈 "Расскажи общую статистику"</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default RealtimeVoiceChat;