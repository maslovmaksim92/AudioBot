import React from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './components/Dashboard/Dashboard';
import Works from './components/Works/Works';
import AIChat from './components/AIChat/AIChat';
import Meetings from './components/Meetings/Meetings';
import LiveConversation from './components/LiveConversation/LiveConversation';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/works" element={<Works />} />
          <Route path="/ai" element={<AIChat />} />
          <Route path="/meetings" element={<Meetings />} />
          <Route path="/live" element={<LiveConversation />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;