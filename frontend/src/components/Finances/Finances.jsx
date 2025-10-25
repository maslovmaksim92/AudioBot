import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import OverviewAnalysis from './OverviewAnalysis';
import TransactionsManager from './TransactionsManager';
import CashFlow from './CashFlow';
import ProfitLoss from './ProfitLoss';
import BalanceSheet from './BalanceSheet';
import ExpenseAnalysis from './ExpenseAnalysis';
import RevenueAnalysis from './RevenueAnalysis';
import DebtsManagement from './DebtsManagement';
import PaymentCalendar from './PaymentCalendar';
import TransactionForm from './TransactionForm';
import ForecastView from './ForecastView';
import { TrendingUp, DollarSign, PieChart, CreditCard, BarChart3, Plus, Upload, Activity, List, Calendar, LineChart } from 'lucide-react';

function Finances() {
  const [activeTab, setActiveTab] = useState('overview');
  const [showAddForm, setShowAddForm] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleTransactionAdded = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-6">
      <div className="max-w-7xl mx-auto space-y-4 md:space-y-6 px-2 md:px-0">
        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 md:gap-4">
          <div className="space-y-1 md:space-y-2">
            <h1 className="text-2xl md:text-4xl font-bold text-gray-900">
              Финансовый анализ
            </h1>
            <p className="text-sm md:text-lg text-gray-600">
              Минимизируйте ручную работу с отчетами и получайте данные о финансовом состоянии компании в один клик
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => window.location.href = '/finances/revenue'} variant="outline" className="bg-green-600 hover:bg-green-700 text-white">
              <BarChart3 className="h-4 w-4 mr-2" />
              Ввод выручки
            </Button>
            <Button onClick={() => window.location.href = '/finances/articles'} variant="outline" className="bg-blue-600 hover:bg-blue-700 text-white">
              <BarChart3 className="h-4 w-4 mr-2" />
              Управление статьями
            </Button>
            <Button onClick={() => setShowAddForm(true)} className="bg-green-600 hover:bg-green-700">
              <Plus className="h-4 w-4 mr-2" />
              Добавить транзакцию
            </Button>
            <Button variant="outline">
              <Upload className="h-4 w-4 mr-2" />
              Импорт CSV
            </Button>
          </div>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4 md:space-y-6">
          <TabsList className="flex w-full overflow-x-auto gap-1 md:gap-2 bg-white p-1 md:p-2 rounded-xl shadow-sm scrollbar-hide">
            <TabsTrigger 
              value="overview" 
              className="flex items-center gap-1 md:gap-2 text-xs md:text-sm data-[state=active]:bg-indigo-600 data-[state=active]:text-white px-2 md:px-3 whitespace-nowrap flex-shrink-0"
            >
              <Activity className="h-3 w-3 md:h-4 md:w-4" />
              <span className="inline">Анализ</span>
            </TabsTrigger>
            <TabsTrigger 
              value="revenue"
              className="flex items-center gap-1 md:gap-2 text-xs md:text-sm data-[state=active]:bg-green-600 data-[state=active]:text-white px-2 md:px-3 whitespace-nowrap flex-shrink-0"
            >
              <DollarSign className="h-3 w-3 md:h-4 md:w-4" />
              <span className="inline">Выручка</span>
            </TabsTrigger>
            <TabsTrigger 
              value="expenses"
              className="flex items-center gap-1 md:gap-2 text-xs md:text-sm data-[state=active]:bg-orange-600 data-[state=active]:text-white px-2 md:px-3 whitespace-nowrap flex-shrink-0"
            >
              <PieChart className="h-3 w-3 md:h-4 md:w-4" />
              <span className="inline">Расходы</span>
            </TabsTrigger>
            <TabsTrigger 
              value="debts"
              className="flex items-center gap-1 md:gap-2 text-xs md:text-sm data-[state=active]:bg-red-600 data-[state=active]:text-white px-2 md:px-3 whitespace-nowrap flex-shrink-0"
            >
              <CreditCard className="h-3 w-3 md:h-4 md:w-4" />
              <span className="inline">Долги</span>
            </TabsTrigger>
            <TabsTrigger 
              value="payment-calendar"
              className="flex items-center gap-1 md:gap-2 text-xs md:text-sm data-[state=active]:bg-cyan-600 data-[state=active]:text-white px-2 md:px-3 whitespace-nowrap flex-shrink-0"
            >
              <Calendar className="h-3 w-3 md:h-4 md:w-4" />
              <span className="inline">Календарь</span>
            </TabsTrigger>
            <TabsTrigger 
              value="forecast"
              className="flex items-center gap-1 md:gap-2 text-xs md:text-sm data-[state=active]:bg-purple-600 data-[state=active]:text-white px-2 md:px-3 whitespace-nowrap flex-shrink-0"
            >
              <LineChart className="h-3 w-3 md:h-4 md:w-4" />
              <span className="inline">Прогноз 26-30</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <OverviewAnalysis />
          </TabsContent>

          <TabsContent value="revenue" className="space-y-4">
            <RevenueAnalysis />
          </TabsContent>

          <TabsContent value="expenses" className="space-y-4">
            <ExpenseAnalysis />
          </TabsContent>

          <TabsContent value="debts" className="space-y-4">
            <DebtsManagement />
          </TabsContent>

          <TabsContent value="payment-calendar" className="space-y-4">
            <PaymentCalendar />
          </TabsContent>
        </Tabs>

        {/* Transaction Form Modal */}
        <TransactionForm 
          open={showAddForm} 
          onOpenChange={setShowAddForm}
          onSuccess={handleTransactionAdded}
        />
      </div>
    </div>
  );
}

export default Finances;