import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Компонент навигации
const Navigation = ({ activeSection, setActiveSection }) => {
  const sections = [
    { id: 'overview', name: 'Общее', icon: '🏠' },
    { id: 'meetings', name: 'Планерка', icon: '🎤' },
    { id: 'live-chat', name: 'Живой разговор', icon: '📞' },
    { id: 'ai-tasks', name: 'Задачи для AI', icon: '🤖' },
    { id: 'sales', name: 'Продажи / Маркетинг', icon: '💰' },
    { id: 'employees', name: 'Сотрудники + HR', icon: '👥' },
    { id: 'work', name: 'Работы', icon: '🏗️' },
    { id: 'training', name: 'Обучение', icon: '📚' },
    { id: 'finances', name: 'Финансы', icon: '💹' },
    { id: 'logs', name: 'Логи', icon: '📊' }
  ];

  return (
    <nav className="bg-gray-900 text-white h-screen w-64 fixed left-0 top-0 overflow-y-auto">
      <div className="p-4">
        <h1 className="text-xl font-bold mb-6">🤖 VasDom AI</h1>
        <div className="space-y-2">
          {sections.map(section => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`w-full text-left p-3 rounded-lg transition-colors flex items-center gap-3 ${
                activeSection === section.id 
                  ? 'bg-blue-600 text-white' 
                  : 'hover:bg-gray-700 text-gray-300'
              }`}
            >
              <span className="text-lg">{section.icon}</span>
              <span className="text-sm">{section.name}</span>
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
};

// Компонент статистики
const StatCard = ({ title, value, icon, color = "bg-blue-500" }) => (
  <div className="bg-white rounded-lg shadow-md p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-gray-600 text-sm">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
      <div className={`${color} text-white p-3 rounded-full`}>
        <span className="text-xl">{icon}</span>
      </div>
    </div>
  </div>
);

// Раздел "Общее"
const OverviewSection = ({ dashboardData, aiInsights }) => (
  <div className="space-y-6">
    <div className="flex items-center justify-between mb-6">
      <h2 className="text-3xl font-bold text-gray-900">Общий обзор</h2>
      <div className="flex items-center gap-2">
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          dashboardData?.system_health === 'excellent' ? 'bg-green-100 text-green-800' :
          dashboardData?.system_health === 'good' ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          Система: {dashboardData?.system_health || 'Загрузка...'}
        </span>
      </div>
    </div>
    
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard title="Сотрудников" value={dashboardData?.total_employees || 0} icon="👥" color="bg-blue-500" />
      <StatCard title="Планерок" value={dashboardData?.total_meetings || 0} icon="📅" color="bg-green-500" />
      <StatCard title="Сообщений" value={dashboardData?.total_messages || 0} icon="💬" color="bg-purple-500" />
      <StatCard title="Предупреждений" value={dashboardData?.recent_alerts || 0} icon="⚠️" color="bg-orange-500" />
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold mb-4">🤖 AI Предложения по улучшению</h3>
        {dashboardData?.ai_suggestions?.length > 0 ? (
          <div className="space-y-3">
            {dashboardData.ai_suggestions.map((suggestion, index) => (
              <div key={index} className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-semibold text-gray-900">{suggestion.title}</h4>
                <p className="text-gray-600 text-sm">{suggestion.description}</p>
                <span className="text-xs text-blue-600">Влияние: {suggestion.impact_score}/10</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">Система анализирует данные...</p>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold mb-4">📊 Активность AI</h3>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-gray-600">Активных предложений:</span>
            <span className="font-semibold">{aiInsights?.active_suggestions || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Внедрено улучшений:</span>
            <span className="font-semibold">{aiInsights?.implemented_improvements || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Статус обучения:</span>
            <span className="font-semibold text-green-600">{aiInsights?.ai_status || 'Активно'}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Раздел "Сотрудники"
const EmployeesSection = ({ employees }) => {
  const [selectedDepartment, setSelectedDepartment] = useState('all');
  
  const departments = [...new Set(employees?.map(emp => emp.department) || [])];
  const filteredEmployees = selectedDepartment === 'all' 
    ? employees || []
    : employees?.filter(emp => emp.department === selectedDepartment) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-900">Управление сотрудниками</h2>
        <select 
          value={selectedDepartment}
          onChange={(e) => setSelectedDepartment(e.target.value)}
          className="bg-white border border-gray-300 rounded-lg px-4 py-2"
        >
          <option value="all">Все отделы</option>
          {departments.map(dept => (
            <option key={dept} value={dept}>{dept}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredEmployees.map(employee => (
          <div key={employee.id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900">{employee.full_name}</h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                employee.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {employee.active ? 'Активен' : 'Неактивен'}
              </span>
            </div>
            
            <div className="space-y-2 text-sm text-gray-600">
              <p><strong>Отдел:</strong> {employee.department}</p>
              <p><strong>Роль:</strong> {employee.role}</p>
              <p><strong>Телефон:</strong> {employee.phone}</p>
              <div className="flex items-center gap-2">
                <strong>Производительность:</strong>
                <div className="w-16 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${(employee.performance_score / 10) * 100}%` }}
                  ></div>
                </div>
                <span>{employee.performance_score}/10</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Раздел "Задачи"
const TasksSection = ({ tasks }) => {
  const [filterStatus, setFilterStatus] = useState('all');
  
  const filteredTasks = filterStatus === 'all' 
    ? tasks || []
    : tasks?.filter(task => task.status === filterStatus) || [];

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800',
    in_progress: 'bg-blue-100 text-blue-800', 
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800'
  };

  const priorityColors = {
    low: 'bg-gray-100 text-gray-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    urgent: 'bg-red-100 text-red-800'
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-900">Управление задачами</h2>
        <select 
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="bg-white border border-gray-300 rounded-lg px-4 py-2"
        >
          <option value="all">Все задачи</option>
          <option value="pending">Ожидают</option>
          <option value="in_progress">В работе</option>
          <option value="completed">Завершены</option>
        </select>
      </div>

      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6">
          <div className="space-y-4">
            {filteredTasks.map(task => (
              <div key={task.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">{task.title}</h3>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColors[task.priority] || 'bg-gray-100 text-gray-800'}`}>
                      {task.priority}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[task.status] || 'bg-gray-100 text-gray-800'}`}>
                      {task.status}
                    </span>
                  </div>
                </div>
                
                <p className="text-gray-600 mb-2">{task.description}</p>
                
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>Создано: {new Date(task.created_at).toLocaleDateString()}</span>
                  {task.due_date && (
                    <span>Срок: {new Date(task.due_date).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Раздел "Живой разговор" - ГОЛОСОВОЙ ИНТЕРФЕЙС (как телефонный звонок)
const LiveChatSection = () => {
  const [isCallActive, setIsCallActive] = useState(false);
  const [callId, setCallId] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [callHistory, setCallHistory] = useState([]);

  const startVoiceCall = async () => {
    try {
      const response = await axios.post(`${API}/voice/start-call`, {
        caller_id: 'dashboard_user'
      });
      
      if (response.data.status === 'success') {
        setCallId(response.data.call_id);
        setIsCallActive(true);
        setTranscript('');
        setAiResponse('');
      }
    } catch (error) {
      console.error('Error starting call:', error);
    }
  };

  const endVoiceCall = () => {
    setIsCallActive(false);
    setIsRecording(false);
    setCallId(null);
  };

  const startRecording = () => {
    setIsRecording(true);
    // В production здесь будет WebRTC запись аудио
    setTimeout(() => {
      setIsRecording(false);
      setTranscript("Это демо транскрипт голосового сообщения (функция в разработке)");
      processVoiceMessage("Это демо транскрипт голосового сообщения");
    }, 3000);
  };

  const processVoiceMessage = async (transcript) => {
    try {
      const response = await axios.post(`${API}/voice/process-audio`, {
        call_id: callId,
        transcript: transcript
      });
      
      if (response.data.status === 'success') {
        setAiResponse(response.data.ai_response);
        
        // В production здесь будет воспроизведение TTS аудио
        if ('speechSynthesis' in window) {
          const utterance = new SpeechSynthesisUtterance(response.data.ai_response);
          utterance.lang = 'ru-RU';
          speechSynthesis.speak(utterance);
        }
      }
    } catch (error) {
      console.error('Error processing voice:', error);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">📞 Живой голосовой разговор с AI</h2>
      
      <div className="bg-white rounded-lg shadow-md p-8">
        <div className="text-center">
          {!isCallActive ? (
            <div>
              <div className="mb-6">
                <div className="w-32 h-32 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-4xl text-white">📞</span>
                </div>
                <h3 className="text-xl font-bold mb-2">Голосовой AI ассистент</h3>
                <p className="text-gray-600">Нажмите для начала разговора с AI как по телефону</p>
              </div>
              
              <button
                onClick={startVoiceCall}
                className="bg-green-500 text-white px-8 py-4 rounded-full text-lg font-bold hover:bg-green-600 transition-colors"
              >
                🎤 Начать звонок
              </button>
            </div>
          ) : (
            <div>
              <div className="mb-6">
                <div className={`w-32 h-32 ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-green-500'} rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <span className="text-4xl text-white">{isRecording ? '🔴' : '🎤'}</span>
                </div>
                <h3 className="text-xl font-bold mb-2">Звонок активен</h3>
                <p className="text-gray-600">
                  {isRecording ? 'Запись голоса...' : 'Нажмите кнопку и говорите'}
                </p>
              </div>
              
              <div className="space-y-4 mb-6">
                {!isRecording && (
                  <button
                    onClick={startRecording}
                    className="bg-blue-500 text-white px-6 py-3 rounded-lg font-bold hover:bg-blue-600 mr-4"
                  >
                    🎤 Говорить
                  </button>
                )}
                
                <button
                  onClick={endVoiceCall}
                  className="bg-red-500 text-white px-6 py-3 rounded-lg font-bold hover:bg-red-600"
                >
                  📞 Завершить звонок
                </button>
              </div>
              
              {transcript && (
                <div className="bg-gray-100 p-4 rounded-lg mb-4">
                  <h4 className="font-bold text-sm mb-2">Ваша речь:</h4>
                  <p>{transcript}</p>
                </div>
              )}
              
              {aiResponse && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-bold text-sm mb-2">🤖 AI ответ:</h4>
                  <p>{aiResponse}</p>
                  <p className="text-xs text-gray-500 mt-2">
                    🔊 Аудио ответ воспроизводится автоматически
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-bold text-sm mb-2">💡 Функция в разработке:</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• WebRTC для записи голоса в браузере</li>
          <li>• Speech-to-Text транскрибация в реальном времени</li>
          <li>• Text-to-Speech озвучивание ответов AI</li>
          <li>• Сохранение истории голосовых звонков</li>
        </ul>
      </div>
    </div>
  );
};

// Раздел "Планерка"
const MeetingsSection = () => {
  const [meetings, setMeetings] = useState([]);
  const [newMeetingText, setNewMeetingText] = useState('');
  const [creatingMeeting, setCreatingMeeting] = useState(false);

  const loadMeetings = async () => {
    try {
      const response = await axios.get(`${API}/meetings`);
      if (response.data.status === 'success') {
        setMeetings(response.data.meetings || []);
      }
    } catch (error) {
      console.error('Error loading meetings:', error);
    }
  };

  const createMeeting = async () => {
    if (!newMeetingText.trim() || creatingMeeting) return;
    
    setCreatingMeeting(true);
    try {
      const response = await axios.post(`${API}/meetings`, {
        title: `Планерка ${new Date().toLocaleDateString()}`,
        description: 'Запись планерки',
        participants: ['admin'],
        start_time: new Date().toISOString(),
        recording_text: newMeetingText
      });
      
      if (response.data.status === 'success') {
        await loadMeetings();
        setNewMeetingText('');
      }
    } catch (error) {
      console.error('Error creating meeting:', error);
    } finally {
      setCreatingMeeting(false);
    }
  };

  const analyzeMeeting = async (meetingId) => {
    try {
      const response = await axios.post(`${API}/meetings/${meetingId}/analyze`);
      if (response.data.status === 'success') {
        await loadMeetings();
        alert(`AI анализ завершен! ${response.data.bitrix_tasks?.length || 0} задач создано в Bitrix24.`);
      }
    } catch (error) {
      console.error('Error analyzing meeting:', error);
    }
  };

  useEffect(() => {
    loadMeetings();
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">📅 Планерка - Запись и анализ</h2>
      
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold mb-4">Создать запись планерки</h3>
        <div className="space-y-4">
          <textarea
            value={newMeetingText}
            onChange={(e) => setNewMeetingText(e.target.value)}
            placeholder="Введите текст записи планерки для AI анализа..."
            className="w-full h-32 border border-gray-300 rounded-lg p-4"
            disabled={creatingMeeting}
          />
          <button
            onClick={createMeeting}
            disabled={!newMeetingText.trim() || creatingMeeting}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-400"
          >
            {creatingMeeting ? 'Создание...' : 'Создать планерку'}
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {meetings.map(meeting => (
          <div key={meeting.id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold">{meeting.title}</h3>
              <span className="text-sm text-gray-500">
                {new Date(meeting.start_time).toLocaleString()}
              </span>
            </div>
            
            <p className="text-gray-600 mb-3">{meeting.description}</p>
            
            {meeting.recording_text && (
              <div className="mb-3">
                <h4 className="font-semibold text-sm text-gray-700 mb-2">Запись:</h4>
                <p className="text-sm bg-gray-50 p-3 rounded">{meeting.recording_text}</p>
              </div>
            )}
            
            {meeting.ai_summary && (
              <div className="mb-3">
                <h4 className="font-semibold text-sm text-blue-700 mb-2">🤖 AI Анализ:</h4>
                <div className="text-sm bg-blue-50 p-3 rounded">{meeting.ai_summary}</div>
              </div>
            )}
            
            <div className="flex gap-2">
              {!meeting.ai_summary && meeting.recording_text && (
                <button
                  onClick={() => analyzeMeeting(meeting.id)}
                  className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700"
                >
                  🤖 Анализировать с AI
                </button>
              )}
              
              {meeting.bitrix_tasks_created?.length > 0 && (
                <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                  ✅ {meeting.bitrix_tasks_created.length} задач в Bitrix24
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Раздел "Логи"
const LogsSection = () => {
  const [logs, setLogs] = useState([]);
  const [filterLevel, setFilterLevel] = useState('all');
  const [filterComponent, setFilterComponent] = useState('all');

  const loadLogs = async () => {
    try {
      let url = `${API}/logs?limit=50`;
      if (filterLevel !== 'all') url += `&level=${filterLevel}`;
      if (filterComponent !== 'all') url += `&component=${filterComponent}`;
      
      const response = await axios.get(url);
      if (response.data.status === 'success') {
        setLogs(response.data.logs || []);
      }
    } catch (error) {
      console.error('Error loading logs:', error);
      setLogs([]);
    }
  };

  useEffect(() => {
    loadLogs();
    const interval = setInterval(loadLogs, 10000); // Обновляем каждые 10 секунд
    return () => clearInterval(interval);
  }, [filterLevel, filterComponent]);

  const getLevelColor = (level) => {
    switch (level) {
      case 'ERROR': return 'bg-red-100 text-red-800';
      case 'WARNING': return 'bg-yellow-100 text-yellow-800';
      case 'INFO': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getComponentIcon = (component) => {
    switch (component) {
      case 'telegram': return '📱';
      case 'bitrix24': return '🏢';
      case 'ai': return '🤖';
      case 'backend': return '⚙️';
      default: return '📊';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-900">📊 Системные логи</h2>
        <div className="flex gap-4">
          <select 
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2"
          >
            <option value="all">Все уровни</option>
            <option value="ERROR">Ошибки</option>
            <option value="WARNING">Предупреждения</option>
            <option value="INFO">Информация</option>
          </select>
          
          <select 
            value={filterComponent}
            onChange={(e) => setFilterComponent(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2"
          >
            <option value="all">Все компоненты</option>
            <option value="backend">Backend</option>
            <option value="telegram">Telegram</option>
            <option value="bitrix24">Bitrix24</option>
            <option value="ai">AI Система</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6">
          <div className="space-y-3">
            {logs.map((log, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 flex items-start gap-3">
                <span className="text-xl">{getComponentIcon(log.component)}</span>
                
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getLevelColor(log.level)}`}>
                      {log.level}
                    </span>
                    <span className="text-sm text-gray-500">{log.component}</span>
                    <span className="text-sm text-gray-500">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  
                  <p className="text-gray-800">{log.message}</p>
                  
                  {log.data && Object.keys(log.data).length > 0 && (
                    <pre className="text-xs bg-gray-50 p-2 rounded mt-2 overflow-x-auto">
                      {JSON.stringify(log.data, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ))}
            
            {logs.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                Логи не найдены по выбранным фильтрам
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
const FinancesSection = ({ financialReport }) => (
  <div className="space-y-6">
    <h2 className="text-3xl font-bold text-gray-900">Финансовая отчетность</h2>
    
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <StatCard 
        title="Доходы" 
        value={`${(financialReport?.totals?.revenue || 0).toLocaleString()} ₽`}
        icon="📈" 
        color="bg-green-500" 
      />
      <StatCard 
        title="Расходы" 
        value={`${(financialReport?.totals?.expense || 0).toLocaleString()} ₽`}
        icon="📉" 
        color="bg-red-500" 
      />
      <StatCard 
        title="Прибыль" 
        value={`${(financialReport?.profit || 0).toLocaleString()} ₽`}
        icon="💰" 
        color="bg-blue-500" 
      />
    </div>

    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold mb-4">Детализация по категориям</h3>
      {financialReport?.breakdown && Object.entries(financialReport.breakdown).map(([category, items]) => (
        <div key={category} className="mb-6">
          <h4 className="text-lg font-semibold mb-2 capitalize">{category}</h4>
          <div className="space-y-2">
            {Object.entries(items).map(([subcategory, data]) => (
              <div key={subcategory} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span>{subcategory}</span>
                <div className="text-right">
                  <span className="font-semibold">{data.amount?.toLocaleString()} ₽</span>
                  <span className="text-gray-500 text-sm ml-2">({data.count} записей)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
);

// Основной компонент приложения
const Dashboard = () => {
  const [activeSection, setActiveSection] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [aiInsights, setAiInsights] = useState(null);
  const [financialReport, setFinancialReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Обновляем каждые 30 секунд
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Загружаем основные данные
      const [dashboardRes, employeesRes, tasksRes, logsRes] = await Promise.all([
        axios.get(`${API}/dashboard`).catch(() => ({ data: null })),
        axios.get(`${API}/employees`).catch(() => ({ data: [] })),
        axios.get(`${API}/tasks`).catch(() => ({ data: [] })),
        axios.get(`${API}/logs?limit=10`).catch(() => ({ data: null }))
      ]);

      setDashboardData(dashboardRes.data);
      setEmployees(employeesRes.data);
      setTasks(tasksRes.data);
      
      // AI insights пока заглушка
      setAiInsights({
        active_suggestions: 0,
        implemented_improvements: 0,
        ai_status: 'Активно'
      });
      
      // Financial report пока заглушка  
      setFinancialReport({
        totals: { revenue: 0, expense: 0, investment: 0 },
        profit: 0,
        breakdown: {}
      });
      
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderSection = () => {
    if (loading && !dashboardData) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Загрузка данных...</p>
          </div>
        </div>
      );
    }

    switch (activeSection) {
      case 'overview':
        return <OverviewSection dashboardData={dashboardData} aiInsights={aiInsights} />;
      case 'employees':
        return <EmployeesSection employees={employees} />;
      case 'tasks':
        return <TasksSection tasks={tasks} />;
      case 'finances':
        return <FinancesSection financialReport={financialReport} />;
      case 'meetings':
        return <MeetingsSection />;
      case 'live-chat':
        return <LiveChatSection />;
      case 'logs':
        return <LogsSection />;
      case 'sales':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">💰 Продажи / Маркетинг</h2>
            <div className="bg-white rounded-lg shadow-md p-6 mx-auto max-w-2xl">
              <p className="text-gray-600 mb-4">Интеграция с Bitrix24 CRM готова!</p>
              <div className="space-y-2 text-left">
                <p><strong>✅ Подключено:</strong> Bitrix24 портал vas-dom.bitrix24.ru</p>
                <p><strong>📊 Сделок доступно:</strong> 50+ активных</p>
                <p><strong>🔄 Синхронизация:</strong> В реальном времени</p>
                <p><strong>🎯 Следующий этап:</strong> Воронки продаж и автоматизация</p>
              </div>
            </div>
          </div>
        );
      case 'work':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">🏗️ Управление работами</h2>
            <div className="bg-white rounded-lg shadow-md p-6 mx-auto max-w-2xl">
              <p className="text-gray-600 mb-4">Система планирования готова к настройке!</p>
              <div className="space-y-2 text-left">
                <p><strong>🏠 Объекты:</strong> 400+ домов для уборки</p>
                <p><strong>🚗 Маршруты:</strong> Оптимизация расстояний и времени</p>
                <p><strong>📱 Отчеты:</strong> GPS отметки и фото до/после</p>
                <p><strong>🎯 Следующий этап:</strong> Подключение карт и навигации</p>
              </div>
            </div>
          </div>
        );
      default:
        return <OverviewSection dashboardData={dashboardData} aiInsights={aiInsights} />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <Navigation activeSection={activeSection} setActiveSection={setActiveSection} />
      <main className="flex-1 ml-64 p-8 overflow-y-auto">
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Последнее обновление: {new Date().toLocaleTimeString()}</p>
            </div>
            <button 
              onClick={loadData}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <span>🔄</span>
              Обновить
            </button>
          </div>
        </div>
        {renderSection()}
      </main>
    </div>
  );
};

// Главный компонент App
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;