import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Building, CreditCard, TrendingUp } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

function BalanceSheet() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBalanceSheet();
  }, []);

  const fetchBalanceSheet = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/finances/balance-sheet`);
      setData(response.data);
    } catch (error) {
      console.error('Error fetching balance sheet:', error);
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

  const pieData = [
    { name: 'Активы', value: data.assets.total },
    { name: 'Обязательства', value: data.liabilities.total },
    { name: 'Капитал', value: data.equity.total }
  ];

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-blue-800 flex items-center gap-2">
              <Building className="h-4 w-4" />
              Активы
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">
              {formatCurrency(data.assets.total)}
            </div>
            <div className="mt-2 space-y-1 text-xs text-blue-700">
              <div>Текущие: {formatCurrency(data.assets.current.total)}</div>
              <div>Долгосрочные: {formatCurrency(data.assets.non_current.total)}</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-red-800 flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              Обязательства
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-900">
              {formatCurrency(data.liabilities.total)}
            </div>
            <div className="mt-2 space-y-1 text-xs text-red-700">
              <div>Краткосрочные: {formatCurrency(data.liabilities.current.total)}</div>
              <div>Долгосрочные: {formatCurrency(data.liabilities.non_current.total)}</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-green-800 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Капитал
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900">
              {formatCurrency(data.equity.total)}
            </div>
            <div className="mt-2 space-y-1 text-xs text-green-700">
              <div>Уставный капитал: {formatCurrency(data.equity.capital)}</div>
              <div>Нераспределённая прибыль: {formatCurrency(data.equity.retained_earnings)}</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Структура баланса</CardTitle>
            <CardDescription>Распределение активов, обязательств и капитала</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(value)} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Assets Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Детализация активов</CardTitle>
            <CardDescription>Структура активов компании</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-sm mb-2 text-blue-900">Текущие активы</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Денежные средства</span>
                    <span className="font-medium">{formatCurrency(data.assets.current.cash)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Дебиторская задолженность</span>
                    <span className="font-medium">{formatCurrency(data.assets.current.accounts_receivable)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Запасы</span>
                    <span className="font-medium">{formatCurrency(data.assets.current.inventory)}</span>
                  </div>
                </div>
              </div>
              <div className="border-t pt-4">
                <h4 className="font-semibold text-sm mb-2 text-blue-900">Долгосрочные активы</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Недвижимость</span>
                    <span className="font-medium">{formatCurrency(data.assets.non_current.property)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Оборудование</span>
                    <span className="font-medium">{formatCurrency(data.assets.non_current.equipment)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Транспорт</span>
                    <span className="font-medium">{formatCurrency(data.assets.non_current.vehicles)}</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default BalanceSheet;