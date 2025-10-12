import React, { useState, useEffect } from 'react';
import './SalesFunnel.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

const SalesFunnel = () => {
  const [view, setView] = useState('funnel'); // 'funnel' или 'marketing'
  const [deals, setDeals] = useState([]);
  const [marketingCampaigns, setMarketingCampaigns] = useState([]);

  // Статусы воронки
  const funnelStages = [
    { id: 'lead', name: 'Лидогенерация', icon: '📢', color: '#3b82f6' },
    { id: 'contact', name: 'Первый контакт', icon: '📞', color: '#8b5cf6' },
    { id: 'meeting', name: 'Встреча/Замер', icon: '📏', color: '#6366f1' },
    { id: 'proposal', name: 'Коммерческое', icon: '📄', color: '#f59e0b' },
    { id: 'negotiation', name: 'Переговоры', icon: '💬', color: '#f97316' },
    { id: 'contract', name: 'Договор', icon: '✍️', color: '#10b981' },
    { id: 'won', name: 'Сделка закрыта', icon: '🎉', color: '#059669' }
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    // Загрузка сделок
    setDeals([
      { id: 1, title: 'ЖК Новый', stage: 'lead', value: 500000, company: 'УК Сервис' },
      { id: 2, title: 'ТЦ Галерея', stage: 'contact', value: 1200000, company: 'ООО Торг' },
      { id: 3, title: 'Офис Центр', stage: 'proposal', value: 350000, company: 'БизнесПарк' },
      { id: 4, title: 'ЖК Светлый', stage: 'negotiation', value: 800000, company: 'УК Комфорт' },
      { id: 5, title: 'Школа №5', stage: 'contract', value: 450000, company: 'Минобр' }
    ]);

    // Маркетинговые кампании
    setMarketingCampaigns([
      {
        id: 1,
        name: 'Яндекс Директ - Уборка подъездов',
        status: 'active',
        budget: 50000,
        spent: 32500,
        leads: 45,
        cost_per_lead: 722,
        conversions: 8
      },
      {
        id: 2,
        name: 'Авито - Клининг окон',
        status: 'active',
        budget: 30000,
        spent: 18200,
        leads: 28,
        cost_per_lead: 650,
        conversions: 5
      },
      {
        id: 3,
        name: 'Telegram - Холодная база',
        status: 'paused',
        budget: 15000,
        spent: 8400,
        leads: 12,
        cost_per_lead: 700,
        conversions: 2
      }
    ]);
  };

  const getDealsByStage = (stageId) => {
    return deals.filter(d => d.stage === stageId);
  };

  const getTotalByStage = (stageId) => {
    return getDealsByStage(stageId).reduce((sum, d) => sum + d.value, 0);
  };

  return (
    <div className="sales-funnel-container">
      {/* Шапка */}
      <div className="sales-header">
        <div>
          <h1>📊 Воронка продаж и Маркетинг</h1>
          <p className="subtitle">Управление продажами и рекламными кампаниями</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-primary">➕ Новая сделка</button>
          <button className="btn btn-secondary">➕ Новая кампания</button>
        </div>
      </div>

      {/* Переключатель */}
      <div className="view-switcher">
        <button
          className={`switch-btn ${view === 'funnel' ? 'active' : ''}`}
          onClick={() => setView('funnel')}
        >
          📈 Воронка продаж
        </button>
        <button
          className={`switch-btn ${view === 'marketing' ? 'active' : ''}`}
          onClick={() => setView('marketing')}
        >
          🎯 Маркетинг
        </button>
      </div>

      {/* Контент */}
      {view === 'funnel' ? (
        <div className="funnel-board">
          {funnelStages.map(stage => (
            <div key={stage.id} className="funnel-column">
              <div className="column-header" style={{ background: stage.color }}>
                <span className="stage-icon">{stage.icon}</span>
                <span className="stage-name">{stage.name}</span>
                <span className="stage-count">({getDealsByStage(stage.id).length})</span>
              </div>

              <div className="column-total">
                💰 {getTotalByStage(stage.id).toLocaleString()} ₽
              </div>

              <div className="column-deals">
                {getDealsByStage(stage.id).map(deal => (
                  <div key={deal.id} className="deal-card">
                    <h4>{deal.title}</h4>
                    <p className="deal-company">🏢 {deal.company}</p>
                    <div className="deal-value">
                      💰 {deal.value.toLocaleString()} ₽
                    </div>
                    <div className="deal-actions">
                      <button className="icon-btn">✏️</button>
                      <button className="icon-btn">👁️</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="marketing-dashboard">
          {/* AI Аналитика */}
          <div className="ai-insights">
            <div className="insight-card ai">
              <div className="insight-header">
                <h3>🤖 AI Рекомендации</h3>
                <span className="badge-new">Новое</span>
              </div>
              <div className="insight-content">
                <div className="recommendation">
                  <span className="rec-icon">💡</span>
                  <div>
                    <strong>Увеличьте бюджет Яндекс Директ на 20%</strong>
                    <p>CPL снизился до 722₽, конверсия растет. Прогноз: +12 лидов/месяц</p>
                  </div>
                </div>
                <div className="recommendation">
                  <span className="rec-icon">⚠️</span>
                  <div>
                    <strong>Приостановите кампанию в Telegram</strong>
                    <p>Высокая стоимость лида (700₽), низкая конверсия (16.7%). Пересмотрите таргетинг</p>
                  </div>
                </div>
                <div className="recommendation">
                  <span className="rec-icon">🎯</span>
                  <div>
                    <strong>Создайте кампанию "Мытье окон - весна"</strong>
                    <p>Сезонный спрос растет. Рекомендуемый бюджет: 40,000₽</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Кампании */}
          <div className="campaigns-grid">
            {marketingCampaigns.map(campaign => (
              <div key={campaign.id} className="campaign-card">
                <div className="campaign-header">
                  <h3>{campaign.name}</h3>
                  <span className={`status-badge ${campaign.status}`}>
                    {campaign.status === 'active' ? '🟢 Активна' : '⏸️ Пауза'}
                  </span>
                </div>

                <div className="campaign-stats">
                  <div className="stat-row">
                    <span className="stat-label">Бюджет</span>
                    <span className="stat-value">{campaign.budget.toLocaleString()} ₽</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Потрачено</span>
                    <span className="stat-value">{campaign.spent.toLocaleString()} ₽</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Лидов</span>
                    <span className="stat-value">{campaign.leads}</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">CPL</span>
                    <span className="stat-value">{campaign.cost_per_lead} ₽</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Конверсия</span>
                    <span className="stat-value">
                      {((campaign.conversions / campaign.leads) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                <div className="campaign-progress">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${(campaign.spent / campaign.budget) * 100}%` }}
                    />
                  </div>
                  <span className="progress-text">
                    {((campaign.spent / campaign.budget) * 100).toFixed(0)}% бюджета
                  </span>
                </div>

                <div className="campaign-actions">
                  <button className="btn-small">📊 Аналитика</button>
                  <button className="btn-small">✏️ Редактировать</button>
                  {campaign.status === 'active' ? (
                    <button className="btn-small">⏸️ Пауза</button>
                  ) : (
                    <button className="btn-small">▶️ Запустить</button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* AI Генератор маркетингового плана */}
          <div className="marketing-planner">
            <h3>🎯 AI Генератор маркетингового плана</h3>
            <p>Автоматическое создание и запуск рекламных кампаний на основе анализа рынка</p>
            <button className="btn btn-generate">
              ⚡ Сгенерировать план на месяц
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesFunnel;
