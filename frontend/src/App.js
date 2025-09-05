import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import VoiceAssistant from './VoiceAssistant';
import LiveVoiceChat from './LiveVoiceChat';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Navigation Component
const Navigation = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'dashboard', name: '📊 Дашборд', icon: '📊' },
    { id: 'employees', name: '👥 Сотрудники', icon: '👥' },
    { id: 'analytics', name: '📈 Аналитика', icon: '📈' },
    { id: 'ai-chat', name: '🤖 AI Чат', icon: '🤖' },
    { id: 'live-voice', name: '📞 Live Голос', icon: '📞' }
  ];

  return (
    <nav className="bg-white shadow-lg mb-8">
      <div className="container mx-auto px-4">
        <div className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-6 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Metrics Cards */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Всего сотрудников"
            value={dashboardData.metrics.total_employees}
            icon="👥"
            color="bg-blue-500"
            change="+5 за месяц"
          />
          <MetricCard
            title="Активные сотрудники"
            value={dashboardData.metrics.active_employees}
            icon="✅"
            color="bg-green-500"
            change="98% активность"
          />
          <MetricCard
            title="Дома в Калуге"
            value={dashboardData.metrics.kaluga_houses}
            icon="🏠"
            color="bg-purple-500"
            change="500 домов"
          />
          <MetricCard
            title="Дома в Кемерово"
            value={dashboardData.metrics.kemerovo_houses}
            icon="🏘️"
            color="bg-orange-500"
            change="100 домов"
          />
        </div>
      )}

      {/* Recent Activities and AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            📊 Последние активности
          </h3>
          <div className="space-y-3">
            {dashboardData?.recent_activities.map((activity, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                <div>
                  <p className="text-sm text-gray-900">{activity.message}</p>
                  <p className="text-xs text-gray-500">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            🧠 AI Рекомендации
          </h3>
          <div className="space-y-3">
            {dashboardData?.ai_insights.map((insight, index) => (
              <div key={index} className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-900">{insight}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Employees Component
const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`);
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    } finally {
      setLoading(false);
    }
  };

  const positionNames = {
    'general_director': 'Генеральный директор',
    'director': 'Директор',
    'accountant': 'Бухгалтер',
    'hr_manager': 'HR менеджер',
    'cleaning_manager': 'Менеджер по клинингу',
    'construction_manager': 'Менеджер по стройке',
    'architect': 'Архитектор-сметчик',
    'cleaner': 'Уборщица',
    'other': 'Другое'
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Управление сотрудниками</h2>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
        >
          + Добавить сотрудника
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {employees.length === 0 ? (
            <div className="col-span-full text-center py-8">
              <p className="text-gray-500">Сотрудники не найдены. Добавьте первого сотрудника!</p>
            </div>
          ) : (
            employees.map((employee) => (
              <div key={employee.id} className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                    {employee.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{employee.name}</h3>
                    <p className="text-sm text-gray-600">{positionNames[employee.position] || employee.position}</p>
                  </div>
                </div>
                <div className="space-y-2 text-sm">
                  <p><span className="font-medium">Город:</span> {employee.city}</p>
                  <p><span className="font-medium">Email:</span> {employee.email || 'Не указан'}</p>
                  <p><span className="font-medium">Телефон:</span> {employee.phone || 'Не указан'}</p>
                  <p><span className="font-medium">Дата найма:</span> {new Date(employee.hire_date).toLocaleDateString('ru-RU')}</p>
                </div>
                <div className="mt-4 flex space-x-2">
                  <button className="flex-1 bg-gray-100 text-gray-700 py-2 px-3 rounded text-sm hover:bg-gray-200">
                    Редактировать
                  </button>
                  <button className="bg-red-100 text-red-700 py-2 px-3 rounded text-sm hover:bg-red-200">
                    Удалить
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

// Analytics Component
const Analytics = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Аналитика и отчеты</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">📊 Производительность по городам</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Калуга</span>
              <div className="flex items-center space-x-2">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{width: '85%'}}></div>
                </div>
                <span className="text-sm">85%</span>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span>Кемерово</span>
              <div className="flex items-center space-x-2">
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{width: '92%'}}></div>
                </div>
                <span className="text-sm">92%</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">📈 Финансовые показатели</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Выручка за месяц:</span>
              <span className="font-semibold">2,340,000 ₽</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Расходы:</span>
              <span className="font-semibold">1,850,000 ₽</span>
            </div>
            <div className="flex justify-between border-t pt-2">
              <span className="text-gray-600">Прибыль:</span>
              <span className="font-semibold text-green-600">490,000 ₽</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">🏆 Топ сотрудники месяца</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Сотрудник</th>
                <th className="text-left py-2">Должность</th>
                <th className="text-left py-2">Город</th>
                <th className="text-left py-2">Рейтинг</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b">
                <td className="py-2">Иванов И.И.</td>
                <td className="py-2">Менеджер по клинингу</td>
                <td className="py-2">Калуга</td>
                <td className="py-2">⭐⭐⭐⭐⭐</td>
              </tr>
              <tr className="border-b">
                <td className="py-2">Петрова А.С.</td>
                <td className="py-2">Уборщица</td>
                <td className="py-2">Кемерово</td>
                <td className="py-2">⭐⭐⭐⭐⭐</td>
              </tr>
              <tr>
                <td className="py-2">Сидоров В.В.</td>
                <td className="py-2">Менеджер по стройке</td>
                <td className="py-2">Калуга</td>
                <td className="py-2">⭐⭐⭐⭐</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ title, value, icon, color, change }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {change && <p className="text-xs text-gray-500 mt-1">{change}</p>}
        </div>
        <div className={`w-12 h-12 ${color} rounded-lg flex items-center justify-center text-white text-2xl`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

// AI Chat Component with Voice Integration
const AIChat = () => {
  const [messages, setMessages] = useState([
    {
      type: 'ai',
      content: 'Привет! Я ваш AI-ассистент для управления компанией. Можете писать или говорить со мной голосом! Скажите "Привет, МАКС!" для голосовой команды.',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (messageText = null) => {
    const textToSend = messageText || inputMessage;
    if (!textToSend.trim()) return;

    const userMessage = {
      type: 'user',
      content: textToSend,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/ai/chat`, {
        message: textToSend
      });

      const aiMessage = {
        type: 'ai',
        content: response.data.response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // Text-to-speech for AI responses
      if (textToSend.toLowerCase().includes('макс') || textToSend.toLowerCase().includes('голос')) {
        speakResponse(response.data.response);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        type: 'ai',
        content: 'Извините, произошла ошибка. Попробуйте еще раз.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const speakResponse = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ru-RU';
      utterance.rate = 0.9;
      
      const voices = speechSynthesis.getVoices();
      const russianVoice = voices.find(voice => voice.lang.includes('ru'));
      if (russianVoice) {
        utterance.voice = russianVoice;
      }
      
      speechSynthesis.speak(utterance);
    }
  };

  const handleVoiceMessage = (transcript) => {
    console.log('Voice message received:', transcript);
    sendMessage(transcript);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-4">
        <h3 className="text-lg font-semibold text-white flex items-center">
          🤖 AI Чат-ассистент с голосовым управлением
        </h3>
      </div>
      
      {/* Voice Assistant Component */}
      <div className="p-4 border-b">
        <VoiceAssistant onVoiceMessage={handleVoiceMessage} isListening={isLoading} />
      </div>
      
      <div className="h-96 overflow-y-auto p-6 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.type === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm">{message.content}</p>
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
      
      <div className="border-t p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Напишите сообщение или используйте голос..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={isLoading || !inputMessage.trim()}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Отправить
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2 text-center">
          💡 Попробуйте: "Привет, МАКС! Покажи статистику по Bitrix24"
        </p>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'employees':
        return <Employees />;
      case 'analytics':
        return <Analytics />;
      case 'ai-chat':
        return <AIChat />;
      case 'live-voice':
        return <LiveVoiceChat />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🤖 AI Ассистент для управления компанией
          </h1>
          <p className="text-gray-600">
            Комплексное управление клининговой компанией с помощью искусственного интеллекта
          </p>
        </div>

        <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />
        
        {renderContent()}
      </div>
    </div>
  );
}

export default App;