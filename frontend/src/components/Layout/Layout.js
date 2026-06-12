import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Building2, 
  Bot, 
  Users, 
  FileText,
  Menu,
  X,
  Settings,
  LogOut,
  TrendingUp,
  Calendar,
  Truck,
  BookOpen,
  ClipboardList,
  Sparkles,
  DollarSign,
  Activity,
  Mic,
  Phone
, CheckCircle, Scissors, Network} from 'lucide-react';
import logo from '../../assets/logo.png';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Обзор', href: '/dashboard', icon: Home, color: 'text-blue-600' },
    { name: '👑 Собственнику', href: '/owner', icon: Home, color: 'text-amber-600' },
    { name: '✅ Выполнение', href: '/execution', icon: CheckCircle, color: 'text-green-600' },
    { name: 'Дома', href: '/works', icon: Building2, color: 'text-green-600' },
    { name: 'Календарь уборок', href: '/calendar', icon: Calendar, color: 'text-purple-600' },
    { name: '🪟 Шторы', href: '/curtains', icon: Scissors, color: 'text-indigo-600' },
    { name: '🧭 Структура', href: '/structure', icon: Network, color: 'text-sky-600' },
  ];

  const isActiveRoute = (href) => {
    if (href === '/dashboard' && location.pathname === '/') return true;
    return location.pathname === href;
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-72 transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:relative lg:flex lg:flex-shrink-0
      `}>
        <div className="flex h-full flex-col bg-white border-r border-gray-200">
          {/* Header with Logo */}
          <div className="flex items-center justify-between p-6 border-b border-gray-100">
            <div className="flex flex-col items-center w-full">
              <img 
                src={logo} 
                alt="VasDom Logo" 
                className="w-32 h-auto mb-2"
              />
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-50 absolute top-4 right-4"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            {navigation.map((item) => {
              const isActive = isActiveRoute(item.href);
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center px-4 py-3 text-sm font-light rounded-lg transition-colors
                    ${isActive 
                      ? 'bg-gray-900 text-white' 
                      : 'text-gray-700 hover:bg-gray-50'
                    }
                  `}
                >
                  <item.icon className={`mr-3 w-5 h-5 ${isActive ? 'text-white' : 'text-gray-500'}`} />
                  {item.name}
                  {isActive && (
                    <div className="ml-auto w-1.5 h-1.5 bg-white rounded-full" />
                  )}
                </Link>
              );
            })}
          </nav>


        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <div className="sticky top-0 z-40 flex items-center justify-between bg-white/90 backdrop-blur border-b border-gray-200 px-6 py-4 shadow-sm">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
          >
            <Menu className="w-6 h-6" />
          </button>
          
          <div className="flex items-center space-x-4">
            <div className="hidden sm:block">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Система активна</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-2 bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-2 rounded-full">
              <Bot className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-700">AI Готов</span>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <div className="animate-slide-up px-6 py-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;