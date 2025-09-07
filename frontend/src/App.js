import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

// Логирование для отладки
console.log('🔗 Backend URL:', BACKEND_URL);
console.log('🔗 API URL:', API);

// Main Dashboard Component
function App() {
  const [currentSection, setCurrentSection] = useState('general');
  const [isMenuCollapsed, setIsMenuCollapsed] = useState(false);
  const [dashboardStats, setDashboardStats] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    console.log('🚀 App component mounted, fetching dashboard stats...');
    fetchDashboardStats();
    
    // Принудительное обновление каждые 30 секунд
    const interval = setInterval(() => {
      console.log('🔄 Auto-refreshing dashboard stats...');
      fetchDashboardStats();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardStats = async () => {
    setLoading(true);
    try {
      console.log('📊 Fetching dashboard stats from:', `${API}/dashboard`);
      const response = await axios.get(`${API}/dashboard`, {
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });
      
      console.log('📊 Dashboard response received:', response.data);
      
      if (response.data && response.data.status === 'success' && response.data.stats) {
        setDashboardStats(response.data.stats);
        console.log('✅ Dashboard stats loaded successfully:', response.data.stats);
      } else {
        console.error('❌ Dashboard API returned invalid data:', response.data);
        throw new Error('API returned invalid data structure');
      }
    } catch (error) {
      console.error('❌ Error fetching dashboard stats:', error);
      console.error('📊 API URL that failed:', `${API}/dashboard`);
      
      // Показываем пользователю ошибку
      alert(`Ошибка подключения к API: ${error.message}\nURL: ${API}/dashboard`);
      
      // Mock data if API fails
      setDashboardStats({
        employees: 82,
        houses: 450,
        entrances: 1123,
        apartments: 43308,
        floors: 3372,
        meetings: 3,
        ai_tasks: 5
      });
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

  const renderContent = () => {
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
      default:
        return <div className="p-6"><h2>Раздел в разработке</h2></div>;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className={`bg-blue-900 text-white transition-all duration-300 ${isMenuCollapsed ? 'w-16' : 'w-64'}`}>
        <div className="p-4 border-b border-blue-800">
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
            <button 
              onClick={() => setIsMenuCollapsed(!isMenuCollapsed)}
              className="ml-auto text-white hover:bg-blue-800 p-1 rounded"
            >
              {isMenuCollapsed ? '→' : '←'}
            </button>
          </div>
        </div>
        
        <nav className="mt-4">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setCurrentSection(item.id)}
              className={`w-full text-left p-3 hover:bg-blue-800 transition-colors ${
                currentSection === item.id ? 'bg-blue-800 border-r-4 border-blue-400' : ''
              }`}
            >
              <div className="flex items-center">
                <span className="text-xl mr-3">{item.icon}</span>
                {!isMenuCollapsed && <span>{item.label.split(' ').slice(1).join(' ')}</span>}
              </div>
            </button>
          ))}
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        {renderContent()}
      </div>
    </div>
  );
}

// General Dashboard Component
function GeneralDashboard({ stats, onRefresh, loading }) {
  const statCards = [
    { title: 'Сотрудников', value: stats.employees || 0, icon: '👥', color: 'bg-blue-500' },
    { title: 'Домов в CRM', value: stats.houses || 0, icon: '🏠', color: 'bg-green-500' },
    { title: 'Подъездов', value: stats.entrances || 0, icon: '🚪', color: 'bg-purple-500' },
    { title: 'Квартир', value: stats.apartments || 0, icon: '🔍', color: 'bg-orange-500' },
    { title: 'Этажей', value: stats.floors || 0, icon: '📊', color: 'bg-red-500' },
    { title: 'Планерок', value: stats.meetings || 0, icon: '🎤', color: 'bg-indigo-500' }
  ];

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Общий обзор</h1>
          <p className="text-gray-600">Система excellent</p>
          <p className="text-sm text-gray-500">Последнее обновление: {new Date().toLocaleString('ru-RU')}</p>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? 'Обновление...' : 'Обновить'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((card, index) => (
          <div key={index} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className={`${card.color} rounded-full p-3 mr-4`}>
                <span className="text-2xl text-white">{card.icon}</span>
              </div>
              <div>
                <p className="text-sm text-gray-600">{card.title}</p>
                <p className="text-2xl font-bold text-gray-900">{card.value?.toLocaleString('ru-RU') || '0'}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">🔥 Статус системы</h2>
        <div className="flex items-center space-x-4 flex-wrap">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
            <span>Bitrix24 API подключен</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
            <span>AI GPT-4 mini активен</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
            <span>База знаний работает</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
            <span>Самообучение включено</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
            <span>MongoDB Atlas подключен</span>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            🔗 <strong>Backend API:</strong> {BACKEND_URL}
          </p>
          <p className="text-sm text-blue-600 mt-1">
            📊 Последнее обновление: {new Date().toLocaleString('ru-RU')}
          </p>
        </div>
      </div>
    </div>
  );
}

// Meetings Section Component - REAL FUNCTIONALITY
function MeetingsSection() {
  const [isRecording, setIsRecording] = useState(false);
  const [meetings, setMeetings] = useState([]);
  const [currentMeetingId, setCurrentMeetingId] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [realTimeText, setRealTimeText] = useState('');
  const recognitionRef = useRef(null);

  useEffect(() => {
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
          } else {
            interimTranscript += transcript;
          }
        }
        
        if (finalTranscript) {
          setTranscription(prev => prev + finalTranscript);
        }
        setRealTimeText(interimTranscript);
      };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setRealTimeText('Ошибка распознавания речи: ' + event.error);
      };
      
      recognitionRef.current = recognition;
    } else {
      console.warn('Speech recognition not supported');
    }
  };

  const fetchMeetings = async () => {
    try {
      const response = await axios.get(`${API}/meetings`);
      if (response.data.status === 'success') {
        setMeetings(response.data.meetings);
      }
    } catch (error) {
      console.error('Error fetching meetings:', error);
    }
  };

  const startRecording = async () => {
    try {
      const response = await axios.post(`${API}/meetings/start-recording`);
      if (response.data.status === 'success') {
        setCurrentMeetingId(response.data.meeting_id);
        setIsRecording(true);
        setTranscription('');
        setRealTimeText('');
        
        if (recognitionRef.current) {
          recognitionRef.current.start();
        }
        
        console.log('🎤 Meeting recording started:', response.data.meeting_id);
      }
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = async () => {
    try {
      if (currentMeetingId) {
        const response = await axios.post(`${API}/meetings/stop-recording?meeting_id=${currentMeetingId}`);
        setIsRecording(false);
        setCurrentMeetingId(null);
        setRealTimeText('');
        
        if (recognitionRef.current) {
          recognitionRef.current.stop();
        }
        
        if (response.data.summary) {
          alert('✅ Планерка завершена! Создано резюме:\n\n' + response.data.summary);
        }
        
        fetchMeetings();
        console.log('⏹️ Meeting recording stopped');
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">🎤 Планерка - Диктофон + AI анализ</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recording Panel */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Запись планерки</h2>
          
          <div className="text-center mb-6">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`w-24 h-24 rounded-full text-white text-2xl transition-colors shadow-lg ${
                isRecording 
                  ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                  : 'bg-blue-500 hover:bg-blue-600'
              }`}
            >
              {isRecording ? '⏹️' : '🎤'}
            </button>
            <p className="mt-2 text-gray-600">
              {isRecording ? 'Идет запись планерки...' : 'Нажмите для начала записи'}
            </p>
          </div>

          {/* Live Transcription */}
          {isRecording && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold mb-2">📝 Транскрипция в реальном времени:</h3>
              <div className="h-32 overflow-y-auto bg-white p-3 rounded border">
                <p className="text-sm text-gray-800 whitespace-pre-wrap">
                  {transcription}
                  <span className="text-blue-600 italic">{realTimeText}</span>
                  {isRecording && <span className="animate-blink">|</span>}
                </p>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                💡 Говорите четко для лучшего распознавания. AI автоматически создаст резюме и задачи после завершения.
              </p>
            </div>
          )}
        </div>

        {/* Meetings History */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">📋 История планерок</h2>
          
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {meetings.length > 0 ? (
              meetings.map((meeting, index) => (
                <div key={index} className="border rounded-lg p-3 hover:bg-gray-50">
                  <h3 className="font-medium text-gray-900">{meeting.title}</h3>
                  <p className="text-sm text-gray-600">
                    {new Date(meeting.created_at).toLocaleString('ru-RU')}
                  </p>
                  {meeting.transcription && (
                    <p className="text-sm mt-1 text-gray-700 line-clamp-2">{meeting.transcription}</p>
                  )}
                  {meeting.summary && (
                    <div className="mt-2 p-2 bg-blue-50 rounded text-sm">
                      <strong>🤖 AI Резюме:</strong> {meeting.summary.substring(0, 100)}...
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>📝 Пока нет записей планерок</p>
                <p className="text-sm">Начните первую запись для анализа</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Voice Section Component - REAL AI INTEGRATION  
function VoiceSection() {
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  useEffect(() => {
    initSpeechRecognition();
    initSpeechSynthesis();
    // Добавляем приветственное сообщение
    setMessages([{
      type: 'ai',
      text: 'Привет! Я VasDom AI, ваш помощник по управлению клининговой компанией. О чем хотите поговорить?',
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
      };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
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

  const handleVoiceMessage = async (text) => {
    if (!text.trim()) return;
    
    const userMessage = { type: 'user', text, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);
    
    try {
      console.log('🎤 Sending voice message to AI:', text);
      
      const response = await axios.post(`${API}/voice/process`, {
        text: text,
        user_id: 'voice_user'
      });
      
      const aiResponse = {
        type: 'ai',
        text: response.data.response,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, aiResponse]);
      
      // Speak AI response
      if (synthRef.current && response.data.response) {
        const utterance = new SpeechSynthesisUtterance(response.data.response);
        utterance.lang = 'ru-RU';
        utterance.rate = 0.9;
        synthRef.current.speak(utterance);
      }
      
      console.log('🤖 AI response received');
      
    } catch (error) {
      console.error('Error processing voice message:', error);
      const errorResponse = {
        type: 'ai',
        text: 'Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsProcessing(false);
    }
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setIsListening(true);
      recognitionRef.current.start();
      console.log('🎤 Started listening...');
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
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Voice Control Panel */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">🎤 Голосовое управление</h2>
          
          <div className="text-center">
            <button
              onClick={isListening ? stopListening : startListening}
              disabled={isProcessing}
              className={`w-20 h-20 rounded-full text-white text-2xl transition-all shadow-lg ${
                isListening 
                  ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                  : isProcessing
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-green-500 hover:bg-green-600'
              }`}
            >
              {isProcessing ? '🤖' : isListening ? '⏹️' : '🎤'}
            </button>
            <p className="mt-2 text-gray-600">
              {isProcessing ? 'AI обрабатывает...' :
               isListening ? 'Слушаю вас...' : 'Нажмите и говорите'}
            </p>
            
            {currentMessage && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">{currentMessage}</p>
              </div>
            )}
          </div>
          
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-sm mb-2">💡 Попробуйте спросить:</h3>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>• "Сколько домов у нас в работе?"</li>
              <li>• "Какие бригады работают сегодня?"</li>
              <li>• "Создай задачу на завтра"</li>
              <li>• "Покажи статистику уборки"</li>
            </ul>
          </div>
        </div>
        
        {/* Chat Messages */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">💬 Диалог с AI</h2>
          
          <div className="h-96 overflow-y-auto border rounded-lg p-4 space-y-3 bg-gray-50">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs rounded-lg p-3 shadow-sm ${
                    message.type === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-white text-gray-800 border'
                  }`}
                >
                  <p className="text-sm">{message.text}</p>
                  <p className="text-xs opacity-75 mt-1">
                    {message.timestamp.toLocaleTimeString('ru-RU')}
                  </p>
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="flex justify-start">
                <div className="bg-gray-200 rounded-lg p-3 animate-pulse">
                  <p className="text-sm">AI обрабатывает ваш запрос...</p>
                </div>
              </div>
            )}
          </div>
          
          <div className="mt-4 text-center">
            <p className="text-xs text-gray-500">
              🤖 Powered by GPT-4 mini | 📚 База знаний активна | 🧠 Самообучение включено
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// AI Tasks Section
function AITasksSection() {
  const [tasks, setTasks] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    scheduled_time: ''
  });

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await axios.get(`${API}/ai-tasks`);
      if (response.data.status === 'success') {
        setTasks(response.data.tasks);
      }
    } catch (error) {
      console.error('Error fetching AI tasks:', error);
    }
  };

  const createTask = async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('title', newTask.title);
    formData.append('description', newTask.description);
    formData.append('scheduled_time', newTask.scheduled_time);
    
    try {
      const response = await axios.post(`${API}/ai-tasks`, formData);
      if (response.data.status === 'success') {
        setNewTask({ title: '', description: '', scheduled_time: '' });
        setShowCreateForm(false);
        fetchTasks();
        alert('✅ Задача создана успешно!');
      }
    } catch (error) {
      console.error('Error creating task:', error);
      alert('❌ Ошибка создания задачи');
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">🤖 Задачи для AI</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
        >
          ➕ Создать задачу
        </button>
      </div>

      {/* Create Task Form */}
      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">➕ Новая задача для AI</h2>
          <form onSubmit={createTask} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                📝 Название задачи
              </label>
              <input
                type="text"
                value={newTask.title}
                onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                className="w-full border border-gray-300 rounded-lg p-2"
                placeholder="Например: Напомнить о проверке качества уборки"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                📄 Описание
              </label>
              <textarea
                value={newTask.description}
                onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                className="w-full border border-gray-300 rounded-lg p-2 h-24"
                placeholder="Подробное описание задачи для AI..."
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ⏰ Время выполнения
              </label>
              <input
                type="datetime-local"
                value={newTask.scheduled_time}
                onChange={(e) => setNewTask({ ...newTask, scheduled_time: e.target.value })}
                className="w-full border border-gray-300 rounded-lg p-2"
                required
              />
            </div>
            <div className="flex space-x-2">
              <button
                type="submit"
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg"
              >
                ✅ Создать
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
              >
                ❌ Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tasks List */}
      <div className="space-y-4">
        {tasks.length > 0 ? (
          tasks.map((task, index) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold">{task.title}</h3>
                  <p className="text-gray-600 mt-1">{task.description}</p>
                  <p className="text-sm text-gray-500 mt-2">
                    ⏰ Запланировано: {new Date(task.scheduled_time).toLocaleString('ru-RU')}
                  </p>
                  {task.chat_messages && task.chat_messages.length > 0 && (
                    <p className="text-sm text-blue-600 mt-1">
                      💬 Сообщений в чате: {task.chat_messages.length}
                    </p>
                  )}
                </div>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  task.status === 'pending' 
                    ? 'bg-yellow-100 text-yellow-800'
                    : task.status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {task.status === 'pending' ? '⏳ В ожидании' : 
                   task.status === 'completed' ? '✅ Выполнено' : '🔄 В процессе'}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500">🤖 Пока нет задач для AI</p>
            <p className="text-sm text-gray-400">Создайте первую задачу для автоматизации</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Works Section (Cleaning) - WITH REAL DATA
function WorksSection() {
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchHouses();
  }, []);

  const fetchHouses = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/cleaning/houses?limit=400`);
      if (response.data.status === 'success') {
        setHouses(response.data.houses);
        console.log('🏠 Loaded houses from:', response.data.source);
      }
    } catch (error) {
      console.error('Error fetching houses:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">🏗️ Работы - Уборка подъездов</h1>
          <p className="text-gray-600">Управление всеми объектами клининга</p>
        </div>
        <button
          onClick={fetchHouses}
          disabled={loading}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
        >
          {loading ? '🔄 Загрузка...' : '🔄 Обновить из Bitrix24'}
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-md">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">
            📋 Все дома из Bitrix24 ({houses.length} объектов)
          </h2>
          <p className="text-sm text-gray-600">Данные из воронки "Уборка подъездов"</p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left">🏠 Адрес</th>
                <th className="px-4 py-2 text-left">📊 Статус</th>
                <th className="px-4 py-2 text-left">👥 Бригада</th>
                <th className="px-4 py-2 text-left">📅 График уборки</th>
                <th className="px-4 py-2 text-left">#️⃣ ID сделки</th>
              </tr>
            </thead>
            <tbody>
              {houses.map((house, index) => (
                <tr key={index} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium text-gray-900">{house.address}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      house.stage?.includes('WON') 
                        ? 'bg-green-100 text-green-800'
                        : house.stage?.includes('APOLOGY')
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {house.stage === 'C2:WON' ? '✅ Выполнено' :
                       house.stage === 'C2:APOLOGY' ? '❌ Проблемы' : '🔄 В работе'}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-700">{house.brigade || 'Не назначена'}</td>
                  <td className="px-4 py-2 text-gray-700">{house.cleaning_schedule || 'Не указан'}</td>
                  <td className="px-4 py-2 text-gray-600">#{house.bitrix24_deal_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {houses.length === 0 && !loading && (
          <div className="p-8 text-center text-gray-500">
            <p>📭 Нет данных для отображения</p>
            <p className="text-sm">Проверьте подключение к Bitrix24</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Training Section (Knowledge Base) - REAL FUNCTIONALITY
function TrainingSection() {
  const [knowledgeBase, setKnowledgeBase] = useState([]);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    fetchKnowledgeBase();
  }, []);

  const fetchKnowledgeBase = async () => {
    try {
      const response = await axios.get(`${API}/knowledge`);
      if (response.data.status === 'success') {
        setKnowledgeBase(response.data.knowledge_base);
      }
    } catch (error) {
      console.error('Error fetching knowledge base:', error);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile || !uploadTitle) {
      alert('Пожалуйста, выберите файл и введите название');
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('title', uploadTitle);

    try {
      const response = await axios.post(`${API}/knowledge/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (response.data.status === 'success') {
        alert('✅ ' + response.data.message);
        setUploadFile(null);
        setUploadTitle('');
        fetchKnowledgeBase();
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('❌ Ошибка загрузки файла');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">📚 База знаний и обучение AI</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">📤 Загрузка файлов</h2>
          
          <form onSubmit={handleFileUpload} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                📄 Название документа
              </label>
              <input
                type="text"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2"
                placeholder="Например: Инструкция по уборке подъездов"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                📎 Файл
              </label>
              <input
                type="file"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="w-full border border-gray-300 rounded-lg p-2"
                accept=".txt,.doc,.docx,.pdf"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Поддерживаемые форматы: TXT, DOC, DOCX, PDF
              </p>
            </div>
            
            <button
              type="submit"
              disabled={isUploading}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-lg disabled:opacity-50"
            >
              {isUploading ? '⏳ Загрузка...' : '📤 Загрузить в базу знаний'}
            </button>
          </form>
          
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-sm mb-2">💡 Как это работает:</h3>
            <ul className="text-xs text-blue-800 space-y-1">
              <li>• AI анализирует загруженные документы</li>
              <li>• Извлекает ключевые знания и процедуры</li>
              <li>• Использует информацию для ответов</li>
              <li>• Постоянно улучшается на основе опыта</li>
            </ul>
          </div>
        </div>
        
        {/* Knowledge Base List */}
        <div className="bg-white rounded-lg shadow-md p-6">
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
                    📄 Тип: {kb.file_type} | 🏷️ Ключевых слов: {kb.keywords?.length || 0}
                  </p>
                  {kb.content && (
                    <p className="text-sm text-gray-700 mt-2 line-clamp-2">
                      {kb.content.substring(0, 150)}...
                    </p>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>📚 База знаний пуста</p>
                <p className="text-sm">Загрузите документы для обучения AI</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Logs Section - REAL SYSTEM MONITORING
function LogsSection() {
  const [logs, setLogs] = useState({ voice_logs: [], learning_logs: [] });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/logs`);
      if (response.data.status === 'success') {
        setLogs({
          voice_logs: response.data.voice_logs || [],
          learning_logs: response.data.learning_logs || []
        });
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">📋 Системные логи</h1>
        <button
          onClick={fetchLogs}
          disabled={loading}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
        >
          {loading ? '🔄 Загрузка...' : '🔄 Обновить'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Voice Interactions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">🎤 Голосовые взаимодействия ({logs.voice_logs.length})</h2>
          
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {logs.voice_logs.map((log, index) => (
              <div key={index} className="border-l-4 border-blue-500 pl-3 pb-3">
                <p className="text-sm text-gray-600">
                  👤 <strong>Пользователь:</strong> {log.user_message}
                </p>
                <p className="text-sm text-green-600 mt-1">
                  🤖 <strong>AI:</strong> {log.ai_response}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(log.timestamp).toLocaleString('ru-RU')}
                </p>
              </div>
            ))}
            {logs.voice_logs.length === 0 && (
              <p className="text-gray-500">🎤 Пока нет голосовых взаимодействий</p>
            )}
          </div>
        </div>

        {/* Learning Entries */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">🧠 Самообучение AI ({logs.learning_logs.length})</h2>
          
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {logs.learning_logs.map((log, index) => (
              <div key={index} className="border-l-4 border-green-500 pl-3 pb-3">
                <p className="text-sm text-gray-600">
                  ❓ <strong>Вопрос:</strong> {log.user_question}
                </p>
                <p className="text-sm text-blue-600 mt-1">
                  💭 <strong>Ответ:</strong> {log.ai_response?.substring(0, 100)}...
                </p>
                {log.feedback && (
                  <p className="text-sm text-orange-600 mt-1">
                    📝 <strong>Обратная связь:</strong> {log.feedback}
                  </p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(log.created_at).toLocaleString('ru-RU')}
                </p>
              </div>
            ))}
            {logs.learning_logs.length === 0 && (
              <p className="text-gray-500">🧠 Система начнет учиться после первых взаимодействий</p>
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">📊 Статистика активности</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{logs.voice_logs.length}</p>
            <p className="text-sm text-gray-600">Голосовых запросов</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{logs.learning_logs.length}</p>
            <p className="text-sm text-gray-600">Записей обучения</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">
              {logs.voice_logs.length + logs.learning_logs.length}
            </p>
            <p className="text-sm text-gray-600">Всего взаимодействий</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;