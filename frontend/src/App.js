import React, { useEffect, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Separator } from "./components/ui/separator";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Dashboard Components
const SystemStatus = ({ dashboardData }) => {
  const system = dashboardData?.system || {};
  const services = dashboardData?.services || {};
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'healthy': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'not_configured': return 'bg-gray-400';
      default: return 'bg-red-500';
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Система</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {system.status === 'running' ? 'Работает' : 'Остановлена'}
          </div>
          <p className="text-xs text-muted-foreground">
            Время работы: {system.uptime || '0s'}
          </p>
        </CardContent>
      </Card>

      {Object.entries(services).map(([key, service]) => (
        <Card key={key}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${getStatusColor(service.status)}`}></div>
              {service.name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={service.status === 'active' ? 'default' : 'secondary'}>
              {service.configured ? 'Настроен' : 'Не настроен'}
            </Badge>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

const MetricsCards = ({ dashboardData }) => {
  const metrics = dashboardData?.metrics || {};
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Всего запросов</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.total_requests || 0}</div>
          <p className="text-xs text-muted-foreground">
            {metrics.requests_per_hour || 0} в час
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Ошибки</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-600">{metrics.total_errors || 0}</div>
          <p className="text-xs text-muted-foreground">
            {metrics.error_rate || 0}% от общего числа
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Окружение</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold capitalize">
            {dashboardData?.system?.environment || 'unknown'}
          </div>
          <p className="text-xs text-muted-foreground">
            Текущая среда
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

const RecentActivity = ({ dashboardData }) => {
  const activities = dashboardData?.recent_activity || [];
  
  const getLevelColor = (level) => {
    switch (level) {
      case 'error': return 'text-red-600';
      case 'warning': return 'text-yellow-600';
      case 'info': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Последняя активность</CardTitle>
        <CardDescription>
          Недавние события в системе
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {activities.length > 0 ? (
            activities.map((activity, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className={`w-2 h-2 rounded-full ${
                  activity.level === 'error' ? 'bg-red-500' :
                  activity.level === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                }`}></div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">{activity.message}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(activity.timestamp).toLocaleString('ru-RU')}
                  </p>
                </div>
                <Badge variant="outline" className={getLevelColor(activity.level)}>
                  {activity.type}
                </Badge>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-500">Нет данных об активности</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const SystemLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/logs?lines=50`);
      setLogs(response.data.logs || []);
    } catch (error) {
      console.error('Error fetching logs:', error);
      setLogs(['Ошибка загрузки логов']);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Системные логи
          <Button onClick={fetchLogs} disabled={loading} size="sm">
            {loading ? 'Загрузка...' : 'Обновить'}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
          {logs.length > 0 ? (
            logs.map((log, index) => (
              <div key={index} className="mb-1">
                {log}
              </div>
            ))
          ) : (
            <div>Нет доступных логов</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const ServiceDetails = ({ dashboardData }) => {
  const services = dashboardData?.services || {};
  const environment = dashboardData?.environment || {};
  
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Детали сервисов</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {Object.entries(services).map(([key, service]) => (
            <div key={key} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold">{service.name}</h3>
                <Badge variant={service.status === 'active' ? 'default' : 'secondary'}>
                  {service.status}
                </Badge>
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <div>Настроен: {service.configured ? 'Да' : 'Нет'}</div>
                {service.webhook_url && <div>Webhook: {service.webhook_url}</div>}
                {service.portal && <div>Портал: {service.portal}</div>}
                {service.model && <div>Модель: {service.model}</div>}
                {service.url && <div>URL: {service.url}</div>}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Информация о среде</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>Python версия: {environment.python_version}</div>
            <div>Платформа: {environment.platform}</div>
            <div>Окружение: {environment.environment}</div>
            <div>Режим отладки: {environment.debug_mode ? 'Включен' : 'Выключен'}</div>
            <div>Уровень логирования: {environment.log_level}</div>
            <div>Порт: {environment.port}</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${BACKEND_URL}/api/dashboard`);
      setDashboardData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading && !dashboardData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Загрузка dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Alert className="max-w-md">
          <AlertDescription>
            <strong>Ошибка:</strong> {error}
            <Button onClick={fetchDashboard} className="mt-2 w-full">
              Попробовать снова
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🏠 VasDom AI Assistant Dashboard
          </h1>
          <p className="text-gray-600">
            Мониторинг системы • Обновлено: {
              dashboardData?.system?.current_time ? 
              new Date(dashboardData.system.current_time).toLocaleString('ru-RU') : 
              'неизвестно'
            }
          </p>
          <Button onClick={fetchDashboard} size="sm" className="mt-2">
            🔄 Обновить данные
          </Button>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">Обзор</TabsTrigger>
            <TabsTrigger value="services">Сервисы</TabsTrigger>
            <TabsTrigger value="logs">Логи</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <SystemStatus dashboardData={dashboardData} />
            <MetricsCards dashboardData={dashboardData} />
            <RecentActivity dashboardData={dashboardData} />
          </TabsContent>

          <TabsContent value="services" className="space-y-6">
            <ServiceDetails dashboardData={dashboardData} />
          </TabsContent>

          <TabsContent value="logs" className="space-y-6">
            <SystemLogs />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

// Simple Home component for API testing
const Home = () => {
  const [apiStatus, setApiStatus] = useState(null);

  useEffect(() => {
    const testApi = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/health`);
        setApiStatus('✅ API подключено успешно');
        console.log('API Response:', response.data);
      } catch (e) {
        setApiStatus('❌ Ошибка подключения к API');
        console.error('API Error:', e);
      }
    };
    testApi();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center max-w-md">
        <div className="mb-6">
          <img 
            src="https://avatars.githubusercontent.com/in/1201222?s=120&u=2686cf91179bbafbc7a71bfbc43004cf9ae1acea&v=4" 
            alt="VasDom Logo"
            className="mx-auto mb-4 rounded-full"
          />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            🏠 VasDom AI Assistant
          </h1>
          <p className="text-gray-600 mb-4">
            AI-помощник с интеграцией Telegram и Bitrix24
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg shadow mb-4">
          <p className="text-sm text-gray-600 mb-2">Статус API:</p>
          <p className={`font-mono text-sm ${
            apiStatus?.includes('✅') ? 'text-green-600' : 'text-red-600'
          }`}>
            {apiStatus || 'Проверка...'}
          </p>
        </div>

        <div className="space-y-2">
          <a 
            href="/dashboard" 
            className="block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
          >
            📊 Открыть Dashboard
          </a>
          <a 
            href="https://t.me/aitest123432_bot" 
            target="_blank"
            rel="noopener noreferrer"
            className="block bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
          >
            🤖 Telegram Bot
          </a>
        </div>

        <p className="text-xs text-gray-500 mt-4">
          Система готова к работе! 🚀
        </p>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;