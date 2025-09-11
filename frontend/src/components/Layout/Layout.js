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
      <div className={`transition-all duration-300 ${
        isMenuCollapsed ? 'ml-16' : 'ml-64'
      }`}>
        <NotificationBar />
        <main className="min-h-screen">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;