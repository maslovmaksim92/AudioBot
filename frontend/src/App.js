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
    { id: 'meetings', name: 'Планерка', icon: '📅' },
    { id: 'live-chat', name: 'Живой разговор', icon: '💬' },
    { id: 'tasks', name: 'Задачи', icon: '📋' },
    { id: 'sales', name: 'Продажи / Маркетинг', icon: '💰' },
    { id: 'employees', name: 'Сотрудники + HR', icon: '👥' },
    { id: 'work', name: 'Работы', icon: '🏗️' },
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
      <StatCard title="Активных проектов" value={dashboardData?.active_projects || 0} icon="🏢" color="bg-green-500" />
      <StatCard title="Выполнено задач" value={dashboardData?.completed_tasks_today || 0} icon="✅" color="bg-purple-500" />
      <StatCard title="Выручка месяца" value={`${(dashboardData?.revenue_month || 0).toLocaleString()} ₽`} icon="💰" color="bg-orange-500" />
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

// Раздел "Финансы"
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
      const [dashboardRes, employeesRes, tasksRes, aiRes, financesRes] = await Promise.all([
        axios.get(`${API}/dashboard`).catch(() => ({ data: null })),
        axios.get(`${API}/employees`).catch(() => ({ data: [] })),
        axios.get(`${API}/tasks`).catch(() => ({ data: [] })),
        axios.get(`${API}/ai/insights`).catch(() => ({ data: null })),
        axios.get(`${API}/finances/report`).catch(() => ({ data: null }))
      ]);

      setDashboardData(dashboardRes.data);
      setEmployees(employeesRes.data);
      setTasks(tasksRes.data);
      setAiInsights(aiRes.data);
      setFinancialReport(financesRes.data);
      
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
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">📅 Планерка</h2>
            <p className="text-gray-600">Функция записи и анализа планерок в разработке...</p>
          </div>
        );
      case 'live-chat':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">💬 Живой разговор</h2>
            <p className="text-gray-600">AI-ассистент для живого общения в разработке...</p>
          </div>
        );
      case 'sales':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">💰 Продажи / Маркетинг</h2>
            <p className="text-gray-600">Интеграция с CRM и аналитика продаж в разработке...</p>
          </div>
        );
      case 'work':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">🏗️ Управление работами</h2>
            <p className="text-gray-600">Система планирования маршрутов и управления проектами в разработке...</p>
          </div>
        );
      case 'logs':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">📊 Системные логи</h2>
            <p className="text-gray-600">Мониторинг активности и логирование в разработке...</p>
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