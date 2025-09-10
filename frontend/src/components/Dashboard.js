import React, { useState } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  Home, MessageCircle, Mic, Calendar, Settings, 
  Phone, PhoneCall, Users, BarChart3, FileText 
} from 'lucide-react';
import Overview from './Overview';
import LiveVoiceChat from './LiveVoiceChat';
import Meetings from './Meetings';
import AIChat from './AIChat';

const Dashboard = () => {
  const location = useLocation();
  
  const navigation = [
    { path: "/", label: "Главная", icon: Home },
    { path: "/ai-chat", label: "AI Чат", icon: MessageCircle },
    { path: "/live-voice", label: "Живой голос", icon: Phone },
    { path: "/meetings", label: "Планерки", icon: Calendar },
    { path: "/analytics", label: "Аналитика", icon: BarChart3 },
    { path: "/settings", label: "Настройки", icon: Settings }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex">
      {/* Sidebar */}
      <div className="w-64 bg-black/20 backdrop-blur-sm border-r border-white/10">
        <div className="p-6">
          <div className="flex items-center space-x-3 mb-8">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
              <MessageCircle className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">VasDom</h1>
              <p className="text-sm text-gray-400">AudioBot AI</p>
            </div>
          </div>
          
          <nav className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      : 'text-gray-300 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <Icon size={20} />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full p-6 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/ai-chat" element={<AIChat />} />
            <Route path="/live-voice" element={<LiveVoiceChat />} />
            <Route path="/meetings" element={<Meetings />} />
            <Route path="/analytics" element={<div className="text-white">Аналитика в разработке...</div>} />
            <Route path="/settings" element={<div className="text-white">Настройки в разработке...</div>} />
          </Routes>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;