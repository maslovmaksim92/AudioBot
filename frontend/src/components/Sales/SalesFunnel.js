import React, { useState } from 'react';
import { 
  TrendingUp, 
  Target, 
  DollarSign, 
  Users,
  BarChart3,
  Calendar,
  CheckCircle,
  Clock,
  AlertCircle,
  Plus,
  Filter,
  Download,
  Eye,
  TrendingDown,
  PieChart,
  Zap
} from 'lucide-react';

const SalesFunnel = () => {
  const [activeTab, setActiveTab] = useState('funnel'); // 'funnel' или 'marketing'

  // Воронка продаж данные
  const funnelStages = [
    {
      id: 'lead',
      name: 'Лидогенерация',
      count: 45,
      value: 2250000,
      color: 'from-blue-500 to-blue-600',
      deals: [
        { id: 1, title: 'УК "Комфорт" - 3 дома', value: 500000, source: 'Сайт', created: '2025-01-05' },
        { id: 2, title: 'ЖК "Новый" - офисы', value: 350000, source: 'Звонок', created: '2025-01-06' }
      ]
    },
    {
      id: 'contact',
      name: 'Первый контакт',
      count: 32,
      value: 1800000,
      color: 'from-purple-500 to-purple-600',
      deals: [
        { id: 3, title: 'ТЦ "Галерея"', value: 1200000, source: 'Тендер', created: '2025-01-03' }
      ]
    },
    {
      id: 'proposal',
      name: 'Коммерческое',
      count: 18,
      value: 1100000,
      color: 'from-indigo-500 to-indigo-600',
      deals: [
        { id: 4, title: 'Школа №15', value: 450000, source: 'Рекомендация', created: '2025-01-02' }
      ]
    },
    {
      id: 'negotiation',
      name: 'Переговоры',
      count: 12,
      value: 950000,
      color: 'from-orange-500 to-orange-600',
      deals: []
    },
    {
      id: 'contract',
      name: 'Договор',
      count: 8,
      value: 600000,
      color: 'from-green-500 to-green-600',
      deals: []
    },
    {
      id: 'won',
      name: 'Закрыто',
      count: 25,
      value: 5200000,
      color: 'from-emerald-500 to-emerald-600',
      deals: []
    }
  ];

  // Маркетинг данные
  const marketingCampaigns = [
    {
      id: 1,
      name: 'Яндекс Директ - Уборка подъездов',
      status: 'active',
      budget: 50000,
      spent: 32500,
      leads: 45,
      cost_per_lead: 722,
      conversions: 8,
      roi: 185,
      channel: 'Яндекс'
    },
    {
      id: 2,
      name: 'Авито - Клининг окон',
      status: 'active',
      budget: 30000,
      spent: 28000,
      leads: 32,
      cost_per_lead: 875,
      conversions: 5,
      roi: 142,
      channel: 'Авито'
    },
    {
      id: 3,
      name: 'ВКонтакте - Общежития',
      status: 'paused',
      budget: 20000,
      spent: 12000,
      leads: 18,
      cost_per_lead: 667,
      conversions: 2,
      roi: 95,
      channel: 'VK'
    },
    {
      id: 4,
      name: 'Сайт - SEO продвижение',
      status: 'active',
      budget: 40000,
      spent: 40000,
      leads: 52,
      cost_per_lead: 769,
      conversions: 12,
      roi: 215,
      channel: 'Органика'
    }
  ];

  const stats = {
    funnel: [
      { label: 'Всего лидов', value: '140', change: '+12%', icon: Users, color: 'blue' },
      { label: 'Конверсия', value: '17.9%', change: '+3.2%', icon: TrendingUp, color: 'green' },
      { label: 'В работе', value: '₽11.9М', change: '+8%', icon: DollarSign, color: 'purple' },
      { label: 'Закрыто', value: '₽5.2М', change: '+15%', icon: CheckCircle, color: 'emerald' }
    ],
    marketing: [
      { label: 'Общий бюджет', value: '₽140К', change: '+10%', icon: DollarSign, color: 'blue' },
      { label: 'Потрачено', value: '₽112.5К', change: '80%', icon: TrendingDown, color: 'orange' },
      { label: 'Лидов', value: '147', change: '+18%', icon: Users, color: 'green' },
      { label: 'CPL средний', value: '₽765', change: '-5%', icon: Target, color: 'purple' }
    ]
  };

  const getStatusBadge = (status) => {
    const badges = {
      active: { label: 'Активна', class: 'bg-green-100 text-green-700' },
      paused: { label: 'Приостановлена', class: 'bg-yellow-100 text-yellow-700' },
      completed: { label: 'Завершена', class: 'bg-gray-100 text-gray-700' }
    };
    return badges[status] || badges.active;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <TrendingUp className="w-10 h-10 text-indigo-600" />
            Воронка продаж
          </h1>
          <p className="text-gray-600">
            Управление продажами и маркетинговыми кампаниями
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-8">
          <button
            onClick={() => setActiveTab('funnel')}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all ${
              activeTab === 'funnel'
                ? 'bg-indigo-600 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <TrendingUp className="w-5 h-5" />
            Воронка продаж
          </button>
          <button
            onClick={() => setActiveTab('marketing')}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all ${
              activeTab === 'marketing'
                ? 'bg-purple-600 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            <Target className="w-5 h-5" />
            Маркетинг
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {(activeTab === 'funnel' ? stats.funnel : stats.marketing).map((stat, index) => (
            <div key={index} className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-${stat.color}-100`}>
                  <stat.icon className={`w-6 h-6 text-${stat.color}-600`} />
                </div>
                <span className={`text-xs font-semibold px-2 py-1 rounded ${
                  stat.change.startsWith('+') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {stat.change}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Funnel View */}
        {activeTab === 'funnel' && (
          <div className="space-y-6">
            {/* Funnel Visualization */}
            <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Этапы воронки</h2>
                <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all">
                  <Plus className="w-4 h-4" />
                  Добавить сделку
                </button>
              </div>

              <div className="space-y-4">
                {funnelStages.map((stage, index) => {
                  const conversion = index > 0 
                    ? ((stage.count / funnelStages[0].count) * 100).toFixed(1) 
                    : 100;
                  
                  return (
                    <div key={stage.id} className="relative">
                      {/* Connector Line */}
                      {index < funnelStages.length - 1 && (
                        <div className="absolute left-8 top-20 w-0.5 h-6 bg-gray-200 z-0" />
                      )}
                      
                      <div className={`relative bg-gradient-to-r ${stage.color} rounded-2xl p-6 text-white shadow-lg hover:shadow-xl transition-all cursor-pointer`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 flex-1">
                            {/* Stage Number */}
                            <div className="w-12 h-12 bg-white bg-opacity-20 rounded-xl flex items-center justify-center text-xl font-bold">
                              {index + 1}
                            </div>

                            {/* Stage Info */}
                            <div className="flex-1">
                              <h3 className="text-xl font-bold mb-1">{stage.name}</h3>
                              <div className="flex items-center gap-4 text-sm text-white text-opacity-90">
                                <span className="flex items-center gap-1">
                                  <Users className="w-4 h-4" />
                                  {stage.count} сделок
                                </span>
                                <span className="flex items-center gap-1">
                                  <DollarSign className="w-4 h-4" />
                                  {(stage.value / 1000000).toFixed(1)}М ₽
                                </span>
                                <span className="flex items-center gap-1">
                                  <BarChart3 className="w-4 h-4" />
                                  {conversion}% конверсия
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex items-center gap-2">
                            <button className="p-2 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 transition-all">
                              <Eye className="w-5 h-5" />
                            </button>
                            <div className="w-16 h-16 bg-white bg-opacity-20 rounded-xl flex items-center justify-center text-3xl">
                              {stage.name === 'Лидогенерация' ? '📢' :
                               stage.name === 'Первый контакт' ? '📞' :
                               stage.name === 'Коммерческое' ? '📄' :
                               stage.name === 'Переговоры' ? '💬' :
                               stage.name === 'Договор' ? '✍️' : '🎉'}
                            </div>
                          </div>
                        </div>

                        {/* Stage Width (Funnel Effect) */}
                        <div 
                          className="absolute bottom-0 left-0 h-1 bg-white bg-opacity-40 rounded-full"
                          style={{ width: `${conversion}%` }}
                        />
                      </div>

                      {/* Deals in Stage */}
                      {stage.deals && stage.deals.length > 0 && (
                        <div className="mt-3 ml-16 space-y-2">
                          {stage.deals.map(deal => (
                            <div key={deal.id} className="bg-white rounded-xl p-4 border-2 border-gray-100 hover:border-indigo-200 transition-all">
                              <div className="flex items-center justify-between">
                                <div>
                                  <h4 className="font-semibold text-gray-900">{deal.title}</h4>
                                  <div className="flex items-center gap-3 text-sm text-gray-600 mt-1">
                                    <span>₽{(deal.value / 1000).toFixed(0)}К</span>
                                    <span>•</span>
                                    <span>{deal.source}</span>
                                    <span>•</span>
                                    <span>{new Date(deal.created).toLocaleDateString('ru-RU')}</span>
                                  </div>
                                </div>
                                <button className="text-indigo-600 hover:text-indigo-700 transition-colors">
                                  <Eye className="w-5 h-5" />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Marketing View */}
        {activeTab === 'marketing' && (
          <div className="space-y-6">
            {/* Controls */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
              <div className="flex items-center justify-between">
                <div className="flex gap-2">
                  <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-all">
                    <Plus className="w-4 h-4" />
                    Новая кампания
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-all">
                    <Filter className="w-4 h-4" />
                    Фильтры
                  </button>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-all">
                  <Download className="w-4 h-4" />
                  Отчет
                </button>
              </div>
            </div>

            {/* Campaigns */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {marketingCampaigns.map(campaign => {
                const budget_progress = (campaign.spent / campaign.budget) * 100;
                const statusBadge = getStatusBadge(campaign.status);

                return (
                  <div key={campaign.id} className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl transition-all">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-purple-500 to-indigo-600 p-6 text-white">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-bold mb-2">{campaign.name}</h3>
                          <span className={`inline-block px-3 py-1 rounded-lg text-xs font-semibold ${statusBadge.class}`}>
                            {statusBadge.label}
                          </span>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-purple-100">Канал</div>
                          <div className="text-lg font-bold">{campaign.channel}</div>
                        </div>
                      </div>

                      {/* Budget Progress */}
                      <div>
                        <div className="flex justify-between text-sm text-purple-100 mb-2">
                          <span>Бюджет: ₽{(campaign.budget / 1000).toFixed(0)}К</span>
                          <span>Потрачено: ₽{(campaign.spent / 1000).toFixed(0)}К ({budget_progress.toFixed(0)}%)</span>
                        </div>
                        <div className="w-full bg-white bg-opacity-20 rounded-full h-2">
                          <div 
                            className="bg-white h-2 rounded-full transition-all"
                            style={{ width: `${budget_progress}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="p-6">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-4 bg-blue-50 rounded-xl">
                          <div className="text-3xl font-bold text-blue-600">{campaign.leads}</div>
                          <div className="text-sm text-gray-600 mt-1">Лидов</div>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-xl">
                          <div className="text-3xl font-bold text-green-600">{campaign.conversions}</div>
                          <div className="text-sm text-gray-600 mt-1">Конверсий</div>
                        </div>
                        <div className="text-center p-4 bg-purple-50 rounded-xl">
                          <div className="text-3xl font-bold text-purple-600">₽{campaign.cost_per_lead}</div>
                          <div className="text-sm text-gray-600 mt-1">CPL</div>
                        </div>
                        <div className="text-center p-4 bg-amber-50 rounded-xl">
                          <div className="text-3xl font-bold text-amber-600">{campaign.roi}%</div>
                          <div className="text-sm text-gray-600 mt-1">ROI</div>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2 mt-4">
                        <button className="flex-1 py-2 bg-purple-100 text-purple-700 rounded-xl hover:bg-purple-200 transition-all font-medium">
                          Редактировать
                        </button>
                        <button className="flex-1 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-all font-medium">
                          Аналитика
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Marketing Plan AI */}
            <div className="bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl shadow-2xl p-8 text-white">
              <div className="flex items-start gap-6">
                <div className="w-16 h-16 bg-white bg-opacity-20 rounded-2xl flex items-center justify-center flex-shrink-0">
                  <Zap className="w-8 h-8" />
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold mb-3">AI Маркетинговый план</h3>
                  <p className="text-purple-100 mb-6">
                    Позвольте AI анализировать конкурентов, планировать кампании и оптимизировать бюджет для максимального ROI
                  </p>
                  <div className="flex gap-4">
                    <button className="px-6 py-3 bg-white text-purple-600 rounded-xl hover:bg-gray-100 transition-all font-semibold">
                      Запустить AI планирование
                    </button>
                    <button className="px-6 py-3 bg-white bg-opacity-20 text-white rounded-xl hover:bg-opacity-30 transition-all font-semibold">
                      Анализ конкурентов
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SalesFunnel;