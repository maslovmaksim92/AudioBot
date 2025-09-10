import React from 'react';
import { Link } from 'react-router-dom';
import { MessageCircle, Mic, Calendar, BarChart3, Zap, Brain, Phone } from 'lucide-react';

const Overview = () => {
  const features = [
    {
      icon: MessageCircle,
      title: "AI Чат",
      description: "Интеллектуальное общение с AI помощником на базе GPT-4",
      link: "/ai-chat",
      color: "from-blue-500 to-cyan-500",
      stats: "Самообучающийся AI"
    },
    {
      icon: Phone,
      title: "Живой голосовой чат",
      description: "Разговор с AI используя естественный человеческий голос",
      link: "/live-voice",
      color: "from-green-500 to-emerald-500",
      stats: "GPT-4o Realtime API"
    },
    {
      icon: Calendar,
      title: "Умные планерки",
      description: "Транскрибация, анализ и автоматическая постановка задач в Битрикс",
      link: "/meetings",
      color: "from-purple-500 to-pink-500",
      stats: "Интеграция с Bitrix24"
    },
    {
      icon: BarChart3,
      title: "Аналитика и метрики",
      description: "Детальная статистика использования и производительности AI",
      link: "/analytics",
      color: "from-orange-500 to-red-500",
      stats: "Real-time данные"
    }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-5xl lg:text-7xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent mb-4">
          VasDom AudioBot
        </h1>
        <p className="text-xl text-gray-300 max-w-3xl mx-auto">
          Революционная AI платформа для клининговой компании с живым голосовым чатом, 
          умными планерками и интеграцией с Битрикс24
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {[
          { label: "Диалогов", value: "1,247", change: "+12%" },
          { label: "Средний рейтинг", value: "4.8", change: "+0.3" },
          { label: "Планерок", value: "89", change: "+7" },
          { label: "Задач в Битрикс", value: "156", change: "+23" }
        ].map((stat, index) => (
          <div key={index} className="bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">{stat.label}</p>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
              </div>
              <span className="text-xs text-green-400 bg-green-400/10 px-2 py-1 rounded">
                {stat.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          
          return (
            <Link
              key={index}
              to={feature.link}
              className="group bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl p-8 hover:border-white/20 transition-all duration-300 hover:scale-[1.02]"
            >
              <div className="flex items-start space-x-6">
                <div className={`p-4 rounded-xl bg-gradient-to-r ${feature.color} group-hover:scale-110 transition-transform duration-300`}>
                  <Icon className="text-white" size={32} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xl font-bold text-white group-hover:text-blue-300 transition-colors">
                      {feature.title}
                    </h3>
                    <span className="text-xs text-blue-400 bg-blue-400/10 px-3 py-1 rounded-full">
                      {feature.stats}
                    </span>
                  </div>
                  <p className="text-gray-300 leading-relaxed">
                    {feature.description}
                  </p>
                  <div className="mt-4 flex items-center text-blue-400 text-sm font-medium">
                    Открыть →
                  </div>
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-8">
        <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
          <Zap className="mr-3 text-yellow-400" />
          Быстрые действия
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/live-voice"
            className="flex items-center space-x-3 p-4 bg-green-500/10 border border-green-500/20 rounded-lg hover:bg-green-500/20 transition-all"
          >
            <Phone className="text-green-400" size={20} />
            <span className="text-white font-medium">Начать живой разговор</span>
          </Link>
          <Link
            to="/meetings"
            className="flex items-center space-x-3 p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg hover:bg-purple-500/20 transition-all"
          >
            <Calendar className="text-purple-400" size={20} />
            <span className="text-white font-medium">Создать планерку</span>
          </Link>
          <Link
            to="/ai-chat"
            className="flex items-center space-x-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg hover:bg-blue-500/20 transition-all"
          >
            <Brain className="text-blue-400" size={20} />
            <span className="text-white font-medium">Задать вопрос AI</span>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Overview;