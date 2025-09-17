import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './components/Dashboard/Dashboard';
import Works from './components/Works/Works';
import AIChat from './components/AIChat/AIChat';
import Employees from './components/Employees/Employees';
import Logs from './components/Logs/Logs';
import Meetings from './components/Meetings/Meetings';
import Training from './components/Training/Training';
import Tasks from './components/Tasks/Tasks';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/works" element={<Works />} />
            <Route path="/ai-chat" element={<AIChat />} />
            <Route path="/employees" element={<Employees />} />
            <Route path="/logs" element={<Logs />} />
          </Routes>
        </Layout>
      </div>
    </Router>
  );
}

export default App;