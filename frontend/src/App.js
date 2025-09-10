import React, { useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { 
  MessageCircle, Phone, Calendar, Mic, MicOff, 
  Play, Pause, Square, Bot, Volume2, Send, 
  CheckSquare, Users, Clock, ExternalLink, Loader2 
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Простой AI Chat компонент
const SimpleAIChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = { id: Date.now(), text: inputMessage, sender: 'user', timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/voice/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: inputMessage, session_id: `chat_${Date.now()}` }),
      });

      const data = await response.json();
      const aiMessage = {
        id: Date.now() + 1,
        text: data.response || 'Извините, произошла ошибка.',
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Ошибка соединения. Попробуйте снова.',
        sender: 'ai',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <Bot className="chat-icon" />
        <div>
          <h3>AI Помощник VasDom</h3>
          <p>Самообучающийся AI для клининговой компании</p>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <Bot size={48} />
            <p>Задайте любой вопрос о клининговых услугах</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.sender}`}>
            <div className="message-avatar">
              {message.sender === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <p>{message.text}</p>
              <small>{message.timestamp.toLocaleTimeString()}</small>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message ai">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <Loader2 className="animate-spin" size={20} />
              <span>AI думает...</span>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input">
        <input
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Напишите ваше сообщение..."
          disabled={isLoading}
        />
        <button onClick={sendMessage} disabled={!inputMessage.trim() || isLoading}>
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

// Живой голосовой чат
const LiveVoiceChat = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);

  const startVoiceChat = async () => {
    setIsConnecting(true);
    setTranscription('Подключение к GPT-4o Realtime API...');
    
    try {
      // Запрос разрешения на микрофон
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Симуляция подключения (в реальности здесь будет WebSocket)
      setTimeout(() => {
        setIsConnected(true);
        setIsConnecting(false);
        setTranscription('🎉 Живой голос активен! Говорите что-нибудь...');
        
        // Симуляция аудио уровня
        const interval = setInterval(() => {
          setAudioLevel(Math.random() * 100);
        }, 100);
        
        return () => clearInterval(interval);
      }, 2000);
      
    } catch (error) {
      setIsConnecting(false);
      setTranscription(`Ошибка: ${error.message}`);
    }
  };

  const stopVoiceChat = () => {
    setIsConnected(false);
    setTranscription('');
    setAudioLevel(0);
  };

  return (
    <div className="voice-chat-container">
      <div className="voice-header">
        <Phone className="voice-icon" />
        <div>
          <h3>Живой голосовой чат</h3>
          <p>GPT-4o Realtime API • Человеческий голос</p>
        </div>
      </div>

      {!isConnected && !isConnecting && (
        <div className="voice-start">
          <button className="voice-start-btn" onClick={startVoiceChat}>
            <Phone size={32} />
            <span>Начать живой разговор</span>
          </button>
          <p>Нажмите для подключения к GPT-4o Realtime API</p>
        </div>
      )}

      {isConnecting && (
        <div className="voice-connecting">
          <Loader2 className="animate-spin" size={32} />
          <p>Подключение к живому голосу...</p>
          <small>{transcription}</small>
        </div>
      )}

      {isConnected && (
        <div className="voice-active">
          <div className="voice-status">
            <div className="status-indicator active">🎙️ ЖИВОЙ ГОЛОС АКТИВЕН</div>
          </div>
          
          <div className="audio-level">
            <span>🔊 Уровень микрофона: {Math.round(audioLevel)}%</span>
            <div className="level-bar">
              <div 
                className="level-fill" 
                style={{ width: `${Math.max(5, audioLevel)}%` }}
              />
            </div>
          </div>

          <div className="voice-transcription">
            <p>{transcription}</p>
          </div>

          <button className="voice-stop-btn" onClick={stopVoiceChat}>
            <Phone size={24} />
            <span>Завершить разговор</span>
          </button>
        </div>
      )}
    </div>
  );
};

// Планерки
const MeetingsPage = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcription, setTranscription] = useState('');
  const [meetingTitle, setMeetingTitle] = useState('');
  const [extractedTasks, setExtractedTasks] = useState([]);

  const startRecording = () => {
    setIsRecording(true);
    setRecordingTime(0);
    
    // Симуляция записи
    const interval = setInterval(() => {
      setRecordingTime(prev => prev + 1);
    }, 1000);

    // Симуляция транскрипции
    setTimeout(() => {
      setTranscription('Планерка VasDom. Иван, проверь уборку на Ленина 15. Мария, подготовь отчет до пятницы.');
    }, 3000);

    return () => clearInterval(interval);
  };

  const stopRecording = () => {
    setIsRecording(false);
    
    // Анализ планерки
    setTimeout(() => {
      setExtractedTasks([
        { title: 'Проверить уборку на Ленина 15', assigned_to: 'Иван', priority: 'high' },
        { title: 'Подготовить отчет', assigned_to: 'Мария', priority: 'normal' }
      ]);
    }, 1000);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="meetings-container">
      <div className="meetings-header">
        <Calendar className="meetings-icon" />
        <div>
          <h3>Умные планерки</h3>
          <p>Транскрибация и интеграция с Битрикс24</p>
        </div>
      </div>

      <div className="meeting-setup">
        <input
          type="text"
          value={meetingTitle}
          onChange={(e) => setMeetingTitle(e.target.value)}
          placeholder="Название планерки"
          className="meeting-title-input"
        />
      </div>

      <div className="recording-controls">
        {!isRecording ? (
          <button className="record-btn start" onClick={startRecording}>
            <Mic size={24} />
            <span>Начать запись</span>
          </button>
        ) : (
          <div className="recording-active">
            <div className="recording-status">
              <div className="recording-dot"></div>
              <span>ЗАПИСЬ: {formatTime(recordingTime)}</span>
            </div>
            <button className="record-btn stop" onClick={stopRecording}>
              <Square size={24} />
              <span>Остановить</span>
            </button>
          </div>
        )}
      </div>

      {transcription && (
        <div className="transcription-section">
          <h4>📝 Транскрипция</h4>
          <div className="transcription-text">{transcription}</div>
        </div>
      )}

      {extractedTasks.length > 0 && (
        <div className="tasks-section">
          <h4>✅ Извлечённые задачи ({extractedTasks.length})</h4>
          <div className="tasks-list">
            {extractedTasks.map((task, index) => (
              <div key={index} className="task-item">
                <div className="task-content">
                  <h5>{task.title}</h5>
                  <div className="task-meta">
                    <span>👤 {task.assigned_to}</span>
                    <span className={`priority ${task.priority}`}>
                      {task.priority === 'high' ? 'Высокий' : 'Обычный'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <button className="bitrix-btn">
            <ExternalLink size={16} />
            <span>Создать в Битрикс24</span>
          </button>
        </div>
      )}
    </div>
  );
};

// Главный компонент приложения
const Home = () => {
  const [activeTab, setActiveTab] = useState('chat');

  const tabs = [
    { id: 'chat', label: 'AI Чат', icon: MessageCircle, component: SimpleAIChat },
    { id: 'voice', label: 'Живой голос', icon: Phone, component: LiveVoiceChat },
    { id: 'meetings', label: 'Планерки', icon: Calendar, component: MeetingsPage }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || SimpleAIChat;

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <MessageCircle size={32} />
            <div>
              <h1>VasDom AudioBot</h1>
              <p>Революционная AI платформа для клининговой компании</p>
            </div>
          </div>
          
          <div className="stats-row">
            <div className="stat-item">
              <span className="stat-value">1,247</span>
              <span className="stat-label">Диалогов</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">4.8</span>
              <span className="stat-label">Рейтинг</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">89</span>
              <span className="stat-label">Планерок</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">156</span>
              <span className="stat-label">Задач в Битрикс</span>
            </div>
          </div>
        </div>
      </header>

      <nav className="app-nav">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            >
              <Icon size={20} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      <main className="app-main">
        <ActiveComponent />
      </main>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/*" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
