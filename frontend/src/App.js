import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Компонент дашборда
const Dashboard = ({ stats, onNavigate }) => {
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>🏢 VasDom AudioBot</h1>
        <p className="subtitle">AI-система управления клининговой компанией в Калуге</p>
      </div>
      
      <div className="stats-grid">
        <div className="stat-card houses">
          <div className="stat-icon">🏠</div>
          <div className="stat-content">
            <h3>{stats.houses}</h3>
            <p>Многоквартирных домов</p>
          </div>
        </div>
        
        <div className="stat-card apartments">
          <div className="stat-icon">🏢</div>
          <div className="stat-content">
            <h3>{stats.apartments.toLocaleString()}</h3>
            <p>Квартир в обслуживании</p>
          </div>
        </div>
        
        <div className="stat-card employees">
          <div className="stat-icon">👥</div>
          <div className="stat-content">
            <h3>{stats.employees}</h3>
            <p>Сотрудников в штате</p>
          </div>
        </div>
        
        <div className="stat-card brigades">
          <div className="stat-icon">🛠️</div>
          <div className="stat-content">
            <h3>{stats.brigades}</h3>
            <p>Рабочих бригад</p>
          </div>
        </div>
        
        <div className="stat-card completed">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <h3>{stats.completed_objects}</h3>
            <p>Выполненных объектов</p>
          </div>
        </div>
        
        <div className="stat-card problems">
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <h3>{stats.problem_objects}</h3>
            <p>Проблемных объектов</p>
          </div>
        </div>
      </div>
      
      <div className="navigation-buttons">
        <button className="nav-btn voice-btn" onClick={() => onNavigate('voice')}>
          🎤 Голосовой чат
        </button>
        <button className="nav-btn meeting-btn" onClick={() => onNavigate('meeting')}>
          📝 Планерки
        </button>
        <button className="nav-btn houses-btn" onClick={() => onNavigate('houses')}>
          🏠 Управление домами
        </button>
        <button className="nav-btn ai-btn" onClick={() => onNavigate('ai')}>
          🤖 AI Задачи
        </button>
      </div>
    </div>
  );
};

// Компонент голосового чата
const VoiceChat = ({ onBack }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const startVoiceRecognition = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Ваш браузер не поддерживает распознавание речи');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.lang = 'ru-RU';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
      setTranscript('Слушаю...');
    };

    recognition.onresult = async (event) => {
      const text = event.results[0][0].transcript;
      setTranscript(text);
      setIsListening(false);
      
      // Отправить в AI
      await processVoiceRequest(text);
    };

    recognition.onerror = () => {
      setIsListening(false);
      setTranscript('Ошибка распознавания речи');
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const processVoiceRequest = async (text) => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/voice/process`, {
        text: text,
        user_id: 'user_1'
      });
      
      setAiResponse(response.data.response);
      
      // Озвучить ответ
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(response.data.response);
        utterance.lang = 'ru-RU';
        speechSynthesis.speak(utterance);
      }
    } catch (error) {
      console.error('Ошибка обработки голосового запроса:', error);
      setAiResponse('Ошибка связи с сервером');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="voice-chat">
      <div className="section-header">
        <button className="back-btn" onClick={onBack}>← Назад</button>
        <h2>🎤 Голосовой чат с AI</h2>
      </div>
      
      <div className="voice-interface">
        <div className="voice-status">
          {isListening && (
            <div className="listening-indicator">
              <div className="pulse"></div>
              <p>Слушаю...</p>
            </div>
          )}
        </div>
        
        <button 
          className={`voice-btn-large ${isListening ? 'listening' : ''}`}
          onClick={startVoiceRecognition}
          disabled={isListening || isLoading}
        >
          {isListening ? '🎙️ Слушаю...' : '🎤 Начать разговор'}
        </button>
        
        {transcript && (
          <div className="transcript">
            <h4>Ваш запрос:</h4>
            <p>"{transcript}"</p>
          </div>
        )}
        
        {aiResponse && (
          <div className="ai-response">
            <h4>Ответ AI:</h4>
            <p>{aiResponse}</p>
          </div>
        )}
        
        {isLoading && <div className="loading">Обрабатываю запрос...</div>}
      </div>
    </div>
  );
};

// Компонент управления домами
const HousesManagement = ({ onBack }) => {
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHouses();
  }, []);

  const fetchHouses = async () => {
    try {
      const response = await axios.get(`${API}/cleaning/houses?limit=10`);
      setHouses(response.data.houses);
    } catch (error) {
      console.error('Ошибка загрузки домов:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="houses-management">
      <div className="section-header">
        <button className="back-btn" onClick={onBack}>← Назад</button>
        <h2>🏠 Управление домами</h2>
      </div>
      
      {loading ? (
        <div className="loading">Загрузка домов...</div>
      ) : (
        <div className="houses-list">
          {houses.map((house) => (
            <div key={house.ID} className="house-card">
              <div className="house-info">
                <h4>{house.TITLE}</h4>
                <p>ID: {house.ID}</p>
                <p>Статус: {house.STAGE_ID}</p>
                <p>Сумма: {house.OPPORTUNITY} ₽</p>
              </div>
              <div className="house-status">
                {house.STAGE_ID === 'C2:WON' && <span className="status-won">✅ Выполнено</span>}
                {house.STAGE_ID === 'C2:APOLOGY' && <span className="status-problem">⚠️ Проблема</span>}
                {house.STAGE_ID === 'C2:FINAL_INVOICE' && <span className="status-invoice">📄 Счет</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Основной компонент приложения
function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [dashboardStats, setDashboardStats] = useState({
    houses: 0,
    apartments: 0,
    employees: 0,
    brigades: 0,
    completed_objects: 0,
    problem_objects: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      console.log('Fetching dashboard stats from:', `${API}/dashboard`);
      const response = await axios.get(`${API}/dashboard`);
      console.log('Dashboard response:', response.data);
      setDashboardStats(response.data);
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
      // Используем дефолтные значения при ошибке
      setDashboardStats({
        houses: 348,
        apartments: 25812,
        employees: 82,
        brigades: 6,
        completed_objects: 147,
        problem_objects: 25
      });
    } finally {
      setLoading(false);
    }
  };

  const handleNavigation = (view) => {
    setCurrentView(view);
  };

  const handleBack = () => {
    setCurrentView('dashboard');
  };

  if (loading) {
    return (
      <div className="App">
        <div className="loading-screen">
          <div className="loading-spinner"></div>
          <p>Загрузка VasDom AudioBot...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      {currentView === 'dashboard' && (
        <Dashboard stats={dashboardStats} onNavigate={handleNavigation} />
      )}
      
      {currentView === 'voice' && (
        <VoiceChat onBack={handleBack} />
      )}
      
      {currentView === 'houses' && (
        <HousesManagement onBack={handleBack} />
      )}
      
      {currentView === 'meeting' && (
        <div className="section">
          <div className="section-header">
            <button className="back-btn" onClick={handleBack}>← Назад</button>
            <h2>📝 Планерки</h2>
          </div>
          <p>Функция планерок в разработке...</p>
        </div>
      )}
      
      {currentView === 'ai' && (
        <div className="section">
          <div className="section-header">
            <button className="back-btn" onClick={handleBack}>← Назад</button>
            <h2>🤖 AI Задачи</h2>
          </div>
          <p>AI задачи в разработке...</p>
        </div>
      )}
    </div>
  );
}

export default App;