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
import { TrendingUp, DollarSign, PieChart, CreditCard, BarChart3, Plus, Upload, Activity, List, Calendar, LineChart, Download } from 'lucide-react';

function Finances() {
  const [activeTab, setActiveTab] = useState('overview');
  const [showAddForm, setShowAddForm] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleTransactionAdded = () => {
    setRefreshKey(prev => prev + 1);
  };

  const handleExport = async () => {
    try {
      const backendUrl = import.meta.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
      
      // Показываем индикатор загрузки
      const loadingDiv = document.createElement('div');
      loadingDiv.id = 'export-loading';
      loadingDiv.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.2); z-index: 9999; min-width: 300px; text-align: center;';
      loadingDiv.innerHTML = `
        <div style="margin-bottom: 15px;">
          <div class="spinner" style="border: 4px solid #f3f3f3; border-top: 4px solid #9B59B6; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto;"></div>
        </div>
        <p style="margin: 0; font-weight: bold; font-size: 16px;">Экспорт данных...</p>
        <p style="margin: 10px 0 0 0; font-size: 13px; color: #666;">Генерация прогнозов для всех моделей и сценариев</p>
        <p style="margin: 5px 0 0 0; font-size: 12px; color: #999;">Это может занять до 30 секунд</p>
        <style>
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        </style>
      `;
      document.body.appendChild(loadingDiv);
      
      // Увеличенный timeout для запроса
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 секунд
      
      // Вызываем новый endpoint для экспорта всех данных
      const response = await fetch(`${backendUrl}/api/finances/export-all`, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Получаем blob из ответа
      const blob = await response.blob();
      
      // Создаем ссылку для скачивания
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Получаем имя файла из заголовка Content-Disposition или используем дефолтное
      const contentDisposition = response.headers.get('Content-Disposition');
      let fileName = `financial_data_${new Date().toISOString().split('T')[0]}.xlsx`;
      if (contentDisposition) {
        const fileNameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (fileNameMatch && fileNameMatch.length === 2) {
          fileName = fileNameMatch[1];
        }
      }
      
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      
      // Очистка
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      document.body.removeChild(loadingDiv);
      
    } catch (error) {
      console.error('Ошибка экспорта:', error);
      const loadingDiv = document.getElementById('export-loading');
      if (loadingDiv) {
        document.body.removeChild(loadingDiv);
      }
      if (error.name === 'AbortError') {
        alert('Превышено время ожидания экспорта. Попробуйте еще раз.');
      } else {
        alert('Ошибка при экспорте данных. Попробуйте еще раз.');
      }
    }
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
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleExport} variant="outline" className="bg-purple-600 hover:bg-purple-700 text-white text-xs md:text-sm px-2 md:px-4">
              <Download className="h-4 w-4 md:mr-2" />
              <span className="hidden sm:inline">Экспорт</span>
            </Button>
            <Button onClick={() => window.location.href = '/finances/revenue'} variant="outline" className="bg-green-600 hover:bg-green-700 text-white text-xs md:text-sm px-2 md:px-4">
              <BarChart3 className="h-4 w-4 md:mr-2" />
              <span className="hidden sm:inline">Ввод выручки</span>
            </Button>
            <Button onClick={() => window.location.href = '/finances/articles'} variant="outline" className="bg-blue-600 hover:bg-blue-700 text-white text-xs md:text-sm px-2 md:px-4">
              <BarChart3 className="h-4 w-4 md:mr-2" />
              <span className="hidden sm:inline">Управление статьями</span>
            </Button>
            <Button onClick={() => setShowAddForm(true)} className="bg-green-600 hover:bg-green-700 text-xs md:text-sm px-2 md:px-4">
              <Plus className="h-4 w-4 md:mr-2" />
              <span className="hidden sm:inline">Добавить транзакцию</span>
            </Button>
            <Button variant="outline" className="text-xs md:text-sm px-2 md:px-4">
              <Upload className="h-4 w-4 md:mr-2" />
              <span className="hidden sm:inline">Импорт CSV</span>
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

          <TabsContent value="forecast" className="space-y-4">
            <ForecastView />
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