import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Main Dashboard Component
function App() {
  const [currentSection, setCurrentSection] = useState('general');
  const [isMenuCollapsed, setIsMenuCollapsed] = useState(false);
  const [dashboardStats, setDashboardStats] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/dashboard`);
      if (response.data.status === 'success') {
        setDashboardStats(response.data.stats);
      }
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      // Mock data if API fails
      setDashboardStats({
        employees: 82,
        houses: 50,
        entrances: 0,
        apartments: 0,
        floors: 0,
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
      <div className="flex-1 overflow-hidden">
        {renderContent()}
      </div>
    </div>
  );
}

// General Dashboard Component
function GeneralDashboard({ stats, onRefresh, loading }) {
  const statCards = [
    { title: 'Сотрудников', value: stats.employees || 0, icon: '👥', color: 'blue' },
    { title: 'Домов в CRM', value: stats.houses || 0, icon: '🏠', color: 'green' },
    { title: 'Подъездов', value: stats.entrances || 0, icon: '🚪', color: 'purple' },
    { title: 'Квартир', value: stats.apartments || 0, icon: '🔍', color: 'orange' },
    { title: 'Этажей', value: stats.floors || 0, icon: '📊', color: 'red' },
    { title: 'Планерок', value: stats.meetings || 0, icon: '🎤', color: 'indigo' }
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
              <div className={`bg-${card.color}-100 rounded-full p-3 mr-4`}>
                <span className="text-2xl">{card.icon}</span>
              </div>
              <div>
                <p className="text-sm text-gray-600">{card.title}</p>
                <p className="text-2xl font-bold text-gray-900">{card.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Meetings Section Component
function MeetingsSection() {
  const [isRecording, setIsRecording] = useState(false);
  const [meetings, setMeetings] = useState([]);
  const [currentMeetingId, setCurrentMeetingId] = useState(null);
  const [transcription, setTranscription] = useState('');
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
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        setTranscription(prev => prev + finalTranscript + interimTranscript);
      };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
      };
      
      recognitionRef.current = recognition;
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
        
        if (recognitionRef.current) {
          recognitionRef.current.start();
        }
      }
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = async () => {
    try {
      if (currentMeetingId) {
        await axios.post(`${API}/meetings/stop-recording?meeting_id=${currentMeetingId}`);
        setIsRecording(false);
        setCurrentMeetingId(null);
        
        if (recognitionRef.current) {
          recognitionRef.current.stop();
        }
        
        fetchMeetings();
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">🎤 Планерка - Диктофон + AI</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recording Panel */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Запись планерки</h2>
          
          <div className="text-center mb-6">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`w-24 h-24 rounded-full text-white text-2xl transition-colors ${
                isRecording 
                  ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                  : 'bg-blue-500 hover:bg-blue-600'
              }`}
            >
              {isRecording ? '⏹️' : '🎤'}
            </button>
            <p className="mt-2 text-gray-600">
              {isRecording ? 'Идет запись...' : 'Нажмите для начала записи'}
            </p>
          </div>

          {/* Live Transcription */}
          {isRecording && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold mb-2">Транскрипция в реальном времени:</h3>
              <div className="h-32 overflow-y-auto">
                <p className="text-sm">{transcription || 'Говорите...'}</p>
              </div>
            </div>
          )}
        </div>

        {/* Meetings History */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">История планерок</h2>
          
          <div className="space-y-3">
            {meetings.length > 0 ? (
              meetings.map((meeting, index) => (
                <div key={index} className="border rounded-lg p-3">
                  <h3 className="font-medium">{meeting.title}</h3>
                  <p className="text-sm text-gray-600">
                    {new Date(meeting.created_at).toLocaleString('ru-RU')}
                  </p>
                  <p className="text-sm mt-1">{meeting.transcription}</p>
                </div>
              ))
            ) : (
              <p className="text-gray-500">Пока нет записей планерок</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Voice Section Component
function VoiceSection() {
  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  useEffect(() => {
    initSpeechRecognition();
    initSpeechSynthesis();
  }, []);

  const initSpeechRecognition = () => {
    if ('webkitSpeechRecognition' in window) {
      const recognition = new window.webkitSpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'ru-RU';
      
      recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            transcript = event.results[i][0].transcript;
            handleVoiceMessage(transcript);
          } else {
            setCurrentMessage(event.results[i][0].transcript);
          }
        }
      };
      
      recognition.onend = () => {
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
    
    try {
      const response = await axios.post(`${API}/voice/process`, {
        text: text,
        user_id: 'user'
      });
      
      const aiResponse = {
        type: 'ai',
        text: response.data.response,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, aiResponse]);
      
      // Speak AI response
      if (synthRef.current) {
        const utterance = new SpeechSynthesisUtterance(response.data.response);
        utterance.lang = 'ru-RU';
        synthRef.current.speak(utterance);
      }
      
    } catch (error) {
      console.error('Error processing voice message:', error);
      const errorResponse = {
        type: 'ai',
        text: 'Извините, произошла ошибка при обработке вашего сообщения.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorResponse]);
    }
  };

  const startListening = () => {
    if (recognitionRef.current) {
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">📞 Живой разговор с AI</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Voice Control Panel */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Голосовое управление</h2>
          
          <div className="text-center">
            <button
              onClick={isListening ? stopListening : startListening}
              className={`w-20 h-20 rounded-full text-white text-2xl transition-colors ${
                isListening 
                  ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                  : 'bg-green-500 hover:bg-green-600'
              }`}
            >
              {isListening ? '⏹️' : '🎤'}
            </button>
            <p className="mt-2 text-gray-600">
              {isListening ? 'Слушаю...' : 'Нажмите и говорите'}
            </p>
            
            {currentMessage && (
              <div className="mt-4 p-3 bg-gray-100 rounded-lg">
                <p className="text-sm">{currentMessage}</p>
              </div>
            )}
          </div>
        </div>
        
        {/* Chat Messages */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Диалог с AI</h2>
          
          <div className="h-96 overflow-y-auto border rounded-lg p-4 space-y-3">
            {messages.length === 0 ? (
              <p className="text-gray-500 text-center">Начните разговор, нажав на микрофон</p>
            ) : (
              messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs rounded-lg p-3 ${
                      message.type === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-800'
                    }`}
                  >
                    <p className="text-sm">{message.text}</p>
                    <p className="text-xs opacity-75 mt-1">
                      {message.timestamp.toLocaleTimeString('ru-RU')}
                    </p>
                  </div>
                </div>
              ))
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
      }
    } catch (error) {
      console.error('Error creating task:', error);
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
          Создать задачу
        </button>
      </div>

      {/* Create Task Form */}
      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Новая задача для AI</h2>
          <form onSubmit={createTask} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Название задачи
              </label>
              <input
                type="text"
                value={newTask.title}
                onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                className="w-full border border-gray-300 rounded-lg p-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Описание
              </label>
              <textarea
                value={newTask.description}
                onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                className="w-full border border-gray-300 rounded-lg p-2 h-24"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Время выполнения
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
                Создать
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
              >
                Отмена
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
                    Запланировано: {new Date(task.scheduled_time).toLocaleString('ru-RU')}
                  </p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  task.status === 'pending' 
                    ? 'bg-yellow-100 text-yellow-800'
                    : task.status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {task.status === 'pending' ? 'В ожидании' : 
                   task.status === 'completed' ? 'Выполнено' : 'В процессе'}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500">Пока нет задач для AI</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Works Section (Cleaning)
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
        <h1 className="text-3xl font-bold">🏗️ Работы - Уборка подъездов</h1>
        <button
          onClick={fetchHouses}
          disabled={loading}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
        >
          {loading ? 'Загрузка...' : 'Обновить данные из CRM'}
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-md">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">
            Все дома из Bitrix24 ({houses.length} объектов)
          </h2>
          <p className="text-sm text-gray-600">Данные загружены из воронки "Уборка подъездов"</p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left">Адрес</th>
                <th className="px-4 py-2 text-left">Статус</th>
                <th className="px-4 py-2 text-left">ID сделки</th>
                <th className="px-4 py-2 text-left">Дата создания</th>
              </tr>
            </thead>
            <tbody>
              {houses.map((house, index) => (
                <tr key={index} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium">{house.address}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      house.stage?.includes('WON') 
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {house.stage}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-600">#{house.bitrix24_deal_id}</td>
                  <td className="px-4 py-2 text-gray-600 text-sm">
                    {house.created_date ? new Date(house.created_date).toLocaleDateString('ru-RU') : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;