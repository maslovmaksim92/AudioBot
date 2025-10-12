import React, { useState } from 'react';
import { MessageSquare, Phone, History } from 'lucide-react';
import AIChat from './AIChat';
import LiveConversation from '../LiveConversation/LiveConversation';

const AIChatWrapper = () => {
  const [activeTab, setActiveTab] = useState('chat');

  const tabs = [
    { id: 'chat', name: 'Чат', icon: MessageSquare },
    { id: 'live', name: 'Живой разговор', icon: Phone },
    { id: 'history', name: 'История', icon: History },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with Tabs */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="px-6 py-4">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            💬 AI Ассистент
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
                      ? 'border-purple-600 text-purple-600'
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
      <div className={activeTab === 'chat' ? '' : 'p-6'}>
        {activeTab === 'chat' && <AIChat />}
        {activeTab === 'live' && <LiveConversation />}
        {activeTab === 'history' && <ChatHistory />}
      </div>
    </div>
  );
};

// Компонент истории чата (заглушка)
const ChatHistory = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          📜 История диалогов
        </h2>
        
        <div className="space-y-4">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-gray-900">Диалог от 12 октября 2025</span>
              <span className="text-sm text-gray-600">10:30 - 11:15</span>
            </div>
            <p className="text-sm text-gray-700">
              Вопросы о графике уборок, статистике бригад и расписании на ноябрь
            </p>
            <div className="mt-2 flex gap-2">
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">45 сообщений</span>
              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Web</span>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-gray-900">Диалог от 11 октября 2025</span>
              <span className="text-sm text-gray-600">14:20 - 14:45</span>
            </div>
            <p className="text-sm text-gray-700">
              Консультация по рекламациям клиентов и фото уборок
            </p>
            <div className="mt-2 flex gap-2">
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">23 сообщения</span>
              <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">Telegram</span>
            </div>
          </div>

          <div className="text-center py-8 text-gray-500">
            <p>Полная история диалогов будет доступна после реализации синхронизации</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIChatWrapper;
