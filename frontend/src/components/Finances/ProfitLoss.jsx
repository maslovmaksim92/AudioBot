import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, DollarSign, Percent } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function ProfitLoss() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProfitLoss();
  }, []);

  const fetchProfitLoss = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/finances/profit-loss`);
      setData(response.data);
    } catch (error) {
      console.error('Error fetching profit/loss:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center p-8">Загрузка...</div>;
  }

  if (!data) {
    return <div className="text-center p-8">Нет данных</div>;
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-blue-800">Выручка</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">
              {formatCurrency(data.summary.total_revenue)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-orange-800">Расходы</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-900">
              {formatCurrency(data.summary.total_expenses)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-green-800 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Чистая прибыль
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900">
              {formatCurrency(data.summary.net_profit)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-purple-800 flex items-center gap-2">
              <Percent className="h-4 w-4" />
              Средняя маржа
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-900">
              {data.summary.average_margin.toFixed(1)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Прибыли и убытки по месяцам</CardTitle>
          <CardDescription>Выручка, расходы и прибыль за последние 6 месяцев</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data.profit_loss}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
              <Bar dataKey="revenue" fill="#3b82f6" name="Выручка" />
              <Bar dataKey="expenses" fill="#f97316" name="Расходы" />
              <Bar dataKey="profit" fill="#10b981" name="Прибыль" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Detailed Table */}
      <Card>
        <CardHeader>
          <CardTitle>Детальная информация</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">Период</th>
                  <th className="text-right py-3 px-4">Выручка</th>
                  <th className="text-right py-3 px-4">Расходы</th>
                  <th className="text-right py-3 px-4">Прибыль</th>
                  <th className="text-right py-3 px-4">Маржа</th>
                </tr>
              </thead>
              <tbody>
                {data.profit_loss.map((item, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{item.period}</td>
                    <td className="text-right py-3 px-4">{formatCurrency(item.revenue)}</td>
                    <td className="text-right py-3 px-4">{formatCurrency(item.expenses)}</td>
                    <td className="text-right py-3 px-4 text-green-600 font-semibold">
                      {formatCurrency(item.profit)}
                    </td>
                    <td className="text-right py-3 px-4 text-purple-600 font-semibold">
                      {item.margin.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ProfitLoss;