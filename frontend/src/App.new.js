import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider, useApp } from './context/AppContext';
import { Layout } from './components/Layout';

// Page Components
import Dashboard from './components/Dashboard/Dashboard';
import AIChat from './components/AIChat/AIChat';
import Meetings from './components/Meetings/Meetings';
import Works from './components/Works/Works';
import Employees from './components/Employees/Employees';

// Lazy load less frequently used components
const AITasks = React.lazy(() => import('./components/AITasks/AITasks'));
const Training = React.lazy(() => import('./components/Training/Training'));
const Logs = React.lazy(() => import('./components/Logs/Logs'));

import './App.css';

// Console logging for debugging
console.log('🔗 VasDom AudioBot Frontend (Modular) initialized');
console.log('🔗 Backend URL:', process.env.REACT_APP_BACKEND_URL);

// Main App Router Component
const AppRouter = () => {
  const { state } = useApp();
  const { currentSection } = state;

  // Section to component mapping
  const sectionComponents = {
    'general': Dashboard,
    'voice': AIChat,
    'meetings': Meetings,
    'works': Works,
    'employees': Employees,
    'ai-tasks': React.lazy(() => import('./components/AITasks/AITasks')),
    'training': React.lazy(() => import('./components/Training/Training')),
    'logs': React.lazy(() => import('./components/Logs/Logs'))
  };

  const CurrentComponent = sectionComponents[currentSection] || Dashboard;

  return (
    &lt;Layout&gt;
      &lt;React.Suspense 
        fallback={
          &lt;div className="flex justify-center items-center h-64"&gt;
            &lt;div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"&gt;&lt;/div&gt;
            &lt;span className="ml-2 text-gray-600"&gt;Загрузка...&lt;/span&gt;
          &lt;/div&gt;
        }
      &gt;
        &lt;CurrentComponent /&gt;
      &lt;/React.Suspense&gt;
    &lt;/Layout&gt;
  );
};

// Alternative Router-based approach (commented out for now)
const AppWithRouter = () => {
  return (
    &lt;AppProvider&gt;
      &lt;Router&gt;
        &lt;Layout&gt;
          &lt;React.Suspense 
            fallback={
              &lt;div className="flex justify-center items-center h-64"&gt;
                &lt;div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"&gt;&lt;/div&gt;
                &lt;span className="ml-2 text-gray-600"&gt;Загрузка компонента...&lt;/span&gt;
              &lt;/div&gt;
            }
          &gt;
            &lt;Routes&gt;
              &lt;Route path="/" element={&lt;Navigate to="/dashboard" replace /&gt;} /&gt;
              &lt;Route path="/dashboard" element={&lt;Dashboard /&gt;} /&gt;
              &lt;Route path="/ai-chat" element={&lt;AIChat /&gt;} /&gt;
              &lt;Route path="/meetings" element={&lt;Meetings /&gt;} /&gt;
              &lt;Route path="/works" element={&lt;Works /&gt;} /&gt;
              &lt;Route path="/employees" element={&lt;Employees /&gt;} /&gt;
              &lt;Route path="/ai-tasks" element={&lt;AITasks /&gt;} /&gt;
              &lt;Route path="/training" element={&lt;Training /&gt;} /&gt;
              &lt;Route path="/logs" element={&lt;Logs /&gt;} /&gt;
              &lt;Route path="*" element={&lt;Navigate to="/dashboard" replace /&gt;} /&gt;
            &lt;/Routes&gt;
          &lt;/React.Suspense&gt;
        &lt;/Layout&gt;
      &lt;/Router&gt;
    &lt;/AppProvider&gt;
  );
};

// Main App Component
function App() {
  console.log('🚀 VasDom AudioBot App (Modular Architecture) starting...');

  return (
    &lt;AppProvider&gt;
      &lt;AppRouter /&gt;
    &lt;/AppProvider&gt;
  );
}

export default App;