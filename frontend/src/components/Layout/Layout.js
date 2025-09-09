import React from 'react';
import { useApp } from '../../context/AppContext';
import Sidebar from './Sidebar';
import NotificationBar from './NotificationBar';

const Layout = ({ children }) => {
  const { state } = useApp();
  const { isMenuCollapsed } = state;

  return (
    &lt;div className="min-h-screen bg-gray-50"&gt;
      &lt;Sidebar /&gt;
      
      &lt;div className={`transition-all duration-300 ${
        isMenuCollapsed ? 'ml-16' : 'ml-64'
      }`}&gt;
        &lt;NotificationBar /&gt;
        
        &lt;main className="min-h-screen"&gt;
          {children}
        &lt;/main&gt;
      &lt;/div&gt;
    &lt;/div&gt;
  );
};

export default Layout;