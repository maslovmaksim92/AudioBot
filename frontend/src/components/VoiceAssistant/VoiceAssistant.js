import React, { useState, useRef, useEffect } from 'react';

const VoiceAssistant = ({ onVoiceMessage, isListening: parentListening }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    // Check if browser supports speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      setIsSupported(true);
      recognitionRef.current = new SpeechRecognition();
      
      // Configure recognition
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'ru-RU';
      
      // Handle results
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
        
        if (finalTranscript) {
          onVoiceMessage(finalTranscript);
          setTranscript('');
        }
      };
      
      // Handle events
      recognitionRef.current.onstart = () => {
        setIsListening(true);
      };
      
      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        setTranscript('');
      };
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [onVoiceMessage]);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  // Text-to-speech function
  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ru-RU';
      utterance.rate = 0.9;
      utterance.volume = 0.8;
      
      // Try to find Russian voice
      const voices = speechSynthesis.getVoices();
      const russianVoice = voices.find(voice => voice.lang.includes('ru'));
      if (russianVoice) {
        utterance.voice = russianVoice;
      }
      
      speechSynthesis.speak(utterance);
    }
  };

  if (!isSupported) {
    return (
      <div className="voice-assistant bg-gray-100 p-4 rounded-lg">
        <p className="text-sm text-gray-600">
          🎙️ Голосовые команды не поддерживаются в этом браузере
        </p>
      </div>
    );
  }

  return (
    <div className="voice-assistant bg-gradient-to-r from-purple-100 to-blue-100 p-4 rounded-lg">
      <div className="flex items-center space-x-4">
        <button
          onClick={isListening ? stopListening : startListening}
          className={`p-3 rounded-full transition-all duration-300 ${
            isListening 
              ? 'bg-red-500 text-white animate-pulse' 
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
          disabled={parentListening}
        >
          {isListening ? (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0V9a1 1 0 012 0v1a2 2 0 104 0V9a1 1 0 012 0v1zm-.464 4.95L12 16.414l1.414-1.414a1 1 0 011.414 1.414l-2 2a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L12 16.414l1.536-1.464z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
            </svg>
          )}
        </button>
        
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-800">
            {isListening ? '🎙️ Слушаю...' : '🗣️ Нажмите для голосовой команды'}
          </p>
          {transcript && (
            <p className="text-sm text-blue-600 mt-1">"{transcript}"</p>
          )}
        </div>
        
        <div className="text-xs text-gray-500">
          "Привет, МАКС!"
        </div>
      </div>
      
      {isListening && (
        <div className="mt-3 flex justify-center">
          <div className="flex space-x-1">
            <div className="w-2 h-8 bg-blue-500 rounded animate-pulse"></div>
            <div className="w-2 h-6 bg-blue-400 rounded animate-pulse" style={{animationDelay: '0.1s'}}></div>
            <div className="w-2 h-10 bg-blue-500 rounded animate-pulse" style={{animationDelay: '0.2s'}}></div>
            <div className="w-2 h-4 bg-blue-400 rounded animate-pulse" style={{animationDelay: '0.3s'}}></div>
            <div className="w-2 h-8 bg-blue-500 rounded animate-pulse" style={{animationDelay: '0.4s'}}></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceAssistant;