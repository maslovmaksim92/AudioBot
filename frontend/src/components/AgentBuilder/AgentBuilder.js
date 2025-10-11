import React, { useState } from 'react';
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
  Sparkles
} from 'lucide-react';

const AgentBuilder = () => {
  const [agents, setAgents] = useState([
    {
      id: 1,
      name: 'Планёрка AI',
      description: 'Напоминает о планёрке в 8:25, звонит сотрудникам в 16:55',
      type: 'scheduler',
      status: 'active',
      triggers: ['Cron: 8:25', 'Cron: 16:55'],
      actions: ['Telegram уведомление', 'AI звонок'],
      icon: Calendar,
      color: 'from-blue-500 to-cyan-500'
    },
    {
      id: 2,
      name: 'Bitrix Синхронизация',
      description: 'Автоматически загружает дома из Bitrix24 каждые 15 минут',
      type: 'integration',
      status: 'active',
      triggers: ['Cron: */15 * * * *'],
      actions: ['Загрузка домов', 'Обновление БД'],
      icon: Database,
      color: 'from-green-500 to-emerald-500'
    },
    {
      id: 3,
      name: 'Telegram Фото Бот',
      description: 'Принимает ~300 фото/день от бригад и публикует в группу',
      type: 'bot',
      status: 'active',
      triggers: ['Telegram webhook'],
      actions: ['Сохранение фото', 'Публикация в группу'],
      icon: MessageSquare,
      color: 'from-purple-500 to-pink-500'
    }
  ]);

  const [showBuilder, setShowBuilder] = useState(false);
  const [newAgent, setNewAgent] = useState({
    name: '',
    description: '',
    type: 'custom',
    triggers: [],
    actions: []
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

  const getStatusColor = (status) => {
    return status === 'active' 
      ? 'bg-green-100 text-green-700' 
      : 'bg-gray-100 text-gray-700';
  };

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
              onClick={() => setShowBuilder(!showBuilder)}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
            >
              <Plus className="w-5 h-5" />
              Создать агента
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <Bot className="w-8 h-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">{agents.length}</span>
            </div>
            <p className="text-sm text-gray-600">Активных агентов</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <Zap className="w-8 h-8 text-yellow-600" />
              <span className="text-2xl font-bold text-gray-900">1.2K</span>
            </div>
            <p className="text-sm text-gray-600">Выполнено сегодня</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="w-8 h-8 text-green-600" />
              <span className="text-2xl font-bold text-gray-900">98%</span>
            </div>
            <p className="text-sm text-gray-600">Успешность</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <Users className="w-8 h-8 text-purple-600" />
              <span className="text-2xl font-bold text-gray-900">24</span>
            </div>
            <p className="text-sm text-gray-600">Пользователей</p>
          </div>
        </div>

        {/* Agent Builder Modal */}
        {showBuilder && (
          <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-100 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Новый агент</h2>
              <button
                onClick={() => setShowBuilder(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                ✕
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

            {/* Triggers */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">Триггеры (когда запускать)</label>
              <div className="grid grid-cols-5 gap-3">
                {availableTriggers.map(trigger => (
                  <button
                    key={trigger.id}
                    className="p-3 rounded-xl border-2 border-gray-200 hover:border-indigo-300 transition-all text-center"
                  >
                    <trigger.icon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
                    <div className="text-xs font-medium text-gray-700">{trigger.name}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">Действия (что делать)</label>
              <div className="grid grid-cols-6 gap-3">
                {availableActions.map(action => (
                  <button
                    key={action.id}
                    className="p-3 rounded-xl border-2 border-gray-200 hover:border-purple-300 transition-all text-center"
                  >
                    <action.icon className="w-6 h-6 mx-auto mb-1 text-gray-600" />
                    <div className="text-xs font-medium text-gray-700">{action.name}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button className="flex-1 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all flex items-center justify-center gap-2 font-semibold">
                <Save className="w-5 h-5" />
                Сохранить агента
              </button>
              <button className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-all font-semibold">
                Отмена
              </button>
            </div>
          </div>
        )}

        {/* Agents List */}
        <div className="space-y-4">
          {agents.map(agent => (
            <div 
              key={agent.id}
              className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl transition-all group"
            >
              <div className={`h-2 bg-gradient-to-r ${agent.color}`} />
              
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className={`w-14 h-14 rounded-xl bg-gradient-to-r ${agent.color} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                      <agent.icon className="w-7 h-7 text-white" />
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-bold text-gray-900">{agent.name}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(agent.status)}`}>
                          {agent.status === 'active' ? 'Активен' : 'Неактивен'}
                        </span>
                      </div>
                      <p className="text-gray-600 mb-4">{agent.description}</p>

                      <div className="flex items-center gap-6">
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Триггеры</p>
                          <div className="flex flex-wrap gap-2">
                            {agent.triggers.map((trigger, i) => (
                              <span key={i} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-medium">
                                {trigger}
                              </span>
                            ))}
                          </div>
                        </div>

                        <ArrowRight className="w-5 h-5 text-gray-300" />

                        <div>
                          <p className="text-xs text-gray-500 mb-1">Действия</p>
                          <div className="flex flex-wrap gap-2">
                            {agent.actions.map((action, i) => (
                              <span key={i} className="px-2 py-1 bg-purple-50 text-purple-700 rounded text-xs font-medium">
                                {action}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                      <Settings className="w-5 h-5 text-gray-400" />
                    </button>
                    <button className="p-2 hover:bg-green-50 rounded-lg transition-colors">
                      <Play className="w-5 h-5 text-green-600" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AgentBuilder;