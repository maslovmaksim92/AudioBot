import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const LiveVoiceChat = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [conversationLog, setConversationLog] = useState([]);
  const [callDuration, setCallDuration] = useState(0);
  
  const recognitionRef = useRef(null);
  const callStartTime = useRef(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    // Initialize speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'ru-RU';
      
      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        setTranscript(finalTranscript || interimTranscript);
        
        if (finalTranscript && finalTranscript.trim().length > 3) {
          handleVoiceInput(finalTranscript);
          setTranscript('');
        }
      };
      
      recognitionRef.current.onstart = () => setIsListening(true);
      recognitionRef.current.onend = () => {
        setIsListening(false);
        if (isConnected) {
          // Restart listening if call is active
          setTimeout(() => {
            if (recognitionRef.current && isConnected) {
              recognitionRef.current.start();
            }
          }, 100);
        }
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'not-allowed') {
          alert('Для голосового чата нужно разрешить доступ к микрофону');
        }
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isConnected]);

  const startCall = async () => {
    try {
      setIsConnected(true);
      callStartTime.current = Date.now();
      
      // Start call duration timer
      intervalRef.current = setInterval(() => {
        if (callStartTime.current) {
          setCallDuration(Math.floor((Date.now() - callStartTime.current) / 1000));
        }
      }, 1000);

      // Start listening
      if (recognitionRef.current) {
        recognitionRef.current.start();
      }

      // Initial AI greeting
      const greeting = "Привет! Это МАКС, ваш AI-ассистент. Я готов к разговору! О чем поговорим?";
      setAiResponse(greeting);
      speakText(greeting);
      
      setConversationLog(prev => [...prev, {
        type: 'ai',
        text: greeting,
        timestamp: new Date()
      }]);
      
    } catch (error) {
      console.error('Error starting call:', error);
      alert('Ошибка при запуске вызова');
    }
  };

  const endCall = () => {
    setIsConnected(false);
    setIsListening(false);
    setIsSpeaking(false);
    setTranscript('');
    
    if (recognitionRef.current) {
      recognitionRef.current.abort();
    }
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    // Stop any ongoing speech
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }
    
    callStartTime.current = null;
    setCallDuration(0);
  };

  const handleVoiceInput = async (text) => {
    if (!text.trim()) return;

    // Add user message to log
    setConversationLog(prev => [...prev, {
      type: 'user',
      text: text,
      timestamp: new Date()
    }]);

    try {
      // Send to AI
      const response = await axios.post(`${BACKEND_URL}/api/ai/chat`, {
        message: text,
        session_id: 'live_voice_chat'
      });

      const aiText = response.data.response;
      setAiResponse(aiText);
      
      // Add AI response to log
      setConversationLog(prev => [...prev, {
        type: 'ai',
        text: aiText,
        timestamp: new Date()
      }]);

      // Speak AI response
      speakText(aiText);
      
    } catch (error) {
      console.error('Error getting AI response:', error);
      const errorText = "Извините, произошла ошибка. Повторите, пожалуйста.";
      setAiResponse(errorText);
      speakText(errorText);
    }
  };

  const speakText = (text) => {
    if (!window.speechSynthesis) return;
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    setIsSpeaking(true);
    
    // Make text more natural for speech
    let naturalText = text;
    
    // Add pauses and breathing
    naturalText = naturalText.replace(/\. /g, '... ');
    naturalText = naturalText.replace(/! /g, '! ');
    naturalText = naturalText.replace(/\? /g, '? ');
    
    // Add director personality to speech
    const directorPhrases = {
      'я думаю': 'по моему анализу',
      'возможно': 'рекомендую',
      'может быть': 'необходимо',
      'попробуйте': 'выполните'
    };
    
    Object.entries(directorPhrases).forEach(([casual, formal]) => {
      naturalText = naturalText.replace(new RegExp(casual, 'gi'), formal);
    });
    
    // Create more natural speech
    const utterance = new SpeechSynthesisUtterance(naturalText);
    utterance.lang = 'ru-RU';
    utterance.rate = 0.85; // Slightly slower for authority
    utterance.pitch = 0.9; // Slightly lower pitch for director voice
    utterance.volume = 0.9;
    
    // Try to find the best Russian voice
    const voices = window.speechSynthesis.getVoices();
    const russianVoices = voices.filter(voice => 
      voice.lang.includes('ru') || voice.lang.includes('RU')
    );
    
    // Prefer male voice for director personality
    const maleVoice = russianVoices.find(voice => 
      voice.name.toLowerCase().includes('male') || 
      voice.name.toLowerCase().includes('мужской')
    );
    
    if (maleVoice) {
      utterance.voice = maleVoice;
    } else if (russianVoices.length > 0) {
      utterance.voice = russianVoices[0];
    }
    
    // Add emotion based on content
    if (text.includes('проблем') || text.includes('ошибк')) {
      utterance.rate = 0.8; // Slower for serious topics
      utterance.pitch = 0.8; // Lower for concern
    } else if (text.includes('отлично') || text.includes('успешно')) {
      utterance.rate = 0.95; // Slightly faster for positive news
      utterance.pitch = 1.0; // Normal pitch for good news
    }
    
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    window.speechSynthesis.speak(utterance);
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const toggleMute = () => {
    if (isListening && recognitionRef.current) {
      recognitionRef.current.abort();
    } else if (isConnected && recognitionRef.current) {
      recognitionRef.current.start();
    }
  };

  return (
    <div className="live-voice-chat bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded-lg shadow-lg">
      {/* Header */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          📞 Live голосовой чат с МАКС
        </h2>
        <p className="text-gray-600">
          Разговаривайте с AI как по телефону в реальном времени
        </p>
      </div>

      {/* Call Interface */}
      <div className="bg-white rounded-lg p-6 shadow-md">
        {!isConnected ? (
          /* Call Start Screen */
          <div className="text-center">
            <div className="w-32 h-32 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
              <svg className="w-16 h-16 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z"/>
              </svg>
            </div>
            
            <button
              onClick={startCall}
              className="bg-gradient-to-r from-green-500 to-green-600 text-white px-8 py-4 rounded-full text-lg font-semibold hover:from-green-600 hover:to-green-700 transition-all duration-300 shadow-lg transform hover:scale-105"
            >
              🎙️ Начать разговор с МАКС
            </button>
            
            <p className="text-gray-500 text-sm mt-4">
              Нажмите для начала голосового разговора
            </p>
          </div>
        ) : (
          /* Active Call Screen */
          <div>
            {/* Call Status */}
            <div className="text-center mb-6">
              <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                <span className="text-white text-2xl font-bold">🤖</span>
              </div>
              
              <h3 className="text-xl font-semibold text-gray-800">МАКС AI-ассистент</h3>
              <p className="text-green-600 font-medium">📞 На связи</p>
              <p className="text-gray-500 text-lg font-mono">
                {formatDuration(callDuration)}
              </p>
            </div>

            {/* Current Status */}
            <div className="text-center mb-6">
              {isListening && (
                <div className="mb-4">
                  <p className="text-blue-600 font-medium mb-2">🎙️ Слушаю вас...</p>
                  {transcript && (
                    <p className="text-gray-700 bg-blue-50 px-4 py-2 rounded-lg">
                      "{transcript}"
                    </p>
                  )}
                  {/* Audio Visualizer */}
                  <div className="flex justify-center space-x-1 mt-3">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className="w-2 bg-blue-500 rounded animate-pulse"
                        style={{
                          height: `${Math.random() * 30 + 10}px`,
                          animationDelay: `${i * 0.1}s`
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}
              
              {isSpeaking && (
                <div className="mb-4">
                  <p className="text-purple-600 font-medium mb-2">🗣️ МАКС отвечает...</p>
                  {aiResponse && (
                    <p className="text-gray-700 bg-purple-50 px-4 py-2 rounded-lg">
                      {aiResponse}
                    </p>
                  )}
                  {/* Speaking Animation */}
                  <div className="flex justify-center space-x-1 mt-3">
                    {[...Array(7)].map((_, i) => (
                      <div
                        key={i}
                        className="w-2 bg-purple-500 rounded animate-bounce"
                        style={{
                          height: `${Math.random() * 40 + 15}px`,
                          animationDelay: `${i * 0.1}s`
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}
              
              {!isListening && !isSpeaking && (
                <p className="text-gray-500">🔇 Ожидание...</p>
              )}
            </div>

            {/* Call Controls */}
            <div className="flex justify-center space-x-4">
              <button
                onClick={toggleMute}
                className={`p-4 rounded-full transition-all ${
                  isListening 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-300 text-gray-600'
                }`}
                title={isListening ? 'Выключить микрофон' : 'Включить микрофон'}
              >
                {isListening ? (
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM12.293 7.293a1 1 0 011.414 0L15 8.586l1.293-1.293a1 1 0 111.414 1.414L16.414 10l1.293 1.293a1 1 0 01-1.414 1.414L15 11.414l-1.293 1.293a1 1 0 01-1.414-1.414L13.586 10l-1.293-1.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
              
              <button
                onClick={endCall}
                className="bg-red-500 text-white p-4 rounded-full hover:bg-red-600 transition-all shadow-lg transform hover:scale-105"
                title="Завершить разговор"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Conversation Log */}
      {conversationLog.length > 0 && (
        <div className="mt-6 bg-white rounded-lg p-4 shadow-md max-h-64 overflow-y-auto">
          <h4 className="font-semibold text-gray-800 mb-3">📝 Лог разговора:</h4>
          <div className="space-y-2">
            {conversationLog.map((entry, index) => (
              <div key={index} className={`text-sm ${
                entry.type === 'user' ? 'text-blue-600' : 'text-purple-600'
              }`}>
                <span className="font-medium">
                  {entry.type === 'user' ? '👤 Вы:' : '🤖 МАКС:'}
                </span>
                <span className="ml-2">{entry.text}</span>
                <span className="text-gray-400 text-xs ml-2">
                  {entry.timestamp.toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="mt-4 text-center">
        <p className="text-gray-500 text-sm">
          💡 <strong>Совет:</strong> Говорите четко и делайте паузы между фразами для лучшего распознавания
        </p>
      </div>
    </div>
  );
};

export default LiveVoiceChat;