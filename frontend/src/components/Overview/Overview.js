import React from "react";
import { MessageCircle, Mic, Brain, Zap, Users, Activity } from "lucide-react";
import { Link } from "react-router-dom";

const Overview = () => {
  const stats = [
    { icon: MessageCircle, label: "Сообщений", value: "1,234", color: "from-blue-500 to-blue-600" },
    { icon: Mic, label: "Голосовых чатов", value: "89", color: "from-green-500 to-green-600" },
    { icon: Brain, label: "AI запросов", value: "456", color: "from-purple-500 to-purple-600" },
    { icon: Users, label: "Активных пользователей", value: "12", color: "from-orange-500 to-orange-600" },
  ];

  const features = [
    {
      icon: MessageCircle,
      title: "Текстовый чат с AI",
      description: "Общение с продвинутым AI помощником в текстовом формате",
      link: "/ai-chat",
      color: "from-blue-500 to-cyan-500"
    },
    {
      icon: Mic,
      title: "Живой голосовой чат",
      description: "Разговор с AI используя человеческий голос через OpenAI Realtime API",
      link: "/voice",
      color: "from-green-500 to-emerald-500"
    },
    {
      icon: Brain,
      title: "Умный анализ",
      description: "Глубокое понимание контекста и интеллектуальные ответы",
      link: "/ai-chat",
      color: "from-purple-500 to-violet-500"
    },
    {
      icon: Zap,
      title: "Быстрые ответы",
      description: "Мгновенная обработка запросов и оперативная поддержка",
      link: "/ai-chat",
      color: "from-yellow-500 to-orange-500"
    }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl lg:text-6xl font-bold gradient-text">
          VasDom AudioBot
        </h1>
        <p className="text-xl text-gray-300 max-w-2xl mx-auto">
          Продвинутый AI помощник с поддержкой живого голосового общения
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="glass rounded-xl p-6 hover:bg-white/15 transition-all duration-300">
              <div className="flex items-center space-x-4">
                <div className={`p-3 bg-gradient-to-r ${stat.color} rounded-lg`}>
                  <Icon className="text-white" size={24} />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{stat.value}</p>
                  <p className="text-sm text-gray-400">{stat.label}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <Link
              key={index}
              to={feature.link}
              className="group glass rounded-xl p-8 hover:bg-white/15 transition-all duration-300 hover:scale-105 cursor-pointer"
            >
              <div className="space-y-4">
                <div className={`w-16 h-16 bg-gradient-to-r ${feature.color} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                  <Icon className="text-white" size={28} />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white group-hover:gradient-text transition-all duration-300">
                    {feature.title}
                  </h3>
                  <p className="text-gray-400 mt-2 group-hover:text-gray-300 transition-colors duration-300">
                    {feature.description}
                  </p>
                </div>
                <div className="flex items-center text-blue-400 group-hover:text-blue-300 transition-colors duration-300">
                  <span className="text-sm font-medium">Открыть</span>
                  <Activity className="ml-2" size={16} />
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="glass rounded-xl p-8">
        <h2 className="text-2xl font-bold text-white mb-6">Быстрые действия</h2>
        <div className="flex flex-wrap gap-4">
          <Link
            to="/ai-chat"
            className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg text-white font-medium hover:from-blue-600 hover:to-purple-700 transition-all duration-300 hover:scale-105"
          >
            <MessageCircle size={20} />
            <span>Начать чат</span>
          </Link>
          <Link
            to="/voice"
            className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg text-white font-medium hover:from-green-600 hover:to-emerald-700 transition-all duration-300 hover:scale-105"
          >
            <Mic size={20} />
            <span>Голосовой чат</span>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Overview;