import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { apiService } from '../../services/apiService';
import { Card, Button, LoadingSpinner } from '../UI';

const AIChat = () => {
  const { actions } = useApp();
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [textInput, setTextInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    console.log('📞 AI Chat mounted');
    initSpeechRecognition();
    initSpeechSynthesis();
    
    // Приветственное сообщение от AI
    setMessages([{
      type: 'ai',
      text: 'Привет! Я VasDom AI, ваш помощник по управлению клининговой компанией. У нас 348 домов в управлении и 6 рабочих бригад. О чем хотите поговорить?',
      timestamp: new Date()
    }]);
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
            console.log('🎤 Final voice input:', transcript);
            handleMessage(transcript);
          } else {
            interim = event.results[i][0].transcript;
          }
        }
        
        setCurrentMessage(interim);
      };
      
      recognition.onend = () => {
        setIsListening(false);
        setCurrentMessage('');
        console.log('🎤 Voice recognition ended');
      };
      
      recognition.onerror = (event) => {
        console.error('❌ Speech recognition error:', event.error);
        setIsListening(false);
        setCurrentMessage('');
        actions.addNotification({
          type: 'error',
          message: `Ошибка распознавания речи: ${event.error}`
        });
      };
      
      recognitionRef.current = recognition;
      console.log('✅ Speech recognition initialized');
    } else {
      console.warn('⚠️ Speech recognition not supported');
    }
  };

  const initSpeechSynthesis = () => {
    if ('speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;
      console.log('✅ Speech synthesis initialized');
    } else {
      console.warn('⚠️ Speech synthesis not supported');
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

    try {
      console.log('🤖 Sending message to AI:', text);
      const response = await apiService.sendVoiceMessage(text);
      
      if (response && response.response) {
        const aiMessage = {
          type: 'ai',
          text: response.response,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiMessage]);
        
        // Text-to-speech for AI response
        speakText(response.response);
        
        actions.addNotification({
          type: 'success',
          message: 'AI ответ получен'
        });
      } else {
        throw new Error('Нет ответа от AI');
      }
    } catch (error) {
      console.error('❌ AI chat error:', error);
      const errorMessage = {
        type: 'ai',
        text: 'Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз.',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
      
      actions.addNotification({
        type: 'error',
        message: 'Ошибка AI чата'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const speakText = (text) => {
    if (synthRef.current && text) {
      synthRef.current.cancel(); // Cancel any ongoing speech
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ru-RU';
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 0.8;
      
      synthRef.current.speak(utterance);
      console.log('🔊 Speaking AI response');
    }
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setIsListening(true);
      setCurrentMessage('');
      recognitionRef.current.start();
      console.log('🎤 Started listening...');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
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
      type: 'ai',
      text: 'Чат очищен. Чем могу помочь?',
      timestamp: new Date()
    }]);
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Чат</h1>
          <p className="text-gray-600">Голосовое и текстовое общение с VasDom AI</p>
        </div>
        <Button variant="secondary" onClick={clearChat}>
          🗑️ Очистить чат
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Messages */}
        <div className="lg:col-span-2">
          <Card className="h-96 flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : message.isError
                        ? 'bg-red-100 text-red-800 border border-red-200'
                        : 'bg-gray-100 text-gray-800'
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
                  <div className="bg-gray-100 rounded-lg p-4">
                    <LoadingSpinner size="sm" text="AI думает..." />
                  </div>
                </div>
              )}
              
              {currentMessage && (
                <div className="flex justify-end">
                  <div className="bg-blue-200 text-blue-800 px-4 py-2 rounded-lg max-w-xs lg:max-w-md">
                    <p className="text-sm">{currentMessage}</p>
                    <p className="text-xs opacity-70">Говорите...</p>
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
                  placeholder="Введите сообщение..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isProcessing}
                />
                <Button type="submit" disabled={!textInput.trim() || isProcessing}>
                  📤 Отправить
                </Button>
              </form>
            </div>
          </Card>
        </div>

        {/* Voice Controls */}
        <div className="space-y-4">
          <Card title="🎤 Голосовое управление">
            <div className="space-y-4">
              <div className="text-center">
                <Button
                  onClick={isListening ? stopListening : startListening}
                  variant={isListening ? 'danger' : 'primary'}
                  size="lg"
                  className="w-full"
                  disabled={isProcessing}
                >
                  {isListening ? '⏹️ Остановить' : '🎤 Начать говорить'}
                </Button>
              </div>
              
              {!('webkitSpeechRecognition' in window) && (
                <p className="text-sm text-red-600 text-center">
                  Голосовое распознавание не поддерживается в этом браузере
                </p>
              )}
              
              {isListening && (
                <div className="text-center">
                  <div className="inline-block w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
                  <p className="text-sm text-gray-600 mt-2">Слушаю...</p>
                </div>
              )}
            </div>
          </Card>

          <Card title="💡 Подсказки">
            <div className="space-y-2 text-sm text-gray-600">
              <p>• "Сколько у нас домов?"</p>
              <p>• "Покажи статистику по бригадам"</p>
              <p>• "Какие дома требуют внимания?"</p>
              <p>• "Как дела с планерками?"</p>
            </div>
          </Card>

          <Card title="📊 Статистика чата">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Сообщений:</span>
                <span className="font-semibold">{messages.length}</span>
              </div>
              <div className="flex justify-between">
                <span>Статус AI:</span>
                <span className="text-green-600">✅ Активен</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AIChat;