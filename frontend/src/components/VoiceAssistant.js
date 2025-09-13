import React, { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/apiService';

const VoiceAssistant = () => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [conversation, setConversation] = useState([]);
  const [isInitialized, setIsInitialized] = useState(false);
  
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  useEffect(() => {
    initializeVoiceAssistant();
    return () => {
      cleanup();
    };
  }, []);

  const initializeVoiceAssistant = () => {
    // Проверяем поддержку распознавания речи
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'ru-RU';
      recognitionRef.current.maxAlternatives = 1;

      recognitionRef.current.onstart = () => {
        console.log('🎤 Voice Assistant: Listening started');
        setIsListening(true);
      };

      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript = transcript;
          }
        }

        if (finalTranscript) {
          setTranscript(finalTranscript);
          handleVoiceInput(finalTranscript);
        } else {
          setTranscript(interimTranscript);
        }
      };

      recognitionRef.current.onend = () => {
        console.log('🎤 Voice Assistant: Listening ended');
        setIsListening(false);
        setTranscript('');
      };

      recognitionRef.current.onerror = (event) => {
        console.error('🎤 Voice Assistant: Recognition error:', event.error);
        setIsListening(false);
        setTranscript('');
      };
    }

    // Проверяем поддержку синтеза речи
    if ('speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;
    }

    setIsInitialized(true);
  };

  const cleanup = () => {
    if (recognitionRef.current) {
      recognitionRef.current.abort();
    }
    if (synthRef.current) {
      synthRef.current.cancel();
    }
  };

  const startListening = () => {
    if (!recognitionRef.current || isListening) return;
    
    try {
      recognitionRef.current.start();
    } catch (error) {
      console.error('🎤 Error starting recognition:', error);
    }
  };

  const stopListening = () => {
    if (!recognitionRef.current || !isListening) return;
    
    try {
      recognitionRef.current.stop();
    } catch (error) {
      console.error('🎤 Error stopping recognition:', error);
    }
  };

  const handleVoiceInput = async (text) => {
    if (!text.trim()) return;

    // Добавляем пользовательское сообщение в разговор
    const userMessage = {
      type: 'user',
      text: text.trim(),
      timestamp: new Date()
    };
    
    setConversation(prev => [...prev, userMessage]);

    try {
      // Отправляем в AI для обработки
      const response = await apiService.processVoice(text, 'voice_assistant');
      
      if (response && response.response) {
        const aiMessage = {
          type: 'ai',
          text: response.response,
          timestamp: new Date()
        };
        
        setConversation(prev => [...prev, aiMessage]);
        setAiResponse(response.response);
        
        // Озвучиваем ответ AI
        speakText(response.response);
      } else {
        throw new Error('Invalid AI response');
      }
    } catch (error) {
      console.error('🤖 AI processing error:', error);
      const errorMessage = {
        type: 'ai',
        text: 'Извините, произошла ошибка при обработке вашего запроса.',
        timestamp: new Date()
      };
      
      setConversation(prev => [...prev, errorMessage]);
      speakText('Извините, произошла ошибка при обработке вашего запроса.');
    }
  };

  const speakText = (text) => {
    if (!synthRef.current || !text) return;

    // Останавливаем текущую речь
    synthRef.current.cancel();
    
    setIsSpeaking(true);

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ru-RU';
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 0.8;

    // Пытаемся найти русский голос
    const voices = synthRef.current.getVoices();
    const russianVoice = voices.find(voice => 
      voice.lang.includes('ru') || voice.name.toLowerCase().includes('russian')
    );

    if (russianVoice) {
      utterance.voice = russianVoice;
    }

    utterance.onstart = () => {
      setIsSpeaking(true);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
    };

    synthRef.current.speak(utterance);
  };

  const clearConversation = () => {
    setConversation([]);
    setTranscript('');
    setAiResponse('');
  };

  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Инициализация голосового ассистента...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="voice-assistant bg-gradient-to-br from-indigo-50 to-purple-50 p-6 rounded-lg shadow-lg">
      {/* Header */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          🗣️ Голосовой ассистент МАКС
        </h2>
        <p className="text-gray-600">
          Говорите с AI ассистентом голосом - задавайте вопросы и получайте ответы
        </p>
      </div>

      {/* Voice Controls */}
      <div className="bg-white rounded-lg p-6 shadow-md mb-6">
        <div className="text-center">
          {/* Main Voice Button */}
          <div className="mb-6">
            <button
              onClick={isListening ? stopListening : startListening}
              disabled={isSpeaking}
              className={`w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl font-bold transition-all duration-300 mx-auto ${
                isListening 
                  ? 'bg-red-500 animate-pulse shadow-lg scale-110' 
                  : isSpeaking
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-500 hover:bg-blue-600 shadow-md hover:shadow-lg hover:scale-105'
              }`}
            >
              {isListening ? '🎙️' : isSpeaking ? '🔊' : '🗣️'}
            </button>
          </div>

          {/* Status */}
          <div className="mb-4">
            <p className={`text-lg font-semibold ${
              isListening ? 'text-red-600' : 
              isSpeaking ? 'text-purple-600' : 
              'text-gray-700'
            }`}>
              {isListening ? '🎤 Слушаю вас...' : 
               isSpeaking ? '🔊 Говорю...' : 
               '💬 Готов к разговору'}
            </p>
            
            {transcript && (
              <p className="text-blue-600 bg-blue-50 px-4 py-2 rounded-lg mt-2">
                "{transcript}"
              </p>
            )}
          </div>

          {/* Additional Controls */}
          <div className="flex justify-center space-x-4">
            <button
              onClick={stopSpeaking}
              disabled={!isSpeaking}
              className="bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              🔇 Прервать речь
            </button>
            
            <button
              onClick={clearConversation}
              className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
            >
              🗑️ Очистить
            </button>
          </div>
        </div>
      </div>

      {/* Conversation Log */}
      {conversation.length > 0 && (
        <div className="bg-white rounded-lg p-4 shadow-md max-h-96 overflow-y-auto">
          <h4 className="font-semibold text-gray-800 mb-3">💬 История разговора:</h4>
          <div className="space-y-3">
            {conversation.map((entry, index) => (
              <div key={index} className={`flex ${entry.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  entry.type === 'user' 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-200 text-gray-800'
                }`}>
                  <div className="flex items-start space-x-2">
                    <span className="text-sm">
                      {entry.type === 'user' ? '👤' : '🤖'}
                    </span>
                    <div className="flex-1">
                      <p className="text-sm">{entry.text}</p>
                      <p className="text-xs opacity-70 mt-1">
                        {entry.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-6 bg-yellow-50 rounded-lg p-4 border border-yellow-200">
        <h4 className="font-semibold text-yellow-800 mb-2">💡 Как использовать:</h4>
        <ul className="text-sm text-yellow-700 space-y-1">
          <li>• Нажмите кнопку 🗣️ и начните говорить</li>
          <li>• МАКС автоматически ответит вам голосом</li>
          <li>• Используйте кнопку 🔇 чтобы прервать речь AI</li>
          <li>• Говорите четко для лучшего распознавания</li>
        </ul>
      </div>
    </div>
  );
};

export default VoiceAssistant;