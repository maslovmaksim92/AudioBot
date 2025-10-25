import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TrendingUp, TrendingDown, DollarSign, CreditCard, Package, Calendar } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function OverviewAnalysis() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCompany, setSelectedCompany] = useState('ВАШ ДОМ ФАКТ');

  useEffect(() => {
    loadData();
  }, [selectedCompany]);

  const loadData = async () => {
    try {
      setLoading(true);
      const params = { company: selectedCompany };
      const response = await axios.get(`${BACKEND_URL}/api/finances/profit-loss`, { params });
      setData(response.data);
    } catch (error) {
      console.error('Error loading financial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(value);
  };

  if (loading) return <div className="text-center p-8">Загрузка...</div>;
  if (!data || !data.profit_loss) return <div className="text-center p-8">Нет данных</div>;

  // Данные из API
  const totalIncome = data.summary?.total_revenue || 0;
  const totalExpense = data.summary?.total_expenses || 0;
  const totalProfit = data.summary?.net_profit || 0;
  
  // Текущий месяц (последний в списке)
  const currentMonthData = data.profit_loss[data.profit_loss.length - 1] || {};
  const currentProfit = currentMonthData.profit || 0;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Общий финансовый анализ</h2>
        <Select value={selectedCompany} onValueChange={setSelectedCompany}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Компания" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ВАШ ДОМ ФАКТ">ВАШ ДОМ ФАКТ</SelectItem>
            <SelectItem value="УФИЦ модель">УФИЦ модель</SelectItem>
            <SelectItem value="ВАШ ДОМ модель">ВАШ ДОМ модель</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      {/* Ключевые показатели */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-green-800 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Общий доход
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900">{formatCurrency(totalIncome)}</div>
            <p className="text-xs text-green-700 mt-1">За все время</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-red-800 flex items-center gap-2">
              <TrendingDown className="h-4 w-4" />
              Общие расходы
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-900">{formatCurrency(totalExpense)}</div>
            <p className="text-xs text-red-700 mt-1">За все время</p>
          </CardContent>
        </Card>

        <Card className={`bg-gradient-to-br ${totalProfit >= 0 ? 'from-blue-50 to-blue-100 border-blue-200' : 'from-orange-50 to-orange-100 border-orange-200'}`}>
          <CardHeader className="pb-3">
            <CardTitle className={`text-sm font-medium ${totalProfit >= 0 ? 'text-blue-800' : 'text-orange-800'} flex items-center gap-2`}>
              <DollarSign className="h-4 w-4" />
              Чистая прибыль
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${totalProfit >= 0 ? 'text-blue-900' : 'text-orange-900'}`}>
              {formatCurrency(totalProfit)}
            </div>
            <p className={`text-xs ${totalProfit >= 0 ? 'text-blue-700' : 'text-orange-700'} mt-1`}>
              {totalProfit >= 0 ? 'Профицит' : 'Дефицит'}
            </p>
          </CardContent>
        </Card>

        <Card className={`bg-gradient-to-br ${data.summary?.average_margin >= 0 ? 'from-purple-50 to-purple-100 border-purple-200' : 'from-orange-50 to-orange-100 border-orange-200'}`}>
          <CardHeader className="pb-3">
            <CardTitle className={`text-sm font-medium ${data.summary?.average_margin >= 0 ? 'text-purple-800' : 'text-orange-800'} flex items-center gap-2`}>
              <Package className="h-4 w-4" />
              Средняя маржа
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${data.summary?.average_margin >= 0 ? 'text-purple-900' : 'text-orange-900'}`}>
              {data.summary?.average_margin?.toFixed(1) || 0}%
            </div>
            <p className={`text-xs ${data.summary?.average_margin >= 0 ? 'text-purple-700' : 'text-orange-700'} mt-1`}>Рентабельность</p>
          </CardContent>
        </Card>
      </div>

      {/* Текущий месяц */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Последний месяц ({currentMonthData.period})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Выручка</p>
              <p className="text-xl font-bold text-green-600">{formatCurrency(currentMonthData.revenue)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Расходы</p>
              <p className="text-xl font-bold text-red-600">{formatCurrency(currentMonthData.expenses)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Прибыль</p>
              <p className={`text-xl font-bold ${currentProfit >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>
                {formatCurrency(currentProfit)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Прибыль по месяцам - ТАБЛИЦА */}
      <Card>
        <CardHeader>
          <CardTitle>Прибыль по месяцам</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Месяц</th>
                  <th className="text-right p-2">Выручка</th>
                  <th className="text-right p-2">Расходы</th>
                  <th className="text-right p-2">Прибыль</th>
                  <th className="text-right p-2">Маржа</th>
                </tr>
              </thead>
              <tbody>
                {data.profit_loss.map((month, index) => {
                  const isProfit = month.profit >= 0;
                  return (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="p-2 font-medium">{month.period}</td>
                      <td className="text-right p-2 text-green-600">{formatCurrency(month.revenue)}</td>
                      <td className="text-right p-2 text-red-600">{formatCurrency(month.expenses)}</td>
                      <td className={`text-right p-2 font-bold ${isProfit ? 'text-blue-600' : 'text-orange-600'}`}>
                        {formatCurrency(month.profit)}
                      </td>
                      <td className="text-right p-2">{month.margin}%</td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="border-t-2 font-bold bg-gray-100">
                  <td className="p-2">ИТОГО</td>
                  <td className="text-right p-2 text-green-700">{formatCurrency(totalIncome)}</td>
                  <td className="text-right p-2 text-red-700">{formatCurrency(totalExpense)}</td>
                  <td className={`text-right p-2 ${totalProfit >= 0 ? 'text-blue-700' : 'text-orange-700'}`}>
                    {formatCurrency(totalProfit)}
                  </td>
                  <td className="text-right p-2">{data.summary?.average_margin?.toFixed(1) || 0}%</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* ПРОГНОЗ НА 2026-2030 */}
      <ForecastSection company={selectedCompany} formatCurrency={formatCurrency} />

    </div>
  );
}

// Компонент прогноза
function ForecastSection({ company, formatCurrency }) {
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadForecast();
  }, [company]);

  const loadForecast = async () => {
    try {
      setLoading(true);
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await axios.get(`${BACKEND_URL}/api/finances/forecast`, { 
        params: { company } 
      });
      setForecastData(response.data);
    } catch (error) {
      console.error('Error loading forecast:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center p-4">Загрузка прогноза...</div>;
  if (!forecastData) return null;

  const { base_data, forecast, investor_metrics } = forecastData;

  return (
    <>
      {/* Прогноз модели на 2026-2030 */}
      <Card className="border-2 border-blue-200 bg-blue-50">
        <CardHeader className="bg-blue-100">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-blue-600" />
            Прогноз модели на 2026-2030
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="mb-4 p-4 bg-white rounded-lg">
            <h3 className="font-semibold text-sm mb-2">Базовый год 2025:</h3>
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Выручка:</span>
                <span className="ml-2 font-bold text-green-600">{formatCurrency(base_data.revenue)}</span>
              </div>
              <div>
                <span className="text-gray-600">Расходы:</span>
                <span className="ml-2 font-bold text-red-600">{formatCurrency(base_data.expenses)}</span>
              </div>
              <div>
                <span className="text-gray-600">Прибыль:</span>
                <span className="ml-2 font-bold text-blue-600">{formatCurrency(base_data.profit)}</span>
              </div>
              <div>
                <span className="text-gray-600">Маржа:</span>
                <span className="ml-2 font-bold">{base_data.margin}%</span>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-blue-100">
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
                    <tr key={index} className="border-b hover:bg-blue-50">
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
                <tr className="border-t-2 font-bold bg-blue-200">
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
            Расчеты для инвестора
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Инвестиции (базовые расходы)</div>
              <div className="text-lg font-bold text-gray-800">{formatCurrency(investor_metrics.investment_amount)}</div>
            </div>
            
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Общая прибыль за 5 лет</div>
              <div className="text-lg font-bold text-green-600">{formatCurrency(investor_metrics.total_profit_5_years)}</div>
            </div>
            
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Средняя прибыль в год</div>
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
                  ? `${investor_metrics.payback_period} ${investor_metrics.payback_period === 1 ? 'год' : 'года/лет'}`
                  : investor_metrics.payback_period}
              </div>
            </div>
            
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Рост выручки (год)</div>
              <div className="text-lg font-bold text-teal-600">+{investor_metrics.revenue_growth_rate.toFixed(1)}%</div>
            </div>
            
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <div className="text-xs text-gray-600 mb-1">Рост расходов (год)</div>
              <div className="text-lg font-bold text-red-600">+{investor_metrics.expense_growth_rate.toFixed(1)}%</div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-white rounded-lg border-l-4 border-green-500">
            <p className="text-sm text-gray-700">
              <strong>Ключевые выводы:</strong> При инвестициях в размере {formatCurrency(investor_metrics.investment_amount)} 
              {' '}прогнозируется получение прибыли {formatCurrency(investor_metrics.total_profit_5_years)} за 5 лет 
              (ROI {investor_metrics.roi_5_years.toFixed(1)}%). Средняя годовая прибыль составит {formatCurrency(investor_metrics.average_annual_profit)}.
              {typeof investor_metrics.payback_period === 'number' && 
                ` Окупаемость инвестиций ожидается через ${investor_metrics.payback_period} ${investor_metrics.payback_period === 1 ? 'год' : 'года/лет'}.`}
            </p>
          </div>
        </CardContent>
      </Card>
    </>
  );
}

export default OverviewAnalysis;
