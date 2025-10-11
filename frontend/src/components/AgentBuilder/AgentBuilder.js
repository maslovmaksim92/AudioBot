import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Bot,
  Zap,
  Plus,
  Settings,
  Play,
  Save,
  Code,
  Database,
  MessageSquare,
  Phone,
  Mail,
  Calendar,
  FileText,
  TrendingUp,
  Users,
  CheckCircle,
  ArrowRight,
  Sparkles,
  Trash2,
  Edit,
  X
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const AgentBuilder = () => {
  const [agents, setAgents] = useState([]);
  const [stats, setStats] = useState({
    total_agents: 0,
    active_agents: 0,
    executions_today: 0,
    executions_success_rate: 0,
    total_users: 0
  });
  const [loading, setLoading] = useState(true);
  const [showBuilder, setShowBuilder] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  const [newAgent, setNewAgent] = useState({
    name: '',
    description: '',
    type: 'scheduler',
    triggers: [],
    actions: [],
    config: {},
    status: 'active'
  });

  const agentTypes = [
    { id: 'scheduler', name: 'Планировщик', icon: Calendar, desc: 'Задачи по расписанию' },
    { id: 'integration', name: 'Интеграция', icon: Database, desc: 'Подключение сервисов' },
    { id: 'bot', name: 'Бот', icon: Bot, desc: 'Telegram/WhatsApp бот' },
    { id: 'workflow', name: 'Workflow', icon: Zap, desc: 'Бизнес-процесс' },
    { id: 'ai_agent', name: 'AI Агент', icon: Sparkles, desc: 'Интеллектуальный агент' }
  ];

  const availableTriggers = [
    { id: 'cron', name: 'По расписанию', icon: Calendar },
    { id: 'webhook', name: 'Webhook', icon: Code },
    { id: 'telegram', name: 'Telegram', icon: MessageSquare },
    { id: 'bitrix', name: 'Bitrix24', icon: Database },
    { id: 'manual', name: 'Ручной запуск', icon: Play }
  ];

  const availableActions = [
    { id: 'telegram_send', name: 'Отправить в Telegram', icon: MessageSquare },
    { id: 'ai_call', name: 'AI звонок', icon: Phone },
    { id: 'email_send', name: 'Отправить Email', icon: Mail },
    { id: 'bitrix_create', name: 'Создать в Bitrix24', icon: Database },
    { id: 'log_create', name: 'Записать в Logs', icon: FileText },
    { id: 'task_create', name: 'Создать задачу', icon: CheckCircle }
  ];

  // Загрузка данных при монтировании компонента
  useEffect(() => {
    loadAgents();
    loadStats();
    loadEmployees();
  }, []);
  
  const loadEmployees = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/employees`);
      setEmployees(response.data);
    } catch (error) {
      console.error('Error loading employees:', error);
    }
  };

  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/agents/`);
      setAgents(response.data);
    } catch (error) {
      console.error('Error loading agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/agents/stats/summary`);
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleCreateAgent = async () => {
    if (!newAgent.name || !newAgent.description) {
      alert('Заполните название и описание агента');
      return;
    }

    try {
      // Формируем triggers и actions на основе типа и конфигурации
      const agentData = {
        ...newAgent,
        triggers: [],
        actions: []
      };

      // Для scheduler - добавляем cron trigger
      if (newAgent.type === 'scheduler' && newAgent.config?.schedule_time) {
        const time = newAgent.config.schedule_time; // "08:25"
        const [hour, minute] = time.split(':');
        
        // Формируем cron для разных дней недели
        let cronExpression = '';
        if (newAgent.config.schedule_days === 'weekdays') {
          cronExpression = `${minute} ${hour} * * 1-5`; // Пн-Пт
        } else if (newAgent.config.schedule_days === 'daily') {
          cronExpression = `${minute} ${hour} * * *`; // Каждый день
        } else if (newAgent.config.schedule_days === 'weekend') {
          cronExpression = `${minute} ${hour} * * 0,6`; // Сб-Вс
        }
        
        agentData.triggers.push({
          type: 'cron',
          name: `Расписание: ${time} (${newAgent.config.schedule_days === 'weekdays' ? 'Пн-Пт' : newAgent.config.schedule_days === 'daily' ? 'Ежедневно' : 'Сб-Вс'})`,
          config: { cron: cronExpression }
        });
      }

      // Для TG уведомлений - добавляем telegram_send action
      if (newAgent.config?.telegram_message) {
        // Собираем всех получателей
        let allRecipients = [];
        
        // Добавляем Chat ID групп
        if (newAgent.config.telegram_chat_ids) {
          const chatIds = newAgent.config.telegram_chat_ids.split(',').map(s => s.trim()).filter(Boolean);
          allRecipients.push(...chatIds);
        }
        
        // Добавляем телефоны выбранных сотрудников
        if (selectedEmployees.length > 0) {
          const selectedPhones = employees
            .filter(emp => selectedEmployees.includes(emp.id))
            .map(emp => emp.phone)
            .filter(Boolean);
          allRecipients.push(...selectedPhones);
        }
        
        // Добавляем вручную введённые номера
        if (newAgent.config.telegram_phone_numbers) {
          const phones = newAgent.config.telegram_phone_numbers.split(',').map(s => s.trim()).filter(Boolean);
          allRecipients.push(...phones);
        }
        
        if (allRecipients.length > 0) {
          agentData.actions.push({
            type: 'telegram_send',
            name: 'Отправка в Telegram',
            config: {
              recipients: allRecipients.join(', '),
              message: newAgent.config.telegram_message
            }
          });
        }
      }

      await axios.post(`${BACKEND_URL}/api/agents/`, agentData);
      setShowBuilder(false);
      setSelectedEmployees([]);
      setNewAgent({
        name: '',
        description: '',
        type: 'scheduler',
        triggers: [],
        actions: [],
        config: {},
        status: 'active'
      });
      loadAgents();
      loadStats();
    } catch (error) {
      console.error('Error creating agent:', error);
      alert('Ошибка при создании агента: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleUpdateAgent = async () => {
    if (!editingAgent) return;

    try {
      await axios.put(`${BACKEND_URL}/api/agents/${editingAgent.id}/`, newAgent);
      setShowBuilder(false);
      setEditingAgent(null);
      setNewAgent({
        name: '',
        description: '',
        type: 'scheduler',
        triggers: [],
        actions: [],
        config: {},
        status: 'active'
      });
      loadAgents();
    } catch (error) {
      console.error('Error updating agent:', error);
      alert('Ошибка при обновлении агента');
    }
  };

  const handleDeleteAgent = async (agentId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этого агента?')) {
      return;
    }

    try {
      await axios.delete(`${BACKEND_URL}/api/agents/${agentId}/`);
      loadAgents();
      loadStats();
    } catch (error) {
      console.error('Error deleting agent:', error);
      alert('Ошибка при удалении агента');
    }
  };

  const handleExecuteAgent = async (agentId) => {
    try {
      await axios.post(`${BACKEND_URL}/api/agents/${agentId}/execute/`);
      alert('Агент успешно выполнен');
      loadAgents();
      loadStats();
    } catch (error) {
      console.error('Error executing agent:', error);
      alert('Ошибка при выполнении агента');
    }
  };

  const startEditing = (agent) => {
    setEditingAgent(agent);
    setNewAgent({
      name: agent.name,
      description: agent.description,
      type: agent.type,
      triggers: agent.triggers || [],
      actions: agent.actions || [],
      config: agent.config || {},
      status: agent.status
    });
    setShowBuilder(true);
  };

  const getStatusColor = (status) => {
    return status === 'active' 
      ? 'bg-green-100 text-green-700' 
      : 'bg-gray-100 text-gray-700';
  };

  const getTypeIcon = (type) => {
    const typeInfo = agentTypes.find(t => t.id === type);
    return typeInfo ? typeInfo.icon : Bot;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка агентов...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
                <Bot className="w-10 h-10 text-indigo-600" />
                Конструктор Агентов
              </h1>
              <p className="text-gray-600">
                Создавайте AI агентов и автоматизации для вашего бизнеса
              </p>
            </div>
            
            <button
              onClick={() => {
                setEditingAgent(null);
                setNewAgent({
                  name: '',
                  description: '',
                  type: 'scheduler',
                  triggers: [],
                  actions: [],
                  status: 'active'
                });
                setShowBuilder(!showBuilder);
              }}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
            >
              <Plus className="w-5 h-5" />
              Создать агента
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <Bot className="w-8 h-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">{stats.active_agents}</span>
            </div>
            <p className="text-sm text-gray-600">Активных агентов</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <Zap className="w-8 h-8 text-yellow-600" />
              <span className="text-2xl font-bold text-gray-900">{stats.executions_today}</span>
            </div>
            <p className="text-sm text-gray-600">Выполнено сегодня</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="w-8 h-8 text-green-600" />
              <span className="text-2xl font-bold text-gray-900">{stats.executions_success_rate}%</span>
            </div>
            <p className="text-sm text-gray-600">Успешность</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <Users className="w-8 h-8 text-purple-600" />
              <span className="text-2xl font-bold text-gray-900">{stats.total_users}</span>
            </div>
            <p className="text-sm text-gray-600">Пользователей</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <Database className="w-8 h-8 text-cyan-600" />
              <span className="text-2xl font-bold text-gray-900">{stats.total_agents}</span>
            </div>
            <p className="text-sm text-gray-600">Всего агентов</p>
          </div>
        </div>

        {/* Agent Builder Modal */}
        {showBuilder && (
          <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-100 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {editingAgent ? 'Редактировать агента' : 'Новый агент'}
              </h2>
              <button
                onClick={() => {
                  setShowBuilder(false);
                  setEditingAgent(null);
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Agent Type Selection */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">Тип агента</label>
              <div className="grid grid-cols-5 gap-3">
                {agentTypes.map(type => (
                  <button
                    key={type.id}
                    onClick={() => setNewAgent({...newAgent, type: type.id})}
                    className={`p-4 rounded-xl border-2 transition-all text-center ${
                      newAgent.type === type.id
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <type.icon className={`w-8 h-8 mx-auto mb-2 ${
                      newAgent.type === type.id ? 'text-indigo-600' : 'text-gray-400'
                    }`} />
                    <div className="text-sm font-semibold text-gray-900">{type.name}</div>
                    <div className="text-xs text-gray-500 mt-1">{type.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Agent Name */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Название агента</label>
              <input
                type="text"
                value={newAgent.name}
                onChange={(e) => setNewAgent({...newAgent, name: e.target.value})}
                placeholder="Например: Автоматизация отчётов"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            {/* Description */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Описание</label>
              <textarea
                value={newAgent.description}
                onChange={(e) => setNewAgent({...newAgent, description: e.target.value})}
                placeholder="Что делает этот агент?"
                rows="3"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            {/* Расписание (для scheduler типа) */}
            {newAgent.type === 'scheduler' && (
              <div className="mb-6 p-4 bg-blue-50 rounded-xl border border-blue-200">
                <label className="block text-sm font-semibold text-gray-700 mb-3">Расписание запуска</label>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">Время</label>
                    <input
                      type="time"
                      value={newAgent.config?.schedule_time || '08:25'}
                      onChange={(e) => setNewAgent({...newAgent, config: {...(newAgent.config || {}), schedule_time: e.target.value}})}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">Дни недели</label>
                    <select
                      value={newAgent.config?.schedule_days || 'weekdays'}
                      onChange={(e) => setNewAgent({...newAgent, config: {...(newAgent.config || {}), schedule_days: e.target.value}})}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="weekdays">Пн-Пт</option>
                      <option value="daily">Каждый день</option>
                      <option value="weekend">Сб-Вс</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Настройка TG уведомлений */}
            {(newAgent.type === 'scheduler' || newAgent.type === 'bot') && (
              <div className="mb-6 p-4 bg-purple-50 rounded-xl border border-purple-200">
                <label className="block text-sm font-semibold text-gray-700 mb-3">Telegram уведомления</label>
                
                {/* Chat ID групп/чатов */}
                <div className="mb-3">
                  <label className="block text-xs text-gray-600 mb-1">Chat ID групп/чатов (через запятую)</label>
                  <input
                    type="text"
                    value={newAgent.config?.telegram_chat_ids || ''}
                    onChange={(e) => setNewAgent({...newAgent, config: {...(newAgent.config || {}), telegram_chat_ids: e.target.value}})}
                    placeholder="Например: @vasdom_chat, @company_team, -1001234567890"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Можно указать @username или числовой Chat ID группы</p>
                </div>

                {/* Выбор сотрудников */}
                <div className="mb-3">
                  <label className="block text-xs text-gray-600 mb-2">Выбрать сотрудников</label>
                  <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-lg p-2 bg-white">
                    {employees.length === 0 ? (
                      <p className="text-xs text-gray-400 p-2">Сотрудники не найдены</p>
                    ) : (
                      <div className="space-y-1">
                        {employees.slice(0, 10).map(emp => (
                          <label key={emp.id} className="flex items-center gap-2 p-1 hover:bg-gray-50 rounded cursor-pointer">
                            <input
                              type="checkbox"
                              checked={selectedEmployees.includes(emp.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedEmployees([...selectedEmployees, emp.id]);
                                } else {
                                  setSelectedEmployees(selectedEmployees.filter(id => id !== emp.id));
                                }
                              }}
                              className="rounded text-indigo-600"
                            />
                            <span className="text-xs text-gray-700">{emp.full_name || emp.email}</span>
                            {emp.phone && <span className="text-xs text-gray-400">({emp.phone})</span>}
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                  {selectedEmployees.length > 0 && (
                    <p className="text-xs text-indigo-600 mt-1">Выбрано: {selectedEmployees.length}</p>
                  )}
                </div>

                {/* Или ручной ввод номеров */}
                <div className="mb-3">
                  <label className="block text-xs text-gray-600 mb-1">Или введите номера вручную (через запятую)</label>
                  <input
                    type="text"
                    value={newAgent.config?.telegram_phone_numbers || ''}
                    onChange={(e) => setNewAgent({...newAgent, config: {...(newAgent.config || {}), telegram_phone_numbers: e.target.value}})}
                    placeholder="Например: +79991234567, +79991234568"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                {/* Текст сообщения */}
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Текст сообщения</label>
                  <textarea
                    value={newAgent.config?.telegram_message || ''}
                    onChange={(e) => setNewAgent({...newAgent, config: {...(newAgent.config || {}), telegram_message: e.target.value}})}
                    placeholder="Например: Доброе утро! Напоминаю о планёрке в 8:30"
                    rows="2"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => setShowBuilder(false)}
                className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
              >
                Отмена
              </button>
              <button
                onClick={editingAgent ? handleUpdateAgent : handleCreateAgent}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg"
              >
                {editingAgent ? 'Сохранить изменения' : 'Создать агента'}
              </button>
            </div>
          </div>
        )}

        {/* Agents List */}
        <div className="space-y-4">
          {agents.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 text-center">
              <Bot className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Нет агентов</h3>
              <p className="text-gray-600 mb-6">Создайте первого агента для автоматизации</p>
              <button
                onClick={() => setShowBuilder(true)}
                className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                Создать агента
              </button>
            </div>
          ) : (
            agents.map(agent => {
              const IconComponent = getTypeIcon(agent.type);
              const color = agent.type === 'scheduler' ? 'from-blue-500 to-cyan-500' :
                            agent.type === 'integration' ? 'from-green-500 to-emerald-500' :
                            agent.type === 'bot' ? 'from-purple-500 to-pink-500' :
                            agent.type === 'workflow' ? 'from-yellow-500 to-orange-500' :
                            'from-indigo-500 to-purple-500';

              return (
                <div key={agent.id} className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-shadow">
                  <div className="flex items-start gap-4">
                    <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center flex-shrink-0`}>
                      <IconComponent className="w-7 h-7 text-white" />
                    </div>

                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-xl font-bold text-gray-900 mb-1">{agent.name}</h3>
                          <p className="text-gray-600">{agent.description}</p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(agent.status)}`}>
                          {agent.status === 'active' ? 'Активен' : 'Неактивен'}
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-6 mb-4 text-sm text-gray-600">
                        <div>
                          <span className="font-semibold">Выполнений:</span> {agent.executions_total || 0}
                        </div>
                        <div>
                          <span className="font-semibold">Успешно:</span> {agent.executions_success || 0}
                        </div>
                        {agent.last_execution && (
                          <div>
                            <span className="font-semibold">Последнее:</span> {new Date(agent.last_execution).toLocaleString('ru-RU')}
                          </div>
                        )}
                      </div>

                      {/* Triggers and Actions */}
                      {(agent.triggers?.length > 0 || agent.actions?.length > 0) && (
                        <div className="mb-4 space-y-2">
                          {agent.triggers?.length > 0 && (
                            <div className="flex items-start gap-2 text-sm">
                              <Calendar className="w-4 h-4 text-blue-600 mt-0.5" />
                              <div>
                                <span className="font-semibold text-gray-700">Триггеры:</span>
                                <div className="text-gray-600 mt-1 space-y-1">
                                  {agent.triggers.map((trigger, idx) => (
                                    <div key={idx} className="flex items-center gap-2">
                                      <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{trigger.type}</span>
                                      <span>{trigger.name}</span>
                                      {trigger.config?.cron && (
                                        <code className="text-xs bg-gray-100 px-2 py-0.5 rounded">{trigger.config.cron}</code>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}
                          {agent.actions?.length > 0 && (
                            <div className="flex items-start gap-2 text-sm">
                              <Zap className="w-4 h-4 text-purple-600 mt-0.5" />
                              <div>
                                <span className="font-semibold text-gray-700">Действия:</span>
                                <div className="text-gray-600 mt-1 space-y-1">
                                  {agent.actions.map((action, idx) => (
                                    <div key={idx} className="flex items-center gap-2">
                                      <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">{action.type}</span>
                                      <span>{action.name}</span>
                                      {action.config?.recipients && (
                                        <span className="text-xs text-gray-500">→ {action.config.recipients}</span>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      <div className="flex gap-2">
                        <button
                          onClick={() => handleExecuteAgent(agent.id)}
                          className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors text-sm"
                        >
                          <Play className="w-4 h-4" />
                          Запустить
                        </button>
                        <button
                          onClick={() => startEditing(agent)}
                          className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm"
                        >
                          <Edit className="w-4 h-4" />
                          Редактировать
                        </button>
                        <button
                          onClick={() => handleDeleteAgent(agent.id)}
                          className="flex items-center gap-2 px-4 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors text-sm"
                        >
                          <Trash2 className="w-4 h-4" />
                          Удалить
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentBuilder;