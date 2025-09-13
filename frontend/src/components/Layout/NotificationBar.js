import React, { useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { Button } from '../UI';

const NotificationBar = () => {
  const { state, actions } = useApp();
  const { notifications, isMenuCollapsed } = state;

  useEffect(() => {
    // Auto-remove notifications after 5 seconds
    notifications.forEach(notification => {
      if (notification.id) {
        setTimeout(() => {
          actions.removeNotification(notification.id);
        }, 5000);
      }
    });
  }, [notifications, actions]);

  return (
    <>
      {/* Мобильная кнопка меню */}
      <div className="md:hidden bg-white shadow-sm border-b border-gray-200 p-3 flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={actions.toggleMenu}
          className="p-2 text-gray-600 hover:text-gray-900"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </Button>
        <div className="text-lg font-semibold text-gray-900">VasDom AI</div>
        <div className="w-8"></div> {/* Spacer */}
      </div>

      {/* Notifications */}
      {notifications.length > 0 && (
        <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map(notification => (
        <div
          key={notification.id}
          className={`p-4 rounded-lg shadow-lg border-l-4 ${
            notification.type === 'success' 
              ? 'bg-green-50 border-green-400 text-green-800'
              : notification.type === 'error'
              ? 'bg-red-50 border-red-400 text-red-800'
              : notification.type === 'warning'
              ? 'bg-yellow-50 border-yellow-400 text-yellow-800'
              : 'bg-blue-50 border-blue-400 text-blue-800'
          }`}
        >
          <div className="flex justify-between items-start">
            <div className="flex">
              <div className="flex-shrink-0">
                {notification.type === 'success' && '✅'}
                {notification.type === 'error' && '❌'}
                {notification.type === 'warning' && '⚠️'}
                {notification.type === 'info' && 'ℹ️'}
              </div>
              <div className="ml-2">
                <p className="text-sm font-medium">{notification.message}</p>
                {notification.details && (
                  <p className="text-xs mt-1 opacity-75">{notification.details}</p>
                )}
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => actions.removeNotification(notification.id)}
              className="ml-2 text-current hover:bg-current hover:bg-opacity-20"
            >
              ×
            </Button>
          </div>
        </div>
      ))}
        </div>
      )}
    </>
  );
};

export default NotificationBar;