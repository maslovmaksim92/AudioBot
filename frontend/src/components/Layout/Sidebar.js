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
    &lt;div className={`bg-white shadow-lg transition-all duration-300 ${
      isMenuCollapsed ? 'w-16' : 'w-64'
    } h-screen fixed left-0 top-0 z-10 flex flex-col`}&gt;
      
      {/* Header */}
      &lt;div className="p-4 border-b border-gray-200"&gt;
        &lt;div className="flex items-center justify-between"&gt;
          {!isMenuCollapsed && (
            &lt;div&gt;
              &lt;h1 className="text-xl font-bold text-gray-900"&gt;VasDom AI&lt;/h1&gt;
              &lt;p className="text-xs text-gray-600"&gt;Клининг-система&lt;/p&gt;
            &lt;/div&gt;
          )}
          &lt;Button
            variant="ghost"
            size="sm"
            onClick={actions.toggleMenu}
            className="p-2"
          &gt;
            {isMenuCollapsed ? '→' : '←'}
          &lt;/Button&gt;
        &lt;/div&gt;
      &lt;/div&gt;

      {/* Navigation Menu */}
      &lt;nav className="flex-1 overflow-y-auto py-4"&gt;
        &lt;div className="space-y-1 px-2"&gt;
          {menuItems.map((item) => (
            &lt;button
              key={item.id}
              onClick={() => handleMenuClick(item.id)}
              className={`w-full flex items-center px-3 py-3 rounded-lg text-left transition-colors ${
                currentSection === item.id
                  ? 'bg-blue-100 text-blue-700 border-l-4 border-blue-500'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              title={isMenuCollapsed ? item.name : item.description}
            &gt;
              &lt;span className="text-lg mr-3 flex-shrink-0"&gt;{item.icon}&lt;/span&gt;
              {!isMenuCollapsed && (
                &lt;div className="flex-1 min-w-0"&gt;
                  &lt;p className="text-sm font-medium truncate"&gt;{item.name}&lt;/p&gt;
                  &lt;p className="text-xs text-gray-500 truncate"&gt;{item.description}&lt;/p&gt;
                &lt;/div&gt;
              )}
            &lt;/button&gt;
          ))}
        &lt;/div&gt;
      &lt;/nav&gt;

      {/* Footer */}
      &lt;div className="p-4 border-t border-gray-200"&gt;
        {!isMenuCollapsed ? (
          &lt;div className="text-center"&gt;
            &lt;div className="text-xs text-gray-500 mb-2"&gt;
              Статус: &lt;span className="text-green-600"&gt;Активен&lt;/span&gt;
            &lt;/div&gt;
            &lt;div className="text-xs text-gray-400"&gt;
              v3.0.0 • {new Date().getFullYear()}
            &lt;/div&gt;
          &lt;/div&gt;
        ) : (
          &lt;div className="flex justify-center"&gt;
            &lt;div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" title="Система активна"&gt;&lt;/div&gt;
          &lt;/div&gt;
        )}
      &lt;/div&gt;
    &lt;/div&gt;
  );
};

export default Sidebar;