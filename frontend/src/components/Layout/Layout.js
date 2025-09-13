import React from 'react';
import { useApp } from '../../context/AppContext';
import Sidebar from './Sidebar';
import NotificationBar from './NotificationBar';

const Layout = ({ children }) => {
  const { state } = useApp();
  const { isMenuCollapsed } = state;

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      
      {/* Улучшенная мобильная адаптивность */}
      <div className={`transition-all duration-300 ${
        // Мобильные устройства: полная ширина, десктоп: отступ от sidebar
        isMenuCollapsed 
          ? 'ml-0 md:ml-16' 
          : 'ml-0 md:ml-64'
      }`}>
        <NotificationBar />
        
        <main className="min-h-screen p-2 md:p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;