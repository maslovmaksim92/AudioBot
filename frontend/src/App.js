import React, { useState, useEffect } from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './components/Dashboard/Dashboard';
import Works from './components/Works/Works';
import CleaningCalendar from './components/Calendar/CleaningCalendar';
import WorksConstructor from './components/Works/WorksConstructor';
import AIChat from './components/AIChat/AIChat';
import Meetings from './components/Meetings/Meetings';
import LiveConversation from './components/LiveConversation/LiveConversation';
import Tasks from './components/Tasks/Tasks';
import FunctionStudio from './components/FunctionStudio/FunctionStudio';
import Employees from './components/Employees/Employees';
import SalesFunnel from './components/Sales/SalesFunnel';
import AITasks from './components/AITasks/AITasks';
import Training from './components/Training/Training';
import Logistics from './components/Logistics/Logistics';
import Logs from './components/Logs/Logs';
import AgentBuilder from './components/AgentBuilder/AgentBuilder';
import AgentDashboard from './components/AgentDashboard/AgentDashboard';
import AIImprovementModal from './components/AIImprovement/AIImprovementModal';
import Finances from './components/Finances/Finances';

function App() {
  const [improvementModalOpen, setImprovementModalOpen] = useState(false);
  const [currentSection, setCurrentSection] = useState('');

  useEffect(() => {
    const handleOpenAIImprovement = (e) => {
      setCurrentSection(e.detail.section);
      setImprovementModalOpen(true);
    };

    window.addEventListener('openAIImprovement', handleOpenAIImprovement);
    return () => window.removeEventListener('openAIImprovement', handleOpenAIImprovement);
  }, []);

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/works" element={<Works />} />
          <Route path="/works/constructor" element={<WorksConstructor />} />
          <Route path="/calendar" element={<CleaningCalendar />} />
          <Route path="/employees" element={<Employees />} />
          <Route path="/sales" element={<SalesFunnel />} />
          <Route path="/ai" element={<AIChat />} />
          <Route path="/ai-tasks" element={<AITasks />} />
          <Route path="/meetings" element={<Meetings />} />
          <Route path="/live" element={<LiveConversation />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/constructor" element={<FunctionStudio />} />
          <Route path="/training" element={<Training />} />
          <Route path="/logistics" element={<Logistics />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/finances" element={<Finances />} />
          <Route path="/agents" element={<AgentBuilder />} />
          <Route path="/agents/dashboard" element={<AgentDashboard />} />
        </Routes>
      </Layout>

      {/* AI Improvement Modal */}
      <AIImprovementModal
        isOpen={improvementModalOpen}
        onClose={() => setImprovementModalOpen(false)}
        sectionName={currentSection}
      />
    </Router>
  );
}

export default App;