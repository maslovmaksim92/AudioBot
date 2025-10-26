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
  const [selectedCompany, setSelectedCompany] = useState('ВАШ ДОМ ФАКТ');
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
              <SelectItem value="ВАШ ДОМ ФАКТ">ВАШ ДОМ+УФИЦ</SelectItem>
              <SelectItem value="УФИЦ модель">УФИЦ модель</SelectItem>
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
          
          {/* Показатели роста */}
          <div className="grid grid-cols-2 gap-4 text-sm mb-4">
            <div>
              <span className="text-gray-600">Рост выручки (год):</span>
              <span className="ml-2 font-bold text-green-600">+{scenario_info?.revenue_growth_rate?.toFixed(1) || 0}%</span>
            </div>
            <div>
              <span className="text-gray-600">Рост расходов (год):</span>
              <span className="ml-2 font-bold text-red-600">+{scenario_info?.expense_growth_rate?.toFixed(1) || 0}%</span>
            </div>
          </div>

          {/* Расширенное описание сценария */}
          {scenario_info?.detailed_description && (
            <div className="mt-4 space-y-3">
              {scenario_info.detailed_description.summary && (
                <div className="p-3 bg-white rounded-lg border-l-4 border-blue-500">
                  <p className="text-sm font-semibold text-blue-800">
                    💡 {scenario_info.detailed_description.summary}
                  </p>
                </div>
              )}
              
              {scenario_info.detailed_description.revenue_factors && scenario_info.detailed_description.revenue_factors.length > 0 && (
                <div className="p-3 bg-white rounded-lg">
                  <p className="text-sm font-bold text-green-700 mb-2">📈 За счет чего рост выручки:</p>
                  <ul className="space-y-1">
                    {scenario_info.detailed_description.revenue_factors.map((factor, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start">
                        <span className="text-green-600 mr-2">•</span>
                        <span>{factor}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {scenario_info.detailed_description.expense_factors && scenario_info.detailed_description.expense_factors.length > 0 && (
                <div className="p-3 bg-white rounded-lg">
                  <p className="text-sm font-bold text-red-700 mb-2">📊 Структура расходов:</p>
                  <ul className="space-y-1">
                    {scenario_info.detailed_description.expense_factors.map((factor, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start">
                        <span className="text-red-600 mr-2">•</span>
                        <span>{factor}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Юнит-экономика с таблицей по годам */}
              {scenario_info.detailed_description.unit_economics && selectedCompany === 'УФИЦ модель' && (
                <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                  <p className="text-sm font-bold text-purple-800 mb-3">💰 Юнит-экономика на 1 сотрудника (2026-2030):</p>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead>
                        <tr className="border-b border-purple-300">
                          <th className="text-left py-2 px-2 text-purple-700">Год</th>
                          <th className="text-right py-2 px-2 text-green-700">Выручка</th>
                          <th className="text-right py-2 px-2 text-red-700">Расходы</th>
                          <th className="text-right py-2 px-2 text-blue-700">Прибыль</th>
                          <th className="text-right py-2 px-2 text-gray-700">Сотрудников</th>
                        </tr>
                      </thead>
                      <tbody>
                        {forecast && forecast.map((year, idx) => {
                          const unitRevenue = year.revenue / scenario_info.detailed_description.unit_economics.total_employees;
                          const unitExpense = year.expenses / scenario_info.detailed_description.unit_economics.total_employees;
                          const unitProfit = unitRevenue - unitExpense;
                          return (
                            <tr key={idx} className="border-b border-purple-100">
                              <td className="py-2 px-2 font-semibold">{year.year}</td>
                              <td className="text-right py-2 px-2 text-green-600">{Math.round(unitRevenue).toLocaleString('ru-RU')} ₽</td>
                              <td className="text-right py-2 px-2 text-red-600">{Math.round(unitExpense).toLocaleString('ru-RU')} ₽</td>
                              <td className="text-right py-2 px-2 text-blue-600">{Math.round(unitProfit).toLocaleString('ru-RU')} ₽</td>
                              <td className="text-right py-2 px-2 text-gray-600">{scenario_info.detailed_description.unit_economics.total_employees}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              
              {scenario_info.detailed_description.advantages && scenario_info.detailed_description.advantages.length > 0 && (
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-sm font-bold text-green-800 mb-2">✅ Преимущества сценария:</p>
                  <ul className="space-y-1">
                    {scenario_info.detailed_description.advantages.map((advantage, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start">
                        <span className="text-green-600 mr-2">•</span>
                        <span>{advantage}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {scenario_info.detailed_description.disadvantages && scenario_info.detailed_description.disadvantages.length > 0 && (
                <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                  <p className="text-sm font-bold text-red-800 mb-2">⚠️ Недостатки и риски:</p>
                  <ul className="space-y-1">
                    {scenario_info.detailed_description.disadvantages.map((disadvantage, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start">
                        <span className="text-red-600 mr-2">•</span>
                        <span>{disadvantage}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Юнит-экономика */}
          {scenario_info?.detailed_description?.unit_economics && (
            <div className="mt-4 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border-2 border-indigo-200">
              <p className="text-sm font-bold text-indigo-800 mb-3">💰 Юнит-экономика на 1 сотрудника (2026):</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-white p-3 rounded-lg shadow-sm">
                  <p className="text-xs text-gray-600 mb-1">Выручка</p>
                  <p className="text-lg font-bold text-green-600">
                    {formatCurrency(scenario_info.detailed_description.unit_economics.revenue_per_employee)}
                  </p>
                </div>
                <div className="bg-white p-3 rounded-lg shadow-sm">
                  <p className="text-xs text-gray-600 mb-1">Расходы</p>
                  <p className="text-lg font-bold text-red-600">
                    {formatCurrency(scenario_info.detailed_description.unit_economics.expense_per_employee)}
                  </p>
                </div>
                <div className="bg-white p-3 rounded-lg shadow-sm">
                  <p className="text-xs text-gray-600 mb-1">Прибыль</p>
                  <p className="text-lg font-bold text-blue-600">
                    {formatCurrency(scenario_info.detailed_description.unit_economics.profit_per_employee)}
                  </p>
                </div>
                <div className="bg-white p-3 rounded-lg shadow-sm">
                  <p className="text-xs text-gray-600 mb-1">Всего сотрудников</p>
                  <p className="text-lg font-bold text-purple-600">
                    {scenario_info.detailed_description.unit_economics.total_employees}
                  </p>
                </div>
              </div>
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

      {/* Детализация доходов и расходов */}
      {forecast[0]?.revenue_breakdown && forecast[0]?.expense_breakdown && (
        <Card className={`border-2 border-${scenarioConfig.color}-200`}>
          <CardHeader className={`bg-${scenarioConfig.color}-50`}>
            <CardTitle className="flex items-center gap-2">
              📊 Детализация доходов и расходов по годам
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-6">
              {/* Доходы */}
              <div>
                <h3 className="text-lg font-bold mb-4 text-green-700">Структура доходов</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b-2 bg-green-50">
                        <th className="text-left p-3 font-bold">Год</th>
                        {selectedCompany === 'УФИЦ модель' ? (
                          <>
                            <th className="text-right p-3 font-bold">Швеи</th>
                            <th className="text-right p-3 font-bold">Уборщицы</th>
                            <th className="text-right p-3 font-bold">Аутсорсинг</th>
                          </>
                        ) : (
                          Object.keys(forecast[0]?.revenue_breakdown || {}).map((key, idx) => (
                            <th key={idx} className="text-right p-3 font-bold capitalize">{key.replace(/_/g, ' ')}</th>
                          ))
                        )}
                        <th className="text-right p-3 font-bold">Всего</th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecast.map((year, index) => {
                        const breakdown = year.revenue_breakdown || {};
                        const total = Object.values(breakdown).reduce((sum, val) => sum + (val || 0), 0);
                        return (
                          <tr key={index} className="border-b hover:bg-gray-50">
                            <td className="p-3 font-bold">{year.year}</td>
                            {selectedCompany === 'УФИЦ модель' ? (
                              <>
                                <td className="text-right p-3 text-emerald-600">{formatCurrency(breakdown.sewing || 0)}</td>
                                <td className="text-right p-3 text-teal-600">{formatCurrency(breakdown.cleaning || 0)}</td>
                                <td className="text-right p-3 text-cyan-600">{formatCurrency(breakdown.outsourcing || 0)}</td>
                              </>
                            ) : (
                              Object.entries(breakdown).map(([key, value], idx) => (
                                <td key={idx} className="text-right p-3 text-emerald-600">{formatCurrency(value || 0)}</td>
                              ))
                            )}
                            <td className="text-right p-3 font-bold text-green-700">{formatCurrency(year.revenue)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot>
                      <tr className="border-t-2 font-bold bg-green-100">
                        <td className="p-3">ИТОГО 5 лет</td>
                        {selectedCompany === 'УФИЦ модель' ? (
                          <>
                            <td className="text-right p-3 text-emerald-700">
                              {formatCurrency(forecast.reduce((sum, y) => sum + (y.revenue_breakdown?.sewing || 0), 0))}
                            </td>
                            <td className="text-right p-3 text-teal-700">
                              {formatCurrency(forecast.reduce((sum, y) => sum + (y.revenue_breakdown?.cleaning || 0), 0))}
                            </td>
                            <td className="text-right p-3 text-cyan-700">
                              {formatCurrency(forecast.reduce((sum, y) => sum + (y.revenue_breakdown?.outsourcing || 0), 0))}
                            </td>
                          </>
                        ) : (
                          forecast[0]?.revenue_breakdown && Object.keys(forecast[0].revenue_breakdown).map((key, idx) => (
                            <td key={idx} className="text-right p-3 text-emerald-700">
                              {formatCurrency(forecast.reduce((sum, y) => sum + (y.revenue_breakdown?.[key] || 0), 0))}
                            </td>
                          ))
                        )}
                        <td className="text-right p-3 text-green-800">
                          {formatCurrency(forecast.reduce((sum, y) => sum + y.revenue, 0))}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {/* Расходы */}
              <div>
                <h3 className="text-lg font-bold mb-4 text-red-700">Структура расходов</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b-2 bg-red-50">
                        <th className="text-left p-3 font-bold">Год</th>
                        {forecast[0]?.expense_breakdown && Object.keys(forecast[0].expense_breakdown).map((key, idx) => (
                          <th key={idx} className="text-right p-3 font-bold capitalize">{key.replace(/_/g, ' ')}</th>
                        ))}
                        <th className="text-right p-3 font-bold">Всего</th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecast.map((year, index) => {
                        const breakdown = year.expense_breakdown || {};
                        return (
                          <tr key={index} className="border-b hover:bg-gray-50">
                            <td className="p-3 font-bold">{year.year}</td>
                            {Object.entries(breakdown).map(([key, value], idx) => (
                              <td key={idx} className="text-right p-3 text-red-600">{formatCurrency(value || 0)}</td>
                            ))}
                            <td className="text-right p-3 font-bold text-red-700">{formatCurrency(year.expenses)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot>
                      <tr className="border-t-2 font-bold bg-red-100">
                        <td className="p-3">ИТОГО 5 лет</td>
                        {forecast[0]?.expense_breakdown && Object.keys(forecast[0].expense_breakdown).map((key, idx) => (
                          <td key={idx} className="text-right p-3 text-red-700">
                            {formatCurrency(forecast.reduce((sum, y) => sum + (y.expense_breakdown?.[key] || 0), 0))}
                          </td>
                        ))}
                        <td className="text-right p-3 text-red-800">
                          {formatCurrency(forecast.reduce((sum, y) => sum + y.expenses, 0))}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {/* Пояснение */}
              <div className="mt-4 p-4 bg-blue-50 rounded-lg border-l-4 border-blue-500">
                <p className="text-sm text-blue-800">
                  <strong>💡 О прогнозе:</strong> 
                  {selectedCompany === 'УФИЦ модель' ? (
                    <> Прогноз построен на основе фактических данных 2025 года с учетом трех сценариев развития. 
                    Доходы включают: пошив (швеи), клининг (уборщицы) и аутсорсинг персонала. 
                    Расходы: ФОТ (фонд оплаты труда), управленческие расходы и обслуживание помещений. 
                    Индексация: пессимистичный и реалистичный - 4.8% ежегодно, оптимистичный - 6.9% ежегодно (с 2027 года).</>
                  ) : (
                    <> Прогноз построен на основе консолидированных данных ВАШ ДОМ и УФИЦ за 2025 год. 
                    Учитывает масштабирование бизнеса, оптимизацию расходов и повышение эффективности. 
                    Инвестиции: 40 млн рублей. Маржа растет с 22% (2026) до 37% (2030) за счет оптимизации процессов.</>
                  )}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
