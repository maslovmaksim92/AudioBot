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
import DebtsManagement from './DebtsManagement';
import InventoryManagement from './InventoryManagement';
import PaymentCalendar from './PaymentCalendar';
import BudgetPlanFact from './BudgetPlanFact';
import TransactionForm from './TransactionForm';
import { TrendingUp, DollarSign, PieChart, CreditCard, Package, BarChart3, Plus, Upload, Activity, List, Calendar, Target } from 'lucide-react';

function Finances() {
  const [activeTab, setActiveTab] = useState('overview');
  const [showAddForm, setShowAddForm] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleTransactionAdded = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold text-gray-900">
              Финансовый анализ
            </h1>
            <p className="text-lg text-gray-600">
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
          <TabsList className="grid w-full grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-10 gap-1 md:gap-2 bg-white p-1 md:p-2 rounded-xl shadow-sm overflow-x-auto">
            <TabsTrigger 
              value="overview" 
              className="flex items-center gap-2 data-[state=active]:bg-indigo-600 data-[state=active]:text-white"
            >
              <Activity className="h-4 w-4" />
              <span className="hidden md:inline">Анализ</span>
            </TabsTrigger>
            <TabsTrigger 
              value="transactions" 
              className="flex items-center gap-2 data-[state=active]:bg-indigo-600 data-[state=active]:text-white"
            >
              <List className="h-4 w-4" />
              <span className="hidden md:inline">Транзакции</span>
            </TabsTrigger>
            <TabsTrigger 
              value="cash-flow" 
              className="flex items-center gap-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <TrendingUp className="h-4 w-4" />
              <span className="hidden md:inline">Движение</span>
            </TabsTrigger>
            <TabsTrigger 
              value="profit-loss"
              className="flex items-center gap-2 data-[state=active]:bg-green-600 data-[state=active]:text-white"
            >
              <DollarSign className="h-4 w-4" />
              <span className="hidden md:inline">П&У</span>
            </TabsTrigger>
            <TabsTrigger 
              value="balance"
              className="flex items-center gap-2 data-[state=active]:bg-purple-600 data-[state=active]:text-white"
            >
              <BarChart3 className="h-4 w-4" />
              <span className="hidden md:inline">Баланс</span>
            </TabsTrigger>
            <TabsTrigger 
              value="expenses"
              className="flex items-center gap-2 data-[state=active]:bg-orange-600 data-[state=active]:text-white"
            >
              <PieChart className="h-4 w-4" />
              <span className="hidden md:inline">Расходы</span>
            </TabsTrigger>
            <TabsTrigger 
              value="debts"
              className="flex items-center gap-2 data-[state=active]:bg-red-600 data-[state=active]:text-white"
            >
              <CreditCard className="h-4 w-4" />
              <span className="hidden md:inline">Долги</span>
            </TabsTrigger>
            <TabsTrigger 
              value="inventory"
              className="flex items-center gap-2 data-[state=active]:bg-teal-600 data-[state=active]:text-white"
            >
              <Package className="h-4 w-4" />
              <span className="hidden md:inline">Запасы</span>
            </TabsTrigger>
            <TabsTrigger 
              value="payment-calendar"
              className="flex items-center gap-2 data-[state=active]:bg-cyan-600 data-[state=active]:text-white"
            >
              <Calendar className="h-4 w-4" />
              <span className="hidden md:inline">Календарь</span>
            </TabsTrigger>
            <TabsTrigger 
              value="budget-plan-fact"
              className="flex items-center gap-2 data-[state=active]:bg-pink-600 data-[state=active]:text-white"
            >
              <Target className="h-4 w-4" />
              <span className="hidden md:inline">Бюджеты</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <OverviewAnalysis />
          </TabsContent>

          <TabsContent value="transactions" className="space-y-4">
            <TransactionsManager />
          </TabsContent>

          <TabsContent value="cash-flow" className="space-y-4">
            <CashFlow />
          </TabsContent>

          <TabsContent value="profit-loss" className="space-y-4">
            <ProfitLoss />
          </TabsContent>

          <TabsContent value="balance" className="space-y-4">
            <BalanceSheet />
          </TabsContent>

          <TabsContent value="expenses" className="space-y-4">
            <ExpenseAnalysis />
          </TabsContent>

          <TabsContent value="debts" className="space-y-4">
            <DebtsManagement />
          </TabsContent>

          <TabsContent value="inventory" className="space-y-4">
            <InventoryManagement />
          </TabsContent>

          <TabsContent value="payment-calendar" className="space-y-4">
            <PaymentCalendar />
          </TabsContent>

          <TabsContent value="budget-plan-fact" className="space-y-4">
            <BudgetPlanFact />
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