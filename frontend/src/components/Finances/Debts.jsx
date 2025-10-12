import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, CheckCircle, Clock, CreditCard } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function Debts() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDebts();
  }, []);

  const fetchDebts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/finances/debts`);
      setData(response.data);
    } catch (error) {
      console.error('Error fetching debts:', error);
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

  const getStatusBadge = (status) => {
    if (status === 'active') {
      return <Badge className="bg-green-100 text-green-800 border-green-200">Активна</Badge>;
    } else if (status === 'overdue') {
      return <Badge className="bg-red-100 text-red-800 border-red-200">Просрочена</Badge>;
    }
    return <Badge>{status}</Badge>;
  };

  const getTypeLabel = (type) => {
    const types = {
      'loan': 'Кредит',
      'credit_line': 'Кредитная линия',
      'accounts_payable': 'Кредиторская задолженность',
      'lease': 'Лизинг'
    };
    return types[type] || type;
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-red-800 flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              Общая задолженность
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-900">
              {formatCurrency(data.summary.total)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-orange-800 flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Просроченная
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-900">
              {formatCurrency(data.summary.overdue)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-green-800 flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Активная
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900">
              {formatCurrency(data.summary.active)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-blue-800 flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Количество
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">
              {data.summary.count}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Debts List */}
      <Card>
        <CardHeader>
          <CardTitle>Список задолженностей</CardTitle>
          <CardDescription>Детальная информация по всем обязательствам</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.debts.map((debt) => (
              <Card 
                key={debt.id} 
                className={`${debt.status === 'overdue' ? 'border-red-200 bg-red-50' : 'border-gray-200'}`}
              >
                <CardContent className="pt-6">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-lg">{debt.creditor}</h3>
                        {getStatusBadge(debt.status)}
                      </div>
                      <div className="text-sm text-gray-600">
                        Тип: {getTypeLabel(debt.type)}
                      </div>
                      <div className="text-sm text-gray-600">
                        Срок погашения: {new Date(debt.due_date).toLocaleDateString('ru-RU')}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-red-600">
                        {formatCurrency(debt.amount)}
                      </div>
                      {debt.status === 'overdue' && (
                        <div className="text-sm text-red-600 mt-1 flex items-center justify-end gap-1">
                          <AlertCircle className="h-4 w-4" />
                          Требует внимания
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default Debts;