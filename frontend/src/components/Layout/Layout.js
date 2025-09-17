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
  LogOut
} from 'lucide-react';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Обзор', href: '/dashboard', icon: Home, color: 'text-blue-600' },
    { name: 'Дома', href: '/works', icon: Building2, color: 'text-green-600' },
    { name: 'AI Чат', href: '/ai-chat', icon: Bot, color: 'text-purple-600' },
    { name: 'Сотрудники', href: '/employees', icon: Users, color: 'text-orange-600' },
    { name: 'Логи', href: '/logs', icon: FileText, color: 'text-gray-600' },
  ];

  const isActiveRoute = (href) => {
    if (href === '/dashboard' && location.pathname === '/') return true;
    return location.pathname === href;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
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
        lg:translate-x-0 lg:static lg:inset-0
      `}>
        <div className="flex h-full flex-col bg-white border-r border-gray-200 shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <img src={process.env.PUBLIC_URL + '/logo.png'} alt="VasDom" className="w-10 h-10 rounded-xl object-contain bg-white border" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">Ваш Дом</h1>
                <p className="text-sm text-gray-500">AudioBot</p>
              </div>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const isActive = isActiveRoute(item.href);
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200
                    ${isActive 
                      ? 'bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 border border-blue-200 shadow-sm' 
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `}
                >
                  <item.icon className={`mr-3 w-5 h-5 ${isActive ? 'text-blue-600' : item.color}`} />
                  {item.name}
                  {isActive && (
                    <div className="ml-auto w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">ВД</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">ВасДом</p>
                  <p className="text-xs text-gray-500">Администратор</p>
                </div>
              </div>
              <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-72">
        {/* Top bar */}
        <div className="sticky top-0 z-40 flex items-center justify-between bg-white/90 backdrop-blur border-b border-gray-200 px-3 py-1.5 shadow-sm">
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
          <div className="animate-slide-up pt-0 px-4">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;