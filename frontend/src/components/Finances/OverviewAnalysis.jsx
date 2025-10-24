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
            <SelectItem value="ООО ВАШ ДОМ">ООО ВАШ ДОМ</SelectItem>
            <SelectItem value="УФИЦ">УФИЦ</SelectItem>
            <SelectItem value="ООО ВАШ ДОМ + УФИЦ">ООО ВАШ ДОМ + УФИЦ</SelectItem>
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

    </div>
  );
}

export default OverviewAnalysis;
