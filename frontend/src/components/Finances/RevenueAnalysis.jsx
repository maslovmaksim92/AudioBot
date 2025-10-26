import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DollarSign } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function RevenueAnalysis() {
  const [data, setData] = useState(null);
  const [detailsData, setDetailsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState('ВАШ ДОМ ФАКТ');
  const [selectedMonth, setSelectedMonth] = useState('all');
  const [availableMonths, setAvailableMonths] = useState([]);

  useEffect(() => {
    fetchAvailableMonths();
  }, []);

  useEffect(() => {
    fetchRevenue();
    fetchRevenueDetails();
  }, [selectedCompany, selectedMonth]);

  const fetchAvailableMonths = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/finances/available-months`);
      setAvailableMonths(response.data.months || []);
    } catch (error) {
      console.error('Error fetching months:', error);
    }
  };

  const fetchRevenue = async () => {
    try {
      setLoading(true);
      const params = {
        company: selectedCompany
      };
      if (selectedMonth !== 'all') {
        params.month = selectedMonth;
      }
      const response = await axios.get(`${BACKEND_URL}/api/finances/revenue-analysis`, { params });
      setData(response.data);
    } catch (error) {
      console.error('Error fetching revenue:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRevenueDetails = async () => {
    try {
      setLoadingDetails(true);
      const params = {
        company: selectedCompany
      };
      if (selectedMonth !== 'all') {
        params.month = selectedMonth;
      }
      const response = await axios.get(`${BACKEND_URL}/api/finances/revenue-details`, { params });
      setDetailsData(response.data);
    } catch (error) {
      console.error('Error fetching revenue details:', error);
    } finally {
      setLoadingDetails(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0
    }).format(value);
  };

  if (loading) {
    return <div className="text-center p-8">Загрузка...</div>;
  }

  if (!data) {
    return <div className="text-center p-8">Нет данных</div>;
  }

  return (
    <div className="space-y-6">
      {/* Заголовок и фильтры */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center flex-wrap gap-4">
            <CardTitle>Анализ выручки</CardTitle>
            <div className="flex gap-2 flex-wrap">
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
              
              <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Выберите месяц" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все месяцы</SelectItem>
                  {availableMonths.map((month) => (
                    <SelectItem key={month} value={month}>
                      {month}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Общая выручка */}
      <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-green-800 flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            Общая выручка {selectedMonth !== 'all' && `- ${selectedMonth}`}
          </CardTitle>
          <CardDescription className="text-green-700">Доходы компании</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-green-900">
            {formatCurrency(data.total)}
          </div>
        </CardContent>
      </Card>

      {/* Детальные транзакции */}
      {detailsData && detailsData.transactions && detailsData.transactions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Детальные транзакции {selectedMonth !== 'all' && `- ${selectedMonth}`}</CardTitle>
            <CardDescription>
              Полная прозрачность для инвестора: все поступления с датами, контрагентами и назначениями платежей
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingDetails ? (
              <div className="text-center p-4">Загрузка...</div>
            ) : (
              <>
                {/* Mobile view - cards */}
                <div className="md:hidden space-y-3">
                  {detailsData.transactions.map((transaction, index) => (
                    <div key={transaction.id || index} className="border rounded-lg p-3 bg-gray-50">
                      <div className="flex justify-between items-start mb-2">
                        <div className="text-sm text-gray-600">{transaction.date}</div>
                        <div className="text-green-600 font-bold">{formatCurrency(transaction.amount)}</div>
                      </div>
                      <div className="font-medium mb-1">{transaction.counterparty}</div>
                      <div className="text-sm text-gray-600">{transaction.description || '—'}</div>
                    </div>
                  ))}
                  <div className="border-t-2 pt-3 bg-gray-100 rounded-lg p-3">
                    <div className="flex justify-between font-bold">
                      <span>ИТОГО ({detailsData.count})</span>
                      <span className="text-green-700">{formatCurrency(detailsData.total)}</span>
                    </div>
                  </div>
                </div>

                {/* Desktop view - table */}
                <div className="hidden md:block overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left p-3">Дата</th>
                        <th className="text-left p-3">Контрагент</th>
                        <th className="text-right p-3">Сумма</th>
                        <th className="text-left p-3">Назначение платежа</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detailsData.transactions.map((transaction, index) => (
                        <tr key={transaction.id || index} className="border-b hover:bg-gray-50">
                          <td className="p-3 whitespace-nowrap">{transaction.date}</td>
                          <td className="p-3 font-medium">{transaction.counterparty}</td>
                          <td className="text-right p-3 font-bold text-green-600 whitespace-nowrap">
                            {formatCurrency(transaction.amount)}
                          </td>
                          <td className="p-3 text-sm text-gray-600 max-w-md">
                            {transaction.description || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="border-t-2 font-bold bg-gray-100">
                        <td className="p-3">ИТОГО</td>
                        <td className="p-3 text-gray-600">
                          {detailsData.count} {detailsData.count === 1 ? 'транзакция' : detailsData.count < 5 ? 'транзакции' : 'транзакций'}
                        </td>
                        <td className="text-right p-3 text-green-700">
                          {formatCurrency(detailsData.total)}
                        </td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default RevenueAnalysis;
