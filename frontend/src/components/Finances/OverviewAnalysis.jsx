import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { calculateFinancialData, getDebts, getRevenue, getTransactions } from '../../utils/financeStorage';
import { TrendingUp, TrendingDown, DollarSign, CreditCard, Package, Calendar } from 'lucide-react';

function OverviewAnalysis() {
  const [data, setData] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = () => {
    const financialData = calculateFinancialData();
    setData(financialData);
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(value);
  };

  if (!data) return <div className="text-center p-8">Загрузка...</div>;

  // Расчет текущего месяца
  const currentMonth = new Date().toISOString().substring(0, 7);
  const currentMonthData = data.monthlyData[currentMonth] || { income: 0, expense: 0, net_profit: 0 };
  const currentProfit = currentMonthData.net_profit || (currentMonthData.income - currentMonthData.expense);

  // Итоги по всем месяцам
  const allMonths = Object.keys(data.monthlyData).sort().reverse();
  const totalIncome = data.totalIncome || 0;
  const totalExpense = data.totalExpense || 0;
  const totalProfit = data.totalProfit || 0;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Общий финансовый анализ</h2>
      
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

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-purple-800 flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              Задолженности
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-900">{formatCurrency(data.totalDebts)}</div>
            <p className="text-xs text-purple-700 mt-1">Активные + Просроченные</p>
          </CardContent>
        </Card>
      </div>

      {/* Текущий месяц */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Текущий месяц
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Доход</p>
              <p className="text-xl font-bold text-green-600">{formatCurrency(currentMonthData.income)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Расход</p>
              <p className="text-xl font-bold text-red-600">{formatCurrency(currentMonthData.expense)}</p>
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

      {/* История по месяцам */}
      <Card>
        <CardHeader>
          <CardTitle>История по месяцам</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {allMonths.map(monthKey => {
              const monthData = data.monthlyData[monthKey];
              const profit = monthData.income - monthData.expense;
              const [year, month] = monthKey.split('-');
              const monthName = new Date(year, month - 1).toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' });
              
              return (
                <Card key={monthKey} className="border-l-4 border-blue-500">
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="font-semibold capitalize">{monthName}</h3>
                        <div className="text-sm text-gray-600 mt-1">
                          Доход: {formatCurrency(monthData.income)} | Расход: {formatCurrency(monthData.expense)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-xl font-bold ${profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {profit >= 0 ? '+' : ''}{formatCurrency(profit)}
                        </div>
                        <div className="text-xs text-gray-600">
                          {profit >= 0 ? 'Профицит' : 'Дефицит'}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            
            {allMonths.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                Нет данных. Добавьте транзакции или выручку для расчета.
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Активы */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Товарные запасы
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(data.totalInventoryValue)}</div>
            <p className="text-sm text-gray-600 mt-1">{data.inventory.length} позиций</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Задолженности
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div>
                <p className="text-sm text-gray-600">Активные</p>
                <p className="text-lg font-bold">{formatCurrency(data.totalDebts - data.overdueDebts)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Просроченные</p>
                <p className="text-lg font-bold text-red-600">{formatCurrency(data.overdueDebts)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Последние транзакции */}
      <Card>
        <CardHeader>
          <CardTitle>Последние транзакции</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {data.transactions.slice(-10).reverse().map(t => (
              <div key={t.id} className="flex justify-between items-center py-2 border-b">
                <div>
                  <p className="font-medium">{t.description || t.category}</p>
                  <p className="text-xs text-gray-600">{new Date(t.date).toLocaleDateString('ru-RU')}</p>
                </div>
                <div className={`font-bold ${t.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                  {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
                </div>
              </div>
            ))}
            
            {data.transactions.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                Нет транзакций. Добавьте первую транзакцию.
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default OverviewAnalysis;
