import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Enhanced Financial Analytics Component with Plan vs Fact
const FinancialAnalytics = () => {
  const [financialData, setFinancialData] = useState(null);
  const [expenseBreakdown, setExpenseBreakdown] = useState(null);
  const [cashFlow, setCashFlow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('monthly');

  useEffect(() => {
    fetchFinancialData();
  }, []);

  const fetchFinancialData = async () => {
    try {
      setLoading(true);
      
      const [monthlyRes, expenseRes, cashFlowRes] = await Promise.all([
        axios.get(`${API}/financial/monthly-data?months=9`),
        axios.get(`${API}/financial/expense-breakdown`),
        axios.get(`${API}/financial/cash-flow?months=6`)
      ]);
      
      setFinancialData(monthlyRes.data);
      setExpenseBreakdown(expenseRes.data);
      setCashFlow(cashFlowRes.data);
      
    } catch (error) {
      console.error('Error fetching financial data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Анализируем финансы...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">💰 Финансовая аналитика ВасДом</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('monthly')}
            className={`px-4 py-2 rounded-lg ${activeTab === 'monthly' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            📊 План/Факт
          </button>
          <button
            onClick={() => setActiveTab('expenses')}
            className={`px-4 py-2 rounded-lg ${activeTab === 'expenses' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            💸 Расходы
          </button>
          <button
            onClick={() => setActiveTab('cashflow')}
            className={`px-4 py-2 rounded-lg ${activeTab === 'cashflow' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          >
            💳 Денежный поток
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {financialData && financialData.success && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-600">💰 Доходы (план)</h3>
            <p className="text-3xl font-bold text-blue-600 mt-2">
              {financialData.summary.total_plan_revenue?.toLocaleString()} ₽
            </p>
            <p className="text-sm text-gray-500 mt-1">За анализируемый период</p>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-600">💰 Доходы (факт)</h3>
            <p className="text-3xl font-bold text-green-600 mt-2">
              {financialData.summary.total_actual_revenue?.toLocaleString()} ₽
            </p>
            <div className="flex items-center mt-1">
              <span className={`text-sm ${financialData.summary.revenue_achievement >= 100 ? 'text-green-600' : 'text-red-600'}`}>
                {financialData.summary.revenue_achievement}% от плана
              </span>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-600">💸 Расходы (факт)</h3>
            <p className="text-3xl font-bold text-orange-600 mt-2">
              {financialData.summary.total_actual_expenses?.toLocaleString()} ₽
            </p>
            <div className="flex items-center mt-1">
              <span className={`text-sm ${financialData.summary.expense_efficiency <= 100 ? 'text-green-600' : 'text-red-600'}`}>
                {financialData.summary.expense_efficiency}% от плана
              </span>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-sm font-medium text-gray-600">📈 Прибыль</h3>
            <p className="text-3xl font-bold text-purple-600 mt-2">
              {financialData.summary.actual_profit?.toLocaleString()} ₽
            </p>
            <p className="text-sm text-gray-500 mt-1">
              План: {financialData.summary.plan_profit?.toLocaleString()} ₽
            </p>
          </div>
        </div>
      )}

      {/* Monthly Plan vs Fact */}
      {activeTab === 'monthly' && financialData && financialData.success && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-6">📊 План vs Факт по месяцам (сентябрь 2025 - текущий месяц)</h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Месяц</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Доходы План</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Доходы Факт</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Отклонение</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Расходы План</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Расходы Факт</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Прибыль</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {financialData.monthly_data.map((month, index) => (
                  <tr key={month.period} className={month.is_current ? 'bg-blue-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-sm font-medium text-gray-900">
                          {month.month_name}
                        </span>
                        {month.is_current && <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">Текущий</span>}
                        {month.is_future && <span className="ml-2 px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">Прогноз</span>}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {month.revenue.plan.toLocaleString()} ₽
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {month.revenue.actual ? (
                        <span className={month.revenue.variance >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {month.revenue.actual.toLocaleString()} ₽
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {month.revenue.variance !== null ? (
                        <div className="flex items-center">
                          <span className={month.revenue.variance >= 0 ? 'text-green-600' : 'text-red-600'}>
                            {month.revenue.variance > 0 ? '+' : ''}{month.revenue.variance.toLocaleString()} ₽
                          </span>
                          <span className={`ml-2 text-xs ${month.revenue.variance_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ({month.revenue.variance_percent > 0 ? '+' : ''}{month.revenue.variance_percent}%)
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {month.expenses.plan.total.toLocaleString()} ₽
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {month.expenses.actual.total ? (
                        <span className={month.expenses.variance <= 0 ? 'text-green-600' : 'text-red-600'}>
                          {month.expenses.actual.total.toLocaleString()} ₽
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {month.profit.actual !== null ? (
                        <div>
                          <span className={month.profit.actual >= 0 ? 'text-green-600' : 'text-red-600'}>
                            {month.profit.actual.toLocaleString()} ₽
                          </span>
                          <div className="text-xs text-gray-500">
                            План: {month.profit.plan.toLocaleString()} ₽
                          </div>
                        </div>
                      ) : (
                        <div>
                          <span className="text-blue-600">{month.profit.plan.toLocaleString()} ₽</span>
                          <div className="text-xs text-gray-500">Прогноз</div>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* AI Insights for Financial Data */}
          {financialData.ai_insights && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-800 mb-2">🤖 AI Финансовые рекомендации:</h4>
              <div className="text-sm text-blue-700 whitespace-pre-line">
                {financialData.ai_insights}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Expense Breakdown */}
      {activeTab === 'expenses' && expenseBreakdown && expenseBreakdown.success && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-6">💸 Структура расходов клининговой компании</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h4 className="text-md font-medium mb-4">Планируемые vs Фактические расходы</h4>
              <div className="space-y-4">
                {expenseBreakdown.expense_analysis.map((expense, index) => (
                  <div key={expense.category} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h5 className="font-medium text-gray-900">{expense.name}</h5>
                        <p className="text-sm text-gray-600">{expense.description}</p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        expense.efficiency_score >= 1 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {expense.efficiency_score >= 1 ? 'Эффективно' : 'Превышение'}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">План:</span>
                        <span className="ml-2 font-medium">{expense.budget_amount.toLocaleString()} ₽</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Факт:</span>
                        <span className={`ml-2 font-medium ${expense.variance >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {expense.actual_amount.toLocaleString()} ₽
                        </span>
                      </div>
                    </div>
                    
                    <div className="mt-2 flex items-center">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${expense.variance >= 0 ? 'bg-red-500' : 'bg-green-500'}`}
                          style={{width: `${Math.min(100, (expense.actual_amount / expense.budget_amount) * 100)}%`}}
                        />
                      </div>
                      <span className={`ml-3 text-sm ${expense.variance >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {expense.variance_percent > 0 ? '+' : ''}{expense.variance_percent}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="text-md font-medium mb-4">Распределение бюджета</h4>
              <div className="space-y-3">
                {expenseBreakdown.expense_analysis.map((expense, index) => (
                  <div key={expense.category} className="flex justify-between items-center">
                    <span className="text-sm">{expense.name}</span>
                    <div className="flex items-center space-x-3">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full"
                          style={{width: `${expense.budget_percent}%`}}
                        />
                      </div>
                      <span className="text-sm font-medium w-8">{expense.budget_percent}%</span>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h5 className="font-medium mb-2">💡 Оптимизация расходов:</h5>
                <ul className="text-sm text-gray-700 space-y-1">
                  <li>• Зарплаты - крупнейшая статья (45%). Контролируйте производительность</li>
                  <li>• Материалы - следите за ценами поставщиков и остатками</li>
                  <li>• Транспорт - оптимизируйте маршруты для экономии топлива</li>
                  <li>• Накладные расходы - пересматривайте договоры ежегодно</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cash Flow Forecast */}
      {activeTab === 'cashflow' && cashFlow && cashFlow.success && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-6">💳 Прогноз денежного потока</h3>
          
          <div className="mb-4 p-4 bg-blue-50 rounded-lg">
            <div className="flex justify-between items-center">
              <span className="text-lg font-medium text-blue-800">
                Начальный баланс: {cashFlow.starting_balance.toLocaleString()} ₽
              </span>
              <span className="text-sm text-blue-600">на {new Date().toLocaleDateString('ru-RU')}</span>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Месяц</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Остаток на начало</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Поступления</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Расходы</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Чистый поток</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Остаток на конец</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Запас (мес)</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {cashFlow.cash_flow_forecast.map((month, index) => (
                  <tr key={month.period} className={index === 0 ? 'bg-blue-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {month.month_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {month.opening_balance.toLocaleString()} ₽
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                      +{month.inflow.toLocaleString()} ₽
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                      -{month.outflow.toLocaleString()} ₽
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={month.net_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {month.net_cash_flow >= 0 ? '+' : ''}{month.net_cash_flow.toLocaleString()} ₽
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <span className={month.closing_balance >= 100000 ? 'text-green-600' : 'text-red-600'}>
                        {month.closing_balance.toLocaleString()} ₽
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        month.cash_runway_months >= 3 ? 'bg-green-100 text-green-800' : 
                        month.cash_runway_months >= 1 ? 'bg-yellow-100 text-yellow-800' : 
                        'bg-red-100 text-red-800'
                      }`}>
                        {month.cash_runway_months} {month.cash_runway_months === 1 ? 'месяц' : 'месяцев'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-green-50 rounded-lg">
              <h5 className="font-medium text-green-800">💚 Здоровые показатели</h5>
              <p className="text-sm text-green-700 mt-1">Положительный денежный поток и резерв более 3 месяцев</p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <h5 className="font-medium text-yellow-800">⚠️ Требует внимания</h5>
              <p className="text-sm text-yellow-700 mt-1">Резерв 1-3 месяца - планируйте поступления</p>
            </div>
            <div className="p-4 bg-red-50 rounded-lg">
              <h5 className="font-medium text-red-800">🚨 Критический уровень</h5>
              <p className="text-sm text-red-700 mt-1">Резерв менее 1 месяца - срочные меры</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FinancialAnalytics;