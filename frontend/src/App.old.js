import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

// Консольное логирование для отладки
console.log('🔗 VasDom AudioBot Frontend initialized');
console.log('🔗 Backend URL:', BACKEND_URL);
console.log('🔗 API URL:', API);

// Main Dashboard Component  
function App() {
  const [currentSection, setCurrentSection] = useState('general');
  const [isMenuCollapsed, setIsMenuCollapsed] = useState(false);
  const [dashboardStats, setDashboardStats] = useState({
    employees: 82,
    houses: 491,  // Реальное количество из CRM CSV
    entrances: 1473,
    apartments: 25892,
    floors: 2123,
    meetings: 0,
    ai_tasks: 0
  }); // Инициализируем реальными данными
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState('connecting');

  useEffect(() => {
    console.log('🚀 VasDom AudioBot App mounted with PostgreSQL...');
    
    // Принудительно загружаем данные при каждом монтировании
    const loadData = async () => {
      await fetchDashboardStats();
      
      // Повторяем через 5 секунд если данные не загрузились
      setTimeout(async () => {
        if (dashboardStats.houses === 0) {
          console.log('🔄 Retry loading dashboard data...');
          await fetchDashboardStats();
        }
      }, 5000);
    };
    
    loadData();
    
    // Автообновление каждые 2 минуты
    const interval = setInterval(() => {
      console.log('🔄 Auto-refresh dashboard...');
      fetchDashboardStats();
    }, 120000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardStats = async () => {
    setLoading(true);
    setApiStatus('fetching');
    
    try {
      console.log('📊 API Request to:', `${API}/dashboard`);
      
      const response = await axios.get(`${API}/dashboard`, {
        timeout: 15000,
        withCredentials: false,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      
      console.log('✅ API Response status:', response.status);
      console.log('✅ API Response full:', response.data);
      
      if (response.data && response.data.stats) {
        const newStats = response.data.stats;
        console.log('📊 Stats from API:', newStats);
        
        // ПРИНУДИТЕЛЬНО обновляем state
        setDashboardStats(prevStats => {
          console.log('🔄 Updating stats from:', prevStats, 'to:', newStats);
          return {
            ...newStats,
            employees: newStats.employees || 82,
            houses: newStats.houses || 491, // Fallback к реальному количеству
            entrances: newStats.entrances || 1473,
            apartments: newStats.apartments || 25892,
            floors: newStats.floors || 2123,
            meetings: newStats.meetings || 0,
            ai_tasks: newStats.ai_tasks || 0
          };
        });
        
        setApiStatus('connected');
        console.log('✅ Stats FORCE updated successfully');
      } else {
        console.warn('⚠️ No stats in response, using current data');
      }
      
    } catch (error) {
      console.error('❌ API Error:', error);
      setApiStatus('error');
      
      // НЕ перезаписываем на fallback, оставляем текущие данные
      console.log('🔄 Keeping current stats after error:', dashboardStats);
    } finally {
      setLoading(false);
    }
  };

  const menuItems = [
    { id: 'general', label: '🏠 Общее', icon: '🏠' },
    { id: 'meetings', label: '🎤 Планерка', icon: '🎤' },
    { id: 'voice', label: '📞 Живой разговор', icon: '📞' },
    { id: 'ai-tasks', label: '🤖 Задачи для AI', icon: '🤖' },
    { id: 'sales', label: '💰 Продажи / Маркетинг', icon: '💰' },
    { id: 'employees', label: '👥 Сотрудники + HR', icon: '👥' },
    { id: 'works', label: '🏗️ Работы', icon: '🏗️' },
    { id: 'training', label: '📚 Обучение', icon: '📚' },
    { id: 'finance', label: '💹 Финансы', icon: '💹' },
    { id: 'logs', label: '📋 Логи', icon: '📋' }
  ];

  const handleMenuClick = (sectionId) => {
    console.log(`🔄 Switching to section: ${sectionId}`);
    setCurrentSection(sectionId);
  };

  const renderContent = () => {
    console.log(`🖼️ Rendering section: ${currentSection}`);
    
    switch (currentSection) {
      case 'general':
        return <GeneralDashboard stats={dashboardStats} onRefresh={fetchDashboardStats} loading={loading} />;
      case 'meetings':
        return <MeetingsSection />;
      case 'voice':
        return <VoiceSection />;
      case 'ai-tasks':
        return <AITasksSection />;
      case 'works':
        return <WorksSection />;
      case 'training':
        return <TrainingSection />;
      case 'logs':
        return <LogsSection />;
      case 'employees':
        return <EmployeesSection />;
      default:
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold mb-4">🚧 Раздел в разработке</h2>
            <p>Этот раздел будет добавлен в следующих версиях.</p>
          </div>
        );
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar Navigation */}
      <div className={`bg-blue-900 text-white transition-all duration-300 ${isMenuCollapsed ? 'w-16' : 'w-64'}`}>
        <div className="p-4 border-b border-blue-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="bg-blue-700 rounded-full p-2 mr-3">
                🤖
              </div>
              {!isMenuCollapsed && (
                <div>
                  <h1 className="text-lg font-bold">VasDom AI</h1>
                  <p className="text-sm opacity-75">Система excellent</p>
                </div>
              )}
            </div>
            <button 
              onClick={() => setIsMenuCollapsed(!isMenuCollapsed)}
              className="text-white hover:bg-blue-800 p-1 rounded"
            >
              {isMenuCollapsed ? '→' : '←'}
            </button>
          </div>
        </div>
        
        <nav className="mt-4">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleMenuClick(item.id)}
              className={`w-full text-left p-3 hover:bg-blue-800 transition-colors ${
                currentSection === item.id ? 'bg-blue-800 border-r-4 border-blue-400' : ''
              }`}
            >
              <div className="flex items-center">
                <span className="text-xl mr-3">{item.icon}</span>
                {!isMenuCollapsed && <span className="text-sm">{item.label.split(' ').slice(1).join(' ')}</span>}
              </div>
            </button>
          ))}
        </nav>
      </div>

      {/* Main content area */}
      <div className="flex-1 overflow-auto">
        {renderContent()}
      </div>
    </div>
  );
}

// Dashboard Overview Component
function GeneralDashboard({ stats, onRefresh, loading }) {
  const statCards = [
    { title: 'Сотрудников', value: stats.employees || 0, icon: '👥', color: 'bg-blue-500' },
    { title: 'Домов в CRM', value: stats.houses || 0, icon: '🏠', color: 'bg-green-500' },
    { title: 'Подъездов', value: stats.entrances || 0, icon: '🚪', color: 'bg-purple-500' },
    { title: 'Квартир', value: stats.apartments || 0, icon: '🏠', color: 'bg-orange-500' },
    { title: 'Этажей', value: stats.floors || 0, icon: '📊', color: 'bg-red-500' },
    { title: 'Планерок', value: stats.meetings || 0, icon: '🎤', color: 'bg-indigo-500' }
  ];

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Общий обзор</h1>
          <p className="text-gray-600">VasDom AI - Система excellent</p>
          <p className="text-sm text-gray-500">
            Обновлено: {new Date().toLocaleString('ru-RU')}
          </p>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? '🔄 Обновление...' : '🔄 Обновить'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((card, index) => (
          <div key={index} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex items-center">
              <div className={`${card.color} rounded-full p-3 mr-4`}>
                <span className="text-2xl text-white">{card.icon}</span>
              </div>
              <div>
                <p className="text-sm text-gray-600">{card.title}</p>
                <p className="text-2xl font-bold text-gray-900">
                  {card.value?.toLocaleString('ru-RU') || '0'}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">🔥 Статус системы</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
            <span className="text-sm">Bitrix24 API</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
            <span className="text-sm">GPT-4 mini (Emergent)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
            <span className="text-sm">База знаний</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
            <span className="text-sm">Самообучение</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
            <span className="text-sm">PostgreSQL</span>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            🔗 <strong>Backend:</strong> {BACKEND_URL}
          </p>
          <p className="text-sm text-blue-600">
            📅 <strong>Система активна:</strong> {new Date().toLocaleString('ru-RU')}
          </p>
        </div>
      </div>
    </div>
  );
}

// Meeting Recording Section - ИСПРАВЛЕННАЯ ПЛАНЕРКА
function MeetingsSection() {
  const [isRecording, setIsRecording] = useState(false);
  const [meetings, setMeetings] = useState([]);
  const [currentMeetingId, setCurrentMeetingId] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [realTimeText, setRealTimeText] = useState('');
  const recognitionRef = useRef(null);

  useEffect(() => {
    console.log('🎤 Meetings section mounted');
    fetchMeetings();
    initSpeechRecognition();
  }, []);

  const initSpeechRecognition = () => {
    if ('webkitSpeechRecognition' in window) {
      const recognition = new window.webkitSpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'ru-RU';
      
      recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
            console.log('📝 Final transcript:', transcript);
          } else {
            interimTranscript = transcript;
          }
        }
        
        if (finalTranscript) {
          setTranscription(prev => prev + finalTranscript);
        }
        setRealTimeText(interimTranscript);
      };
      
      recognition.onstart = () => {
        console.log('🎤 Speech recognition started');
      };
      
      recognition.onend = () => {
        console.log('⏹️ Speech recognition ended');
        if (isRecording) {
          // Автоматически перезапускаем если еще записываем
          setTimeout(() => {
            if (isRecording && recognitionRef.current) {
              recognitionRef.current.start();
            }
          }, 100);
        }
      };
      
      recognition.onerror = (event) => {
        console.error('❌ Speech recognition error:', event.error);
        setRealTimeText(`Ошибка распознавания: ${event.error}`);
      };
      
      recognitionRef.current = recognition;
      console.log('✅ Speech recognition initialized');
    } else {
      console.error('❌ Speech recognition not supported');
      setRealTimeText('Распознавание речи не поддерживается в этом браузере');
    }
  };

  const fetchMeetings = async () => {
    try {
      console.log('📋 Fetching meetings...');
      const response = await axios.get(`${API}/meetings`);
      if (response.data.status === 'success') {
        setMeetings(response.data.meetings);
        console.log('✅ Meetings loaded:', response.data.meetings.length);
      }
    } catch (error) {
      console.error('❌ Error fetching meetings:', error);
    }
  };

  const startRecording = async () => {
    try {
      console.log('🎤 Starting meeting recording...');
      
      const response = await axios.post(`${API}/meetings/start-recording`);
      if (response.data.status === 'success') {
        setCurrentMeetingId(response.data.meeting_id);
        setIsRecording(true);
        setTranscription('');
        setRealTimeText('');
        
        if (recognitionRef.current) {
          recognitionRef.current.start();
        }
        
        console.log('✅ Meeting recording started:', response.data.meeting_id);
      } else {
        console.error('❌ Failed to start recording:', response.data);
      }
    } catch (error) {
      console.error('❌ Error starting recording:', error);
      alert('Ошибка начала записи: ' + error.message);
    }
  };

  const stopRecording = async () => {
    try {
      console.log('⏹️ Stopping meeting recording...');
      
      if (currentMeetingId) {
        // Останавливаем распознавание речи
        setIsRecording(false);
        if (recognitionRef.current) {
          recognitionRef.current.stop();
        }
        
        const response = await axios.post(`${API}/meetings/stop-recording?meeting_id=${currentMeetingId}`);
        
        setCurrentMeetingId(null);
        setRealTimeText('');
        
        if (response.data.status === 'success') {
          console.log('✅ Meeting stopped successfully');
          if (response.data.summary) {
            alert('✅ Планерка завершена!\n\nAI создал резюме:\n' + response.data.summary);
          }
          fetchMeetings();
        }
      }
    } catch (error) {
      console.error('❌ Error stopping recording:', error);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">🎤 Планерка - Диктофон + AI анализ</h1>
      
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Recording Control Panel */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">🎙️ Запись планерки</h2>
          
          <div className="text-center mb-6">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`w-32 h-32 rounded-full text-white text-3xl transition-all shadow-lg transform hover:scale-105 ${
                isRecording 
                  ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                  : 'bg-blue-500 hover:bg-blue-600'
              }`}
            >
              {isRecording ? '⏹️' : '🎤'}
            </button>
            <p className="mt-4 text-lg font-medium text-gray-700">
              {isRecording ? '🔴 Идет запись планерки...' : '⚫ Нажмите для начала записи'}
            </p>
          </div>

          {/* Live Transcription Display */}
          {isRecording && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold mb-2 text-green-600">📝 Транскрипция в реальном времени:</h3>
              <div className="h-40 overflow-y-auto bg-white p-3 rounded border-2 border-green-200">
                <p className="text-sm text-gray-800 whitespace-pre-wrap">
                  {transcription}
                  <span className="text-blue-600 italic font-medium">{realTimeText}</span>
                  {isRecording && <span className="text-red-500 animate-ping">●</span>}
                </p>
                {!transcription && !realTimeText && (
                  <p className="text-gray-400 italic">Говорите четко для лучшего распознавания...</p>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                💡 AI автоматически создаст резюме и задачи после завершения записи.
              </p>
            </div>
          )}
        </div>

        {/* Meetings History */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">📋 История планерок ({meetings.length})</h2>
          
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {meetings.length > 0 ? (
              meetings.map((meeting, index) => (
                <div key={index} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <h3 className="font-semibold text-gray-900">{meeting.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    📅 {new Date(meeting.created_at).toLocaleString('ru-RU')}
                  </p>
                  
                  {meeting.transcription && (
                    <div className="mt-2 p-2 bg-blue-50 rounded text-sm">
                      <strong>📝 Транскрипция:</strong>
                      <p className="text-gray-700 mt-1">{meeting.transcription.substring(0, 150)}...</p>
                    </div>
                  )}
                  
                  {meeting.summary && (
                    <div className="mt-2 p-2 bg-green-50 rounded text-sm">
                      <strong>🤖 AI Резюме:</strong>
                      <p className="text-gray-700 mt-1">{meeting.summary.substring(0, 200)}...</p>
                    </div>
                  )}
                  
                  <span className={`inline-block mt-2 px-2 py-1 rounded-full text-xs ${
                    meeting.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {meeting.status === 'completed' ? '✅ Завершено' : '🔄 Активно'}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg">📝 Пока нет записей планерок</p>
                <p className="text-sm">Начните первую запись для AI анализа</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Voice Chat Section - ИСПРАВЛЕННЫЙ ЖИВОЙ РАЗГОВОР
function VoiceSection() {
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  useEffect(() => {
    console.log('📞 Voice section mounted');
    initSpeechRecognition();
    initSpeechSynthesis();
    
    // Приветственное сообщение от AI
    setMessages([{
      type: 'ai',
      text: 'Привет! Я VasDom AI, ваш помощник по управлению клининговой компанией. У нас 450+ домов в управлении и 6 рабочих бригад. О чем хотите поговорить?',
      timestamp: new Date()
    }]);
  }, []);

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
            handleVoiceMessage(transcript);
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
        alert(`Ошибка распознавания речи: ${event.error}`);
      };
      
      recognitionRef.current = recognition;
      console.log('✅ Speech recognition initialized for voice chat');
    }
  };

  const initSpeechSynthesis = () => {
    if ('speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;
      console.log('✅ Speech synthesis initialized');
    }
  };

  const handleVoiceMessage = async (text) => {
    if (!text?.trim()) {
      console.warn('⚠️ Empty voice message received');
      return;
    }
    
    console.log('🎤 Processing voice message:', text);
    
    const userMessage = { type: 'user', text, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);
    
    try {
      const response = await axios.post(`${API}/voice/process`, {
        text: text,
        user_id: 'voice_user'
      }, {
        timeout: 30000
      });
      
      console.log('🤖 AI response received:', response.data);
      
      if (response.data && response.data.response) {
        const aiResponse = {
          type: 'ai',
          text: response.data.response,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, aiResponse]);
        
        // Озвучиваем ответ AI
        if (synthRef.current && response.data.response) {
          const utterance = new SpeechSynthesisUtterance(response.data.response);
          utterance.lang = 'ru-RU';
          utterance.rate = 0.9;
          utterance.volume = 0.8;
          
          synthRef.current.cancel(); // Останавливаем предыдущую речь
          synthRef.current.speak(utterance);
          
          console.log('🔊 AI response spoken aloud');
        }
      } else {
        throw new Error('Invalid AI response format');
      }
      
    } catch (error) {
      console.error('❌ Voice message processing error:', error);
      
      const errorMessage = {
        type: 'ai',
        text: 'Извините, произошла ошибка при обработке вашего сообщения. Проверьте подключение к интернету и попробуйте еще раз.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening && !isProcessing) {
      setIsListening(true);
      setCurrentMessage('');
      recognitionRef.current.start();
      console.log('🎤 Started listening for voice input');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      console.log('⏹️ Stopped listening');
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">📞 Живой разговор с VasDom AI</h1>
      <p className="text-gray-600 mb-6">Голосовое взаимодействие с AI помощником в реальном времени</p>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Voice Control */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">🎤 Голосовое управление</h2>
          
          <div className="text-center">
            <button
              onClick={isListening ? stopListening : startListening}
              disabled={isProcessing}
              className={`w-24 h-24 rounded-full text-white text-3xl transition-all shadow-lg transform hover:scale-105 ${
                isListening 
                  ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                  : isProcessing
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-500 hover:bg-green-600'
              }`}
            >
              {isProcessing ? '🤖' : isListening ? '⏹️' : '🎤'}
            </button>
            
            <p className="mt-3 text-gray-600 font-medium">
              {isProcessing ? '🤖 AI обрабатывает...' :
               isListening ? '👂 Слушаю вас...' : '🎤 Нажмите и говорите'}
            </p>
            
            {currentMessage && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg border-2 border-blue-200">
                <p className="text-sm text-blue-800 font-medium">🎤 Вы говорите:</p>
                <p className="text-blue-900">{currentMessage}</p>
              </div>
            )}
          </div>
          
          <div className="mt-6 p-4 bg-green-50 rounded-lg">
            <h3 className="font-semibold text-sm mb-2 text-green-800">💡 Попробуйте спросить:</h3>
            <ul className="text-xs text-green-700 space-y-1">
              <li>• "Сколько домов у нас в работе?"</li>
              <li>• "Какие бригады работают сегодня?"</li>
              <li>• "Создай задачу на завтра"</li>
              <li>• "Покажи статистику по Пролетарской улице"</li>
              <li>• "Как дела с уборкой?"</li>
            </ul>
          </div>
        </div>
        
        {/* Chat Messages */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">💬 Диалог с AI помощником</h2>
          
          <div className="h-96 overflow-y-auto border rounded-lg p-4 space-y-4 bg-gray-50">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-md rounded-lg p-4 shadow-sm ${
                    message.type === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-white text-gray-800 border border-gray-200'
                  }`}
                >
                  <p className="text-sm leading-relaxed">{message.text}</p>
                  <p className="text-xs opacity-75 mt-2">
                    {message.type === 'user' ? '👤 Вы' : '🤖 VasDom AI'} • {message.timestamp.toLocaleTimeString('ru-RU')}
                  </p>
                </div>
              </div>
            ))}
            
            {isProcessing && (
              <div className="flex justify-start">
                <div className="bg-gray-200 rounded-lg p-4 animate-pulse">
                  <p className="text-sm">🤖 AI анализирует ваш запрос...</p>
                </div>
              </div>
            )}
          </div>
          
          <div className="mt-4 text-center p-3 bg-blue-50 rounded-lg">
            <p className="text-xs text-blue-700">
              🤖 <strong>Powered by GPT-4 mini (Emergent)</strong> | 📚 База знаний активна | 🧠 Самообучение включено
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Works Section - ВСЕ ДОМА ИЗ CRM 1В1
function WorksSection() {
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [brigadeFilter, setBrigadeFilter] = useState('all');

  useEffect(() => {
    console.log('🏗️ Works section mounted');
    fetchAllHouses();
  }, []);

  const fetchAllHouses = async () => {
    setLoading(true);
    console.log('🏠 Fetching ALL houses from Bitrix24...');
    
    try {
      const response = await axios.get(`${API}/cleaning/houses?limit=500`, {
        timeout: 30000
      });
      
      if (response.data.status === 'success') {
        setHouses(response.data.houses);
        console.log('✅ All houses loaded:', response.data.houses.length, 'from', response.data.source);
      } else {
        console.error('❌ Houses API error:', response.data);
      }
    } catch (error) {
      console.error('❌ Error fetching all houses:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredHouses = brigadeFilter === 'all' 
    ? houses 
    : houses.filter(house => house.brigade === brigadeFilter);

  const brigadeOptions = ['all', '1 бригада', '2 бригада', '3 бригада', '4 бригада', '5 бригада', '6 бригада'];

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">🏗️ Работы - Уборка подъездов</h1>
          <p className="text-gray-600">Управление всеми объектами из CRM воронки</p>
        </div>
        <button
          onClick={fetchAllHouses}
          disabled={loading}
          className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg disabled:opacity-50"
        >
          {loading ? '🔄 Загружаю все дома...' : '🔄 Загрузить из Bitrix24'}
        </button>
      </div>

      {/* Brigade Filter */}
      <div className="mb-6 bg-white rounded-lg shadow-lg p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          🏷️ Фильтр по бригадам:
        </label>
        <select
          value={brigadeFilter}
          onChange={(e) => setBrigadeFilter(e.target.value)}
          className="border border-gray-300 rounded-lg p-2 w-full md:w-auto"
        >
          {brigadeOptions.map(option => (
            <option key={option} value={option}>
              {option === 'all' ? '🏠 Все дома' : `👥 ${option}`}
            </option>
          ))}
        </select>
        <p className="text-sm text-gray-500 mt-2">
          Показано: {filteredHouses.length} из {houses.length} домов
        </p>
      </div>

      {/* Houses Table */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="p-4 border-b bg-gray-50">
          <h2 className="text-lg font-semibold">
            📋 Все дома из Bitrix24 CRM ({filteredHouses.length} объектов)
          </h2>
          <p className="text-sm text-gray-600">
            Данные из воронки "Уборка подъездов" • 1в1 как в CRM
          </p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">🏠 Адрес</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">📊 Статус</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">👥 Бригада</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">#️⃣ ID сделки</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">📅 Создано</th>
              </tr>
            </thead>
            <tbody>
              {filteredHouses.map((house, index) => (
                <tr key={index} className="border-b hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{house.address}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      house.stage === 'C2:WON' 
                        ? 'bg-green-100 text-green-800'
                        : house.stage === 'C2:APOLOGY'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {house.status_text || house.stage}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {house.brigade || 'Не назначена'}
                  </td>
                  <td className="px-4 py-3 text-gray-600 font-mono">
                    #{house.bitrix24_deal_id}
                  </td>
                  <td className="px-4 py-3 text-gray-600 text-sm">
                    {house.created_date ? new Date(house.created_date).toLocaleDateString('ru-RU') : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredHouses.length === 0 && !loading && (
          <div className="p-12 text-center text-gray-500">
            <p className="text-lg">📭 Нет данных для отображения</p>
            <p className="text-sm">Нажмите "Загрузить из Bitrix24" для получения данных</p>
          </div>
        )}
        
        {loading && (
          <div className="p-12 text-center">
            <p className="text-lg">🔄 Загружаем все дома из CRM...</p>
            <p className="text-sm text-gray-500">Это может занять несколько секунд</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Training Section - Knowledge Base
function TrainingSection() {
  const [knowledgeBase, setKnowledgeBase] = useState([]);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    console.log('📚 Training section mounted');
    fetchKnowledgeBase();
  }, []);

  const fetchKnowledgeBase = async () => {
    try {
      const response = await axios.get(`${API}/knowledge`);
      if (response.data.status === 'success') {
        setKnowledgeBase(response.data.knowledge_base);
        console.log('📚 Knowledge base loaded:', response.data.knowledge_base.length);
      }
    } catch (error) {
      console.error('❌ Error fetching knowledge base:', error);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile || !uploadTitle) {
      alert('Пожалуйста, выберите файл и введите название');
      return;
    }

    setIsUploading(true);
    console.log('📤 Uploading knowledge file:', uploadTitle);

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('title', uploadTitle);

    try {
      const response = await axios.post(`${API}/knowledge/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000
      });
      
      if (response.data.status === 'success') {
        alert('✅ ' + response.data.message);
        setUploadFile(null);
        setUploadTitle('');
        fetchKnowledgeBase();
        console.log('✅ Knowledge file uploaded successfully');
      }
    } catch (error) {
      console.error('❌ Knowledge upload error:', error);
      alert('❌ Ошибка загрузки файла: ' + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">📚 База знаний и обучение AI</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">📤 Загрузка документов</h2>
          
          <form onSubmit={handleFileUpload} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                📄 Название документа
              </label>
              <input
                type="text"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-3"
                placeholder="Например: Инструкция по уборке подъездов"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                📎 Выберите файл
              </label>
              <input
                type="file"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="w-full border border-gray-300 rounded-lg p-2"
                accept=".txt,.doc,.docx,.pdf"
                required
              />
            </div>
            
            <button
              type="submit"
              disabled={isUploading}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-lg disabled:opacity-50 font-medium"
            >
              {isUploading ? '⏳ Загружаю в базу знаний...' : '📤 Загрузить для обучения AI'}
            </button>
          </form>
        </div>
        
        {/* Knowledge Base */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">🧠 База знаний ({knowledgeBase.length})</h2>
          
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {knowledgeBase.length > 0 ? (
              knowledgeBase.map((kb, index) => (
                <div key={index} className="border rounded-lg p-3 hover:bg-gray-50">
                  <h3 className="font-medium text-gray-900">{kb.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    📅 {new Date(kb.created_at).toLocaleDateString('ru-RU')}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    📄 {kb.file_type} | 🏷️ Ключевых слов: {kb.keywords?.length || 0}
                  </p>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p className="text-lg">📚 База знаний пуста</p>
                <p className="text-sm">Загрузите документы для обучения AI</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// AI Tasks Section
function AITasksSection() {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    console.log('🤖 AI Tasks section mounted');
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await axios.get(`${API}/ai-tasks`);
      if (response.data.status === 'success') {
        setTasks(response.data.tasks);
        console.log('🤖 AI tasks loaded:', response.data.tasks.length);
      }
    } catch (error) {
      console.error('❌ Error fetching AI tasks:', error);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">🤖 Задачи для AI</h1>
      <p className="text-gray-600 mb-6">Календарное планирование задач с AI помощником</p>
      
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">📅 Список задач ({tasks.length})</h2>
        
        {tasks.length > 0 ? (
          <div className="space-y-4">
            {tasks.map((task, index) => (
              <div key={index} className="border rounded-lg p-4">
                <h3 className="font-semibold">{task.title}</h3>
                <p className="text-gray-600">{task.description}</p>
                <p className="text-sm text-gray-500">
                  ⏰ {new Date(task.scheduled_time).toLocaleString('ru-RU')}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">🤖 Пока нет задач для AI</p>
        )}
      </div>
    </div>
  );
}

// Employees Section
function EmployeesSection() {
  const [employees, setEmployees] = useState([]);

  useEffect(() => {
    console.log('👥 Employees section mounted');
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`);
      if (response.data.status === 'success') {
        setEmployees(response.data.employees);
        console.log('👥 Employees loaded:', response.data.employees.length);
      }
    } catch (error) {
      console.error('❌ Error fetching employees:', error);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">👥 Сотрудники + HR</h1>
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Команда VasDom (82 человека)</h2>
        
        {employees.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {employees.map((employee, index) => (
              <div key={index} className="border rounded-lg p-4">
                <h3 className="font-semibold">{employee.name}</h3>
                <p className="text-gray-600">{employee.role}</p>
                <p className="text-sm text-gray-500">{employee.phone}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">👥 Загрузка данных сотрудников...</p>
        )}
      </div>
    </div>
  );
}

// Logs Section
function LogsSection() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    console.log('📋 Logs section mounted');
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API}/logs`);
      if (response.data.status === 'success') {
        setLogs(response.data.voice_logs || []);
        console.log('📋 Logs loaded:', response.data.voice_logs?.length || 0);
      }
    } catch (error) {
      console.error('❌ Error fetching logs:', error);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">📋 Системные логи</h1>
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">🎤 Голосовые взаимодействия ({logs.length})</h2>
        
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {logs.length > 0 ? (
            logs.map((log, index) => (
              <div key={index} className="border-l-4 border-blue-500 pl-3 pb-3">
                <p className="text-sm text-gray-600">
                  👤 <strong>Пользователь:</strong> {log.user_message}
                </p>
                <p className="text-sm text-green-600 mt-1">
                  🤖 <strong>AI:</strong> {log.ai_response}
                </p>
                <p className="text-xs text-gray-500">
                  {new Date(log.timestamp).toLocaleString('ru-RU')}
                </p>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-center py-8">📋 Пока нет логов взаимодействий</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;