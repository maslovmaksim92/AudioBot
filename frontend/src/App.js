import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Layout } from './components/Layout';

// Page Components
import Dashboard from './components/Dashboard/Dashboard';
import AIChat from './components/AIChat/AIChat';
import Meetings from './components/Meetings/Meetings';
import Tasks from './components/Tasks/Tasks';
import Works from './components/Works/Works';
import Employees from './components/Employees/Employees';

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
    'tasks': Tasks,
    'ai-tasks': React.lazy(() => import('./components/AITasks/AITasks')),
    'training': React.lazy(() => import('./components/Training/Training')),
    'logs': React.lazy(() => import('./components/Logs/Logs'))
  };

  const CurrentComponent = sectionComponents[currentSection] || Dashboard;

  return (
    <Layout>
      <React.Suspense 
        fallback={
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Загрузка...</span>
          </div>
        }
      >
        <CurrentComponent />
      </React.Suspense>
    </Layout>
  );
};

// Main App Component
function App() {
  console.log('🚀 VasDom AudioBot App (Modular Architecture) starting...');

  return (
    <AppProvider>
      <AppRouter />
    </AppProvider>
  );
}

export default App;