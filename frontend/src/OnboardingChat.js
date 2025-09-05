import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const OnboardingChat = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [userProfile, setUserProfile] = useState({});
  const [chatMessages, setChatMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const onboardingQuestions = [
    {
      id: 'greeting',
      message: 'Привет! Я МАКС, ваш AI-ассистент! Давайте знакомиться. Как вас зовут?',
      field: 'name',
      type: 'text'
    },
    {
      id: 'role',
      message: 'Отлично! Какова ваша роль в компании?',
      field: 'role',
      type: 'select',
      options: ['Генеральный директор', 'Директор', 'Менеджер', 'Бухгалтер', 'Сотрудник']
    },
    {
      id: 'experience',
      message: 'Сколько лет вы работаете в клининговом бизнесе?',
      field: 'experience',
      type: 'text'
    },
    {
      id: 'goals',
      message: 'Какие основные цели и задачи у вас в компании?',
      field: 'goals',
      type: 'textarea'
    },
    {
      id: 'challenges',
      message: 'С какими основными проблемами вы сталкиваетесь в работе?',
      field: 'challenges',
      type: 'textarea'
    },
    {
      id: 'expectations',
      message: 'Что вы ожидаете от AI-ассистента? Как я могу лучше всего помочь?',
      field: 'expectations',
      type: 'textarea'
    },
    {
      id: 'schedule',
      message: 'Расскажите о вашем обычном рабочем дне и графике',
      field: 'schedule',
      type: 'textarea'
    },
    {
      id: 'preferences',
      message: 'Как вы предпочитаете получать информацию: подробно или кратко? Часто или только важное?',
      field: 'preferences',
      type: 'textarea'
    }
  ];

  useEffect(() => {
    // Start with greeting
    if (chatMessages.length === 0) {
      setChatMessages([{
        type: 'ai',
        content: onboardingQuestions[0].message,
        timestamp: new Date()
      }]);
    }
  }, []);

  const handleAnswer = async (answer) => {
    const currentQuestion = onboardingQuestions[currentStep];
    
    // Add user message
    setChatMessages(prev => [...prev, {
      type: 'user',
      content: answer,
      timestamp: new Date()
    }]);

    // Save answer to profile
    const newProfile = {
      ...userProfile,
      [currentQuestion.field]: answer
    };
    setUserProfile(newProfile);

    setIsLoading(true);

    try {
      // Send to AI for processing and storage
      await axios.post(`${BACKEND_URL}/api/user/profile/update`, {
        field: currentQuestion.field,
        value: answer,
        profile: newProfile
      });

      // Move to next question
      if (currentStep < onboardingQuestions.length - 1) {
        setTimeout(() => {
          const nextQuestion = onboardingQuestions[currentStep + 1];
          setChatMessages(prev => [...prev, {
            type: 'ai',
            content: nextQuestion.message,
            timestamp: new Date()
          }]);
          setCurrentStep(currentStep + 1);
          setIsLoading(false);
        }, 1000);
      } else {
        // Onboarding complete
        const finalMessage = `Отлично, ${newProfile.name}! Теперь я знаю вас лучше и смогу предоставить персонализированную помощь. 

📋 **Ваш профиль сохранен:**
👤 Имя: ${newProfile.name}
💼 Роль: ${newProfile.role}
⭐ Опыт: ${newProfile.experience}
🎯 Цели: ${newProfile.goals}

Теперь я буду учитывать ваши предпочтения и стиль работы во всех наших взаимодействиях. Готов помочь с управлением компанией!`;

        setChatMessages(prev => [...prev, {
          type: 'ai',
          content: finalMessage,
          timestamp: new Date()
        }]);

        setTimeout(() => {
          onComplete(newProfile);
        }, 3000);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      setIsLoading(false);
    }
  };

  const handleTextSubmit = () => {
    if (inputMessage.trim()) {
      handleAnswer(inputMessage);
      setInputMessage('');
    }
  };

  const currentQuestion = onboardingQuestions[currentStep];
  
  return (
    <div className="onboarding-chat min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-3xl">🤖</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Знакомство с МАКС</h1>
          <p className="text-gray-600">Давайте познакомимся, чтобы я мог лучше помочь вам</p>
          
          {/* Progress Bar */}
          <div className="mt-6 bg-gray-200 rounded-full h-2 max-w-md mx-auto">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / onboardingQuestions.length) * 100}%` }}
            />
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Шаг {currentStep + 1} из {onboardingQuestions.length}
          </p>
        </div>

        {/* Chat Messages */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6 max-h-96 overflow-y-auto">
          <div className="space-y-4">
            {chatMessages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                    message.type === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input Section */}
        {currentStep < onboardingQuestions.length && !isLoading && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            {currentQuestion.type === 'select' ? (
              <div className="space-y-3">
                <p className="font-medium text-gray-800">Выберите вариант:</p>
                <div className="grid grid-cols-1 gap-2">
                  {currentQuestion.options.map((option, index) => (
                    <button
                      key={index}
                      onClick={() => handleAnswer(option)}
                      className="text-left p-3 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {currentQuestion.type === 'textarea' ? (
                  <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Расскажите подробнее..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={4}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && e.ctrlKey) {
                        handleTextSubmit();
                      }
                    }}
                  />
                ) : (
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Введите ваш ответ..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleTextSubmit();
                      }
                    }}
                  />
                )}
                
                <div className="flex justify-between items-center">
                  <p className="text-sm text-gray-500">
                    {currentQuestion.type === 'textarea' ? 'Ctrl+Enter для отправки' : 'Enter для отправки'}
                  </p>
                  <button
                    onClick={handleTextSubmit}
                    disabled={!inputMessage.trim()}
                    className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Ответить
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Skip Option */}
        {currentStep > 0 && currentStep < onboardingQuestions.length && !isLoading && (
          <div className="text-center mt-4">
            <button
              onClick={() => handleAnswer('Пропустить')}
              className="text-gray-500 text-sm hover:text-gray-700"
            >
              Пропустить этот вопрос
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default OnboardingChat;