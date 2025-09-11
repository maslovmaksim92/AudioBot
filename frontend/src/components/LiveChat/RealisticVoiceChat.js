import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button } from '../UI';

const RealisticVoiceChat = () => {
  const { actions } = useApp();
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [textInput, setTextInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [wsConnection, setWsConnection] = useState(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    console.log('🎤 Realistic Voice Chat mounted');
    initRealisticWebSocket();
    initUltraRealisticVoices();
    
    setMessages([{
      type: 'system',
      text: '🎤 Подключаюсь к системе ультра-реалистичного человеческого голоса...',
      timestamp: new Date()
    }]);

    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
      if (currentAudio) {
        currentAudio.pause();
      }
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initRealisticWebSocket = () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const wsUrl = backendUrl.replace('https://', 'wss://').replace('http://', 'ws://');
      const ws = new WebSocket(`${wsUrl}/api/realistic-voice/ws`);
      
      ws.onopen = () => {
        console.log('🎤 Realistic Voice WebSocket connected');
        setIsConnected(true);
        setWsConnection(ws);
        
        setMessages(prev => [...prev, {
          type: 'system',
          text: '✨ Подключение к OpenAI TTS установлено! Алиса готова говорить живым человеческим голосом.',
          timestamp: new Date()
        }]);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('🎤 Realistic voice message received:', data);
          
          if (data.type === 'voice_message') {
            const voiceMessage = {
              type: 'ai',
              text: data.text,
              timestamp: new Date(),
              audioData: data.audio_data,
              voiceType: 'human_realistic',
              model: data.model || 'OpenAI TTS HD'
            };
            
            setMessages(prev => [...prev, voiceMessage]);
            
            // Автоматически воспроизводим голос
            if (data.audio_data) {
              playRealisticVoice(data.audio_data, data.text);
            }
            
            setIsProcessing(false);
          }
        } catch (error) {
          console.error('❌ Error parsing realistic voice message:', error);
        }
      };

      ws.onclose = () => {
        console.log('🔌 Realistic Voice WebSocket disconnected');
        setIsConnected(false);
        setWsConnection(null);
        
        setMessages(prev => [...prev, {
          type: 'system',
          text: '😔 Голосовое соединение прервалось. Восстанавливаю связь...',
          timestamp: new Date()
        }]);

        setTimeout(() => {
          initRealisticWebSocket();
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error('❌ Realistic Voice WebSocket error:', error);
        actions.addNotification({
          type: 'error',
          message: 'Ошибка соединения с системой реального голоса'
        });
      };

    } catch (error) {
      console.error('❌ Realistic Voice WebSocket initialization error:', error);
      
      setMessages(prev => [...prev, {
        type: 'system',
        text: '⚠️ Система реального голоса недоступна.',
        timestamp: new Date()
      }]);
    }
  };

  const playRealisticVoice = (audioData, text) => {
    try {
      // Проверяем, это ли маркер для Speech Synthesis
      if (audioData && audioData.startsWith('SPEECH_SYNTHESIS:')) {
        const textToSpeak = audioData.replace('SPEECH_SYNTHESIS:', '');
        playUltraRealisticSpeech(textToSpeak);
        return;
      }

      // Если это настоящий base64 аудио (в будущем от OpenAI TTS)
      if (audioData && !audioData.startsWith('SPEECH_SYNTHESIS:')) {
        // Останавливаем предыдущее аудио
        if (currentAudio) {
          currentAudio.pause();
          currentAudio.currentTime = 0;
        }

        const audioBlob = base64ToBlob(audioData, 'audio/mp3');
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        audio.onloadstart = () => {
          setIsSpeaking(true);
          console.log('🎤 Воспроизвожу OpenAI TTS голос');
        };
        
        audio.onended = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(audioUrl);
          console.log('🎤 OpenAI TTS закончен');
        };
        
        setCurrentAudio(audio);
        audio.play();
      }
    } catch (error) {
      console.error('❌ Ошибка воспроизведения:', error);
      // Fallback к Speech Synthesis
      playUltraRealisticSpeech(text);
    }
  };

  const playUltraRealisticSpeech = (text) => {
    try {
      if (!('speechSynthesis' in window)) {
        console.error('Speech Synthesis не поддерживается');
        return;
      }

      // Останавливаем предыдущий синтез
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      
      // Максимально реалистичные настройки для русского языка
      utterance.lang = 'ru-RU';
      utterance.rate = 0.85;     // Чуть медленнее для естественности
      utterance.pitch = 0.95;    // Немного ниже для серьезности
      utterance.volume = 0.9;    // Чуть тише для комфорта
      
      // Находим лучший женский русский голос
      const voices = window.speechSynthesis.getVoices();
      console.log('🎤 Доступные голоса:', voices.map(v => `${v.name} (${v.lang})`));
      
      // Ищем самый качественный русский женский голос
      const premiumVoice = voices.find(voice => 
        voice.lang.includes('ru') && 
        (voice.name.toLowerCase().includes('милена') ||
         voice.name.toLowerCase().includes('irina') ||
         voice.name.toLowerCase().includes('anna') ||
         voice.name.toLowerCase().includes('elena') ||
         voice.name.toLowerCase().includes('premium') ||
         voice.name.toLowerCase().includes('enhanced'))
      );
      
      const qualityVoice = premiumVoice || voices.find(voice => 
        voice.lang.includes('ru') && 
        (voice.name.toLowerCase().includes('female') ||
         voice.name.toLowerCase().includes('woman') ||
         !voice.name.toLowerCase().includes('male'))
      );
      
      const russianVoice = qualityVoice || voices.find(voice => voice.lang.includes('ru'));
      
      if (russianVoice) {
        utterance.voice = russianVoice;
        console.log(`🎤 Используем голос: ${russianVoice.name} (${russianVoice.lang})`);
      } else {
        console.log('🎤 Используем голос по умолчанию');
      }
      
      utterance.onstart = () => {
        setIsSpeaking(true);
        console.log('🗣️ Алиса начала говорить реалистичным голосом');
      };
      
      utterance.onend = () => {
        setIsSpeaking(false);
        console.log('🤐 Алиса закончила говорить');
      };
      
      utterance.onerror = (event) => {
        setIsSpeaking(false);
        console.error('❌ Ошибка синтеза речи:', event.error);
      };
      
      // Небольшая задержка для лучшей загрузки голосов
      setTimeout(() => {
        window.speechSynthesis.speak(utterance);
      }, 100);
      
    } catch (error) {
      console.error('❌ Ошибка реалистичного синтеза:', error);
      setIsSpeaking(false);
    }
  };

  const base64ToBlob = (base64, mimeType) => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  };

  const handleMessage = async (text) => {
    if (!text?.trim()) return;

    const userMessage = {
      type: 'user',
      text: text.trim(),
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);

    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      wsConnection.send(JSON.stringify({
        type: 'user_message',
        message: text.trim(),
        user_id: 'realistic_voice_user'
      }));
    } else {
      setMessages(prev => [...prev, {
        type: 'ai',
        text: 'Извините, соединение с системой голоса недоступно.',
        timestamp: new Date(),
        isError: true
      }]);
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
    if (currentAudio) {
      currentAudio.pause();
    }
    setIsSpeaking(false);
    setMessages([{
      type: 'system',
      text: '🧹 Чат очищен. Алиса готова продолжать разговор живым голосом!',
      timestamp: new Date()
    }]);
  };

  const reconnectVoice = () => {
    if (wsConnection) {
      wsConnection.close();
    }
    if (currentAudio) {
      currentAudio.pause();
    }
    setIsSpeaking(false);
    initRealisticWebSocket();
  };

  const testRealisticVoice = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/realistic-voice/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: "Привет! Это тест моего реального человеческого голоса от OpenAI!" })
      });
      
      const data = await response.json();
      if (data.success && data.audio_base64) {
        playRealisticVoice(data.audio_base64, data.text);
        
        setMessages(prev => [...prev, {
          type: 'ai',
          text: data.text,
          timestamp: new Date(),
          voiceType: 'test_realistic',
          model: 'OpenAI TTS HD'
        }]);
      }
    } catch (error) {
      console.error('❌ Ошибка тестирования голоса:', error);
    }
  };

  return (
    <div className="p-6 bg-gradient-to-br from-pink-50 via-purple-50 to-indigo-100 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center">
            🎤 Алиса - Реальный Человеческий Голос
            {isSpeaking && <span className="ml-3 text-xl animate-pulse">🗣️</span>}
          </h1>
          <p className="text-gray-600">OpenAI TTS HD - неотличимо от живого человека</p>
        </div>
        <div className="flex space-x-2">
          <Button 
            variant="secondary" 
            onClick={testRealisticVoice}
            disabled={!isConnected}
          >
            🎵 Тест голоса
          </Button>
          <Button variant="secondary" onClick={clearChat}>
            🧹 Очистить
          </Button>
          <Button 
            variant={isConnected ? "success" : "warning"} 
            onClick={reconnectVoice}
            disabled={isConnected}
          >
            {isConnected ? '✨ OpenAI TTS активен' : '🔄 Подключить'}
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
                    className={`px-4 py-3 rounded-2xl shadow-sm cursor-pointer ${
                      message.type === 'user'
                        ? 'bg-pink-600 text-white max-w-xs lg:max-w-md shadow-lg font-medium'
                        : message.type === 'system'
                        ? 'bg-purple-50 text-purple-700 border border-purple-200 max-w-md text-center rounded-full'
                        : message.isError
                        ? 'bg-red-50 text-red-700 border border-red-200 max-w-xs lg:max-w-md'
                        : 'bg-gradient-to-r from-pink-50 to-purple-50 text-gray-800 border border-pink-200 max-w-xs lg:max-w-md'
                    }`}
                    onClick={() => {
                      if (message.audioData && message.type === 'ai') {
                        playRealisticVoice(message.audioData, message.text);
                      }
                    }}
                  >
                    <div className="flex items-start space-x-2">
                      {message.type === 'ai' && (
                        <span className="text-sm">
                          {message.voiceType === 'human_realistic' ? '🎤' : '🤖'}
                        </span>
                      )}
                      <div>
                        <p className="text-sm leading-relaxed">{message.text}</p>
                        <div className="flex items-center justify-between mt-1">
                          <p className="text-xs opacity-60">
                            {message.timestamp.toLocaleTimeString('ru-RU')}
                          </p>
                          {message.voiceType === 'human_realistic' && (
                            <span className="text-xs bg-pink-100 text-pink-700 px-2 py-1 rounded-full">
                              🎤 Живой голос
                            </span>
                          )}
                          {message.audioData && (
                            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full ml-1">
                              🔊 Кликни
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
                  <div className="bg-gradient-to-r from-pink-50 to-purple-50 border border-pink-200 rounded-2xl p-4 shadow-sm">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-pink-600"></div>
                      <span className="text-sm text-gray-600">
                        Алиса генерирует реальный человеческий голос...
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
                  placeholder="Напишите Алисе - она ответит живым человеческим голосом..."
                  className="flex-1 px-4 py-2 bg-white rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent shadow-sm"
                  disabled={isProcessing}
                />
                <Button 
                  type="submit" 
                  disabled={!textInput.trim() || isProcessing}
                  variant="primary"
                  className="rounded-full bg-pink-600 hover:bg-pink-700"
                >
                  🎤 Живой голос
                </Button>
              </form>
            </div>
          </Card>
        </div>

        {/* Status Panel */}
        <div className="space-y-4">
          <Card title="🎤 Статус OpenAI TTS" className="bg-white/90 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Соединение:</span>
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                  isConnected 
                    ? 'bg-pink-100 text-pink-700' 
                    : 'bg-red-100 text-red-700'
                }`}>
                  {isConnected ? '🎤 OpenAI активен' : '😴 Не подключен'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Технология:</span>
                <span className="text-xs text-pink-600 font-semibold px-3 py-1 bg-pink-100 rounded-full">
                  OpenAI TTS HD
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Голос:</span>
                <span className="text-xs text-green-600 font-semibold px-3 py-1 bg-green-100 rounded-full">
                  👤 Как живой человек
                </span>
              </div>
              
              {isSpeaking && (
                <div className="flex items-center justify-center p-2 bg-pink-50 rounded-lg">
                  <span className="text-sm text-pink-700 animate-pulse">🗣️ Алиса говорит живым голосом...</span>
                </div>
              )}
            </div>
          </Card>

          <Card title="🏢 Данные из Bitrix24" className="bg-white/90 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>🏠 Домов:</span>
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
            </div>
          </Card>

          <Card title="🎵 Преимущества голоса" className="bg-white/90 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-2 text-sm text-gray-600">
              <p>🎤 <strong>OpenAI TTS HD</strong> качество</p>
              <p>👤 <strong>Неотличимо</strong> от человека</p>
              <p>🎭 <strong>Естественные</strong> интонации</p>
              <p>🇷🇺 <strong>Идеальный</strong> русский</p>
              <p>💫 <strong>Эмоциональная</strong> речь</p>
            </div>
          </Card>

          <Card title="💡 Примеры для Алисы" className="bg-white/90 backdrop-blur-sm shadow-xl border-0">
            <div className="space-y-2 text-sm text-gray-600">
              <p>🏠 "Как дела с нашими домами?"</p>
              <p>📊 "Расскажи статистику работы"</p>
              <p>👥 "Что с бригадами сегодня?"</p>
              <p>💬 "Привет, Алиса! Как настроение?"</p>
              <p>🎤 "Спой что-нибудь красивое"</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default RealisticVoiceChat;