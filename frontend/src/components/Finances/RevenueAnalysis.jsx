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
  const [selectedCompany, setSelectedCompany] = useState('ООО ВАШ ДОМ');
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
                  <SelectItem value="ООО ВАШ ДОМ">ООО ВАШ ДОМ</SelectItem>
                  <SelectItem value="УФИЦ">УФИЦ</SelectItem>
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

      {/* Детализация по категориям */}
      {data.revenue && data.revenue.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Детальная информация по выручке {selectedMonth !== 'all' && `- ${selectedMonth}`}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3">Категория</th>
                    <th className="text-right p-3">Сумма</th>
                    <th className="text-right p-3">% от общей</th>
                  </tr>
                </thead>
                <tbody>
                  {data.revenue.map((item, index) => (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{
                              backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]
                            }}
                          />
                          <span className="font-medium">{item.category}</span>
                        </div>
                      </td>
                      <td className="text-right p-3 font-bold text-green-600">
                        {formatCurrency(item.amount)}
                      </td>
                      <td className="text-right p-3 text-green-700">
                        {item.percentage.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 font-bold bg-gray-100">
                    <td className="p-3">ИТОГО</td>
                    <td className="text-right p-3 text-green-700">
                      {formatCurrency(data.total)}
                    </td>
                    <td className="text-right p-3">100%</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default RevenueAnalysis;
