import React, { useState } from 'react';
import { Settings, Activity, Calendar, MessageSquare } from 'lucide-react';
import AgentBuilder from '../AgentBuilder/AgentBuilder';
import AgentDashboard from '../AgentDashboard/AgentDashboard';
import AITasks from '../AITasks/AITasks';

const Agents = () => {
  const [activeTab, setActiveTab] = useState('builder');

  const tabs = [
    { id: 'builder', name: 'Агенты', icon: Settings },
    { id: 'monitoring', name: 'Мониторинг', icon: Activity },
    { id: 'ai-tasks', name: 'AI Задачи', icon: Calendar },
    { id: 'telegram-bot', name: 'Telegram Бот', icon: MessageSquare },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with Tabs */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="px-6 py-4">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            🤖 Агенты и Автоматизация
          </h1>
          
          {/* Tabs Navigation */}
          <div className="flex space-x-1 border-b border-gray-200">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 px-4 py-3 font-medium text-sm
                    border-b-2 transition-colors
                    ${isActive
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                    }
                  `}
                  data-testid={`tab-${tab.id}`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.name}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'builder' && <AgentBuilder />}
        {activeTab === 'monitoring' && <AgentDashboard />}
        {activeTab === 'ai-tasks' && <AITasks />}
        {activeTab === 'telegram-bot' && <TelegramBotConfig />}
      </div>
    </div>
  );
};

// Компонент настройки Telegram бота
const TelegramBotConfig = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          📱 Настройка Telegram Бота для Бригад
        </h2>
        
        <div className="space-y-6">
          {/* Статус */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-green-800">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="font-semibold">Бот активен</span>
            </div>
            <p className="text-sm text-green-700 mt-2">
              Telegram бот работает и готов принимать фото от бригад
            </p>
          </div>

          {/* Инструкция */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-3">
              📖 Инструкция для бригад:
            </h3>
            <ol className="space-y-2 text-sm text-blue-800">
              <li>1. Откройте Telegram бота</li>
              <li>2. Отправьте команду <code className="bg-blue-100 px-2 py-1 rounded">/start</code></li>
              <li>3. Выберите дом из списка</li>
              <li>4. Отправьте фото уборки (одно или несколько)</li>
              <li>5. Когда закончите, отправьте <code className="bg-blue-100 px-2 py-1 rounded">/done</code></li>
            </ol>
          </div>

          {/* Workflow */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">
              🔄 Workflow бота:
            </h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                  1
                </div>
                <div>
                  <div className="font-medium text-gray-900">Список домов</div>
                  <div className="text-sm text-gray-600">
                    Бот показывает дома на сегодня для бригады
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                  2
                </div>
                <div>
                  <div className="font-medium text-gray-900">Выбор дома</div>
                  <div className="text-sm text-gray-600">
                    Бригада выбирает дом через inline кнопки
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                  3
                </div>
                <div>
                  <div className="font-medium text-gray-900">Загрузка фото</div>
                  <div className="text-sm text-gray-600">
                    Отправка фото уборки (поддерживается несколько фото)
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                  4
                </div>
                <div>
                  <div className="font-medium text-gray-900">AI подпись и отправка</div>
                  <div className="text-sm text-gray-600">
                    Генерируется AI подпись через GPT-3.5, фото отправляются с подписью
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Режим работы */}
          <div className="border-t pt-4">
            <h3 className="font-semibold text-gray-900 mb-3">
              ⚙️ Текущий режим:
            </h3>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="font-medium text-yellow-900 mb-2">
                🧪 Тестовый режим
              </div>
              <p className="text-sm text-yellow-800">
                Фото отправляются обратным сообщением пользователю для тестирования.
                Для production нужно переключить на отправку в целевую группу.
              </p>
            </div>
          </div>

          {/* Статистика (заглушка) */}
          <div className="border-t pt-4">
            <h3 className="font-semibold text-gray-900 mb-3">
              📊 Статистика (ближайшее обновление):
            </h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-gray-900">—</div>
                <div className="text-sm text-gray-600">Уборок сегодня</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-gray-900">—</div>
                <div className="text-sm text-gray-600">Фото загружено</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-gray-900">—</div>
                <div className="text-sm text-gray-600">Активных бригад</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Agents;
