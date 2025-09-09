import React, { useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { Button } from '../UI';

const NotificationBar = () => {
  const { state, actions } = useApp();
  const { notifications } = state;

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

  if (notifications.length === 0) return null;

  return (
    &lt;div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm"&gt;
      {notifications.map(notification => (
        &lt;div
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
        &gt;
          &lt;div className="flex justify-between items-start"&gt;
            &lt;div className="flex"&gt;
              &lt;div className="flex-shrink-0"&gt;
                {notification.type === 'success' && '✅'}
                {notification.type === 'error' && '❌'}
                {notification.type === 'warning' && '⚠️'}
                {notification.type === 'info' && 'ℹ️'}
              &lt;/div&gt;
              &lt;div className="ml-2"&gt;
                &lt;p className="text-sm font-medium"&gt;{notification.message}&lt;/p&gt;
                {notification.details && (
                  &lt;p className="text-xs mt-1 opacity-75"&gt;{notification.details}&lt;/p&gt;
                )}
              &lt;/div&gt;
            &lt;/div&gt;
            &lt;Button
              variant="ghost"
              size="sm"
              onClick={() => actions.removeNotification(notification.id)}
              className="ml-2 text-current hover:bg-current hover:bg-opacity-20"
            &gt;
              ×
            &lt;/Button&gt;
          &lt;/div&gt;
        &lt;/div&gt;
      ))}
    &lt;/div&gt;
  );
};

export default NotificationBar;