import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TrendingUp, TrendingDown, DollarSign, AlertTriangle, Target, Sparkles } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const SCENARIOS = {
  pessimistic: { name: 'Пессимистичный', color: 'orange', icon: AlertTriangle },
  realistic: { name: 'Реалистичный', color: 'blue', icon: Target },
  optimistic: { name: 'Оптимистичный', color: 'green', icon: Sparkles }
};

function ForecastView() {
  const [selectedCompany, setSelectedCompany] = useState('ВАШ ДОМ модель');
  const [selectedScenario, setSelectedScenario] = useState('realistic');
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadForecast();
  }, [selectedCompany, selectedScenario]);

  const loadForecast = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/finances/forecast`, { 
        params: { 
          company: selectedCompany,
          scenario: selectedScenario
        } 
      });
      setForecastData(response.data);
    } catch (error) {
      console.error('Error loading forecast:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('ru-RU', { 
      style: 'currency', 
      currency: 'RUB', 
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  if (loading) return <div className="text-center p-8">Загрузка прогноза...</div>;
  if (!forecastData) return <div className="text-center p-8">Нет данных</div>;

  const { base_data, forecast, investor_metrics, scenario_info } = forecastData;
  const scenarioConfig = SCENARIOS[selectedScenario];
  const ScenarioIcon = scenarioConfig.icon;

  return (
    <div className="space-y-6">
      {/* Заголовок и селекторы */}
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold">Прогноз 2026-2030</h2>
        <div className="flex gap-4">
          <Select value={selectedCompany} onValueChange={setSelectedCompany}>
            <SelectTrigger className="w-[250px]">
              <SelectValue placeholder="Выберите модель" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ВАШ ДОМ ФАКТ">ВАШ ДОМ ФАКТ</SelectItem>
              <SelectItem value="УФИЦ модель">УФИЦ модель</SelectItem>
              <SelectItem value="ВАШ ДОМ модель">ВАШ ДОМ модель</SelectItem>
            </SelectContent>
          </Select>

          <Select value={selectedScenario} onValueChange={setSelectedScenario}>
            <SelectTrigger className="w-[250px]">
              <SelectValue placeholder="Выберите сценарий" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pessimistic">🔻 Пессимистичный</SelectItem>
              <SelectItem value="realistic">🎯 Реалистичный</SelectItem>
              <SelectItem value="optimistic">✨ Оптимистичный</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Информация о сценарии */}
      <Card className={`border-2 border-${scenarioConfig.color}-300 bg-${scenarioConfig.color}-50`}>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3 mb-4">
            <ScenarioIcon className={`h-8 w-8 text-${scenarioConfig.color}-600`} />
            <div>
              <h3 className="text-xl font-bold">{scenarioConfig.name} сценарий</h3>
              <p className="text-sm text-gray-600">{scenario_info?.description || 'Прогноз на основе текущих данных'}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Рост выручки (год):</span>
              <span className="ml-2 font-bold text-green-600">+{scenario_info?.revenue_growth_rate?.toFixed(1) || 0}%</span>
            </div>
            <div>
              <span className="text-gray-600">Рост расходов (год):</span>
              <span className="ml-2 font-bold text-red-600">+{scenario_info?.expense_growth_rate?.toFixed(1) || 0}%</span>
            </div>
          </div>
          {scenario_info?.cleaners_info && (
            <div className="mt-4 p-3 bg-white rounded-lg border-l-4 border-blue-500">
              <p className="text-sm font-semibold text-blue-800">
                📋 {scenario_info.cleaners_info}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Базовый год */}
      <Card>
        <CardHeader className="bg-gray-100">
          <CardTitle>Базовый год 2025</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-4 gap-6">
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Выручка</div>
              <div className="text-xl font-bold text-green-600">{formatCurrency(base_data.revenue)}</div>
            </div>
            <div className="p-4 bg-red-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Расходы</div>
              <div className="text-xl font-bold text-red-600">{formatCurrency(base_data.expenses)}</div>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Прибыль</div>
              <div className="text-xl font-bold text-blue-600">{formatCurrency(base_data.profit)}</div>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <div className="text-sm text-gray-600 mb-1">Маржа</div>
              <div className="text-xl font-bold text-purple-600">{base_data.margin}%</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Прогноз на 2026-2030 */}
      <Card className={`border-2 border-${scenarioConfig.color}-200`}>
        <CardHeader className={`bg-${scenarioConfig.color}-100`}>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className={`h-6 w-6 text-${scenarioConfig.color}-600`} />
            Прогноз 2026-2030
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={`border-b-2 bg-${scenarioConfig.color}-50`}>
                  <th className="text-left p-3 font-bold">Год</th>
                  <th className="text-right p-3 font-bold">Выручка</th>
                  <th className="text-right p-3 font-bold">Расходы</th>
                  <th className="text-right p-3 font-bold">Прибыль</th>
                  <th className="text-right p-3 font-bold">Маржа</th>
                </tr>
              </thead>
              <tbody>
                {forecast.map((year, index) => {
                  const isProfit = year.profit >= 0;
                  return (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="p-3 font-bold">{year.year}</td>
                      <td className="text-right p-3 text-green-600 font-semibold">{formatCurrency(year.revenue)}</td>
                      <td className="text-right p-3 text-red-600 font-semibold">{formatCurrency(year.expenses)}</td>
                      <td className={`text-right p-3 font-bold ${isProfit ? 'text-blue-600' : 'text-orange-600'}`}>
                        {formatCurrency(year.profit)}
                      </td>
                      <td className="text-right p-3 font-semibold">{year.margin}%</td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="border-t-2 font-bold bg-gray-100">
                  <td className="p-3">ИТОГО 5 лет</td>
                  <td className="text-right p-3 text-green-700">
                    {formatCurrency(forecast.reduce((sum, y) => sum + y.revenue, 0))}
                  </td>
                  <td className="text-right p-3 text-red-700">
                    {formatCurrency(forecast.reduce((sum, y) => sum + y.expenses, 0))}
                  </td>
                  <td className="text-right p-3 text-blue-700">
                    {formatCurrency(forecast.reduce((sum, y) => sum + y.profit, 0))}
                  </td>
                  <td className="text-right p-3">
                    {(forecast.reduce((sum, y) => sum + y.margin, 0) / forecast.length).toFixed(1)}%
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Расчеты для инвестора */}
      <Card className="border-2 border-green-200 bg-green-50">
        <CardHeader className="bg-green-100">
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-6 w-6 text-green-600" />
            Расчеты для инвестора ({scenarioConfig.name} сценарий)
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Инвестиции</div>
              <div className="text-lg font-bold text-gray-800">{formatCurrency(investor_metrics.investment_amount)}</div>
            </div>
            
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Прибыль за 5 лет</div>
              <div className="text-lg font-bold text-green-600">{formatCurrency(investor_metrics.total_profit_5_years)}</div>
            </div>
            
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Средняя прибыль/год</div>
              <div className="text-lg font-bold text-blue-600">{formatCurrency(investor_metrics.average_annual_profit)}</div>
            </div>
            
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Средняя маржа</div>
              <div className="text-lg font-bold text-purple-600">{investor_metrics.average_margin.toFixed(1)}%</div>
            </div>
            
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">ROI за 5 лет</div>
              <div className="text-lg font-bold text-green-700">{investor_metrics.roi_5_years.toFixed(1)}%</div>
            </div>
            
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Срок окупаемости</div>
              <div className="text-lg font-bold text-orange-600">
                {typeof investor_metrics.payback_period === 'number' 
                  ? `${investor_metrics.payback_period} ${investor_metrics.payback_period === 1 ? 'год' : investor_metrics.payback_period < 5 ? 'года' : 'лет'}`
                  : investor_metrics.payback_period}
              </div>
            </div>
            
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Рост выручки</div>
              <div className="text-lg font-bold text-teal-600">+{investor_metrics.revenue_growth_rate.toFixed(1)}%</div>
            </div>
            
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Рост расходов</div>
              <div className="text-lg font-bold text-red-600">+{investor_metrics.expense_growth_rate.toFixed(1)}%</div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-white rounded-lg border-l-4 border-green-500">
            <p className="text-sm text-gray-700">
              <strong>Ключевые выводы:</strong> При инвестициях {formatCurrency(investor_metrics.investment_amount)} 
              {' '}прогнозируется прибыль {formatCurrency(investor_metrics.total_profit_5_years)} за 5 лет 
              (ROI {investor_metrics.roi_5_years.toFixed(1)}%). Средняя годовая прибыль: {formatCurrency(investor_metrics.average_annual_profit)}.
              {typeof investor_metrics.payback_period === 'number' && 
                ` Окупаемость: ${investor_metrics.payback_period} ${investor_metrics.payback_period === 1 ? 'год' : investor_metrics.payback_period < 5 ? 'года' : 'лет'}.`}
            </p>
          </div>
        </CardContent>
      </Card>

    </div>
  );
}

export default ForecastView;
