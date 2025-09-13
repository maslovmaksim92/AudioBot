import React from 'react';
import { useApp } from '../../context/AppContext';
import { Button } from '../UI';

const Sidebar = () => {
  const { state, actions } = useApp();
  const { currentSection, isMenuCollapsed } = state;

  const menuItems = [
    { id: 'general', name: 'Обзор', icon: '📊', description: 'Главная панель' },
    { id: 'voice', name: 'AI Чат', icon: '🤖', description: 'Голосовой помощник' },
    { id: 'meetings', name: 'Планерки', icon: '🎤', description: 'Записи совещаний' },
    { id: 'works', name: 'Дома', icon: '🏠', description: 'Управление домами' },
    { id: 'analytics', name: 'Аналитика', icon: '📊', description: 'Отчеты и аналитика' },
    { id: 'ai-tasks', name: 'AI Задачи', icon: '🧠', description: 'Умные задачи' },
    { id: 'training', name: 'Обучение', icon: '📚', description: 'База знаний' },
    { id: 'employees', name: 'Сотрудники', icon: '👥', description: 'Управление бригадами' },
    { id: 'logs', name: 'Логи', icon: '📝', description: 'Системные логи' }
  ];

  const handleMenuClick = (sectionId) => {
    actions.setCurrentSection(sectionId);
    console.log(`📍 Navigation: switched to ${sectionId}`);
  };

  return (
    <>
      {/* Мобильный overlay */}
      {!isMenuCollapsed && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={actions.toggleMenu}
        />
      )}
      
      {/* Sidebar */}
      <div className={`bg-white shadow-lg transition-all duration-300 ${
        isMenuCollapsed 
          ? 'w-16 -translate-x-full md:translate-x-0' 
          : 'w-64 translate-x-0'
      } h-screen fixed left-0 top-0 z-50 flex flex-col`}>
      
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {!isMenuCollapsed && (
            <div>
              <h1 className="text-xl font-bold text-gray-900">VasDom AI</h1>
              <p className="text-xs text-gray-600">Клининг-система</p>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={actions.toggleMenu}
            className="p-2"
          >
            {isMenuCollapsed ? '→' : '←'}
          </Button>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 overflow-y-auto py-4">
        <div className="space-y-1 px-2">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleMenuClick(item.id)}
              className={`w-full flex items-center px-3 py-3 rounded-lg text-left transition-colors ${
                currentSection === item.id
                  ? 'bg-blue-100 text-blue-700 border-l-4 border-blue-500'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              title={isMenuCollapsed ? item.name : item.description}
            >
              <span className="text-lg mr-3 flex-shrink-0">{item.icon}</span>
              {!isMenuCollapsed && (
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{item.name}</p>
                  <p className="text-xs text-gray-500 truncate">{item.description}</p>
                </div>
              )}
            </button>
          ))}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        {!isMenuCollapsed ? (
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-2">
              Статус: <span className="text-green-600">Активен</span>
            </div>
            <div className="text-xs text-gray-400">
              v3.0.0 • {new Date().getFullYear()}
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" title="Система активна"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;