import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { DollarSign, Save, Plus, Trash2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const MONTHS = [
  "Январь 2025",
  "Февраль 2025",
  "Март 2025",
  "Апрель 2025",
  "Май 2025",
  "Июнь 2025",
  "Июль 2025",
  "Август 2025",
  "Сентябрь 2025",
  "Октябрь 2025",
  "Ноябрь 2025",
  "Декабрь 2025"
];

const RevenueInput = () => {
  const [revenues, setRevenues] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [expandedMonths, setExpandedMonths] = useState(new Set(MONTHS.slice(0, 5)));

  useEffect(() => {
    loadRevenues();
  }, []);

  const loadRevenues = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/finances/revenue/monthly`);
      const data = await response.json();
      
      const revenueMap = {};
      data.revenues.forEach(item => {
        revenueMap[item.month] = {
          revenue: item.revenue,
          notes: item.notes || ''
        };
      });
      
      setRevenues(revenueMap);
    } catch (error) {
      console.error('Ошибка загрузки выручки:', error);
      setMessage({ type: 'error', text: 'Ошибка загрузки данных' });
    }
  };

  const handleRevenueChange = (month, value) => {
    setRevenues(prev => ({
      ...prev,
      [month]: {
        revenue: value,
        notes: prev[month]?.notes || ''
      }
    }));
  };

  const handleNotesChange = (month, value) => {
    setRevenues(prev => ({
      ...prev,
      [month]: {
        revenue: prev[month]?.revenue || 0,
        notes: value
      }
    }));
  };

  const saveRevenues = async () => {
    setLoading(true);
    try {
      const revenueList = Object.entries(revenues)
        .filter(([_, data]) => data.revenue && parseFloat(data.revenue) > 0)
        .map(([month, data]) => ({
          month,
          revenue: parseFloat(data.revenue),
          notes: data.notes
        }));

      if (revenueList.length === 0) {
        setMessage({ type: 'warning', text: 'Нет данных для сохранения' });
        setLoading(false);
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/finances/revenue/monthly`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ revenues: revenueList })
      });

      const result = await response.json();

      if (result.success) {
        // Синхронизируем с транзакциями
        const syncResponse = await fetch(`${BACKEND_URL}/api/finances/revenue/sync-to-transactions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        
        const syncResult = await syncResponse.json();
        
        setMessage({
          type: 'success',
          text: `Успешно сохранено! ${result.message}. ${syncResult.message}`
        });
        setTimeout(() => loadRevenues(), 1000);
      }
    } catch (error) {
      console.error('Ошибка сохранения:', error);
      setMessage({ type: 'error', text: 'Ошибка сохранения данных' });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (!value) return '';
    return new Intl.NumberFormat('ru-RU').format(value);
  };

  const parseCurrency = (value) => {
    return value.replace(/\s/g, '').replace(/,/g, '.');
  };

  const toggleMonth = (month) => {
    setExpandedMonths(prev => {
      const newSet = new Set(prev);
      if (newSet.has(month)) {
        newSet.delete(month);
      } else {
        newSet.add(month);
      }
      return newSet;
    });
  };

  const getTotalRevenue = () => {
    return Object.values(revenues).reduce((sum, data) => {
      return sum + (parseFloat(data.revenue) || 0);
    }, 0);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <DollarSign className="h-8 w-8 text-green-600" />
            Ввод выручки по месяцам
          </h1>
          <p className="text-gray-600 mt-2">Введите фактическую выручку для расчета прибылей и убытков</p>
        </div>
        <Button
          onClick={saveRevenues}
          disabled={loading}
          className="bg-green-600 hover:bg-green-700"
        >
          <Save className="h-4 w-4 mr-2" />
          {loading ? 'Сохранение...' : 'Сохранить'}
        </Button>
      </div>

      {message && (
        <Alert className={
          message.type === 'error' ? 'bg-red-50 border-red-200' :
          message.type === 'success' ? 'bg-green-50 border-green-200' :
          'bg-yellow-50 border-yellow-200'
        }>
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Сводка</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Всего месяцев с данными</p>
              <p className="text-2xl font-bold text-blue-700">
                {Object.keys(revenues).filter(m => revenues[m].revenue > 0).length}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Общая выручка</p>
              <p className="text-2xl font-bold text-green-700">
                {formatCurrency(getTotalRevenue())} ₽
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Средняя за месяц</p>
              <p className="text-2xl font-bold text-purple-700">
                {formatCurrency(getTotalRevenue() / Math.max(1, Object.keys(revenues).filter(m => revenues[m].revenue > 0).length))} ₽
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Выручка по месяцам</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {MONTHS.map((month) => (
            <div
              key={month}
              className={`border rounded-lg p-4 transition-all ${
                expandedMonths.has(month) ? 'bg-white' : 'bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <button
                  onClick={() => toggleMonth(month)}
                  className="flex-1 text-left"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-lg">{month}</span>
                    {revenues[month]?.revenue > 0 && (
                      <span className="text-green-600 font-semibold">
                        {formatCurrency(revenues[month].revenue)} ₽
                      </span>
                    )}
                  </div>
                </button>
              </div>

              {expandedMonths.has(month) && (
                <div className="mt-4 space-y-3">
                  <div>
                    <Label htmlFor={`revenue-${month}`}>Выручка (₽)</Label>
                    <Input
                      id={`revenue-${month}`}
                      type="text"
                      placeholder="0"
                      value={revenues[month]?.revenue ? formatCurrency(revenues[month].revenue) : ''}
                      onChange={(e) => handleRevenueChange(month, parseCurrency(e.target.value))}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label htmlFor={`notes-${month}`}>Примечания (опционально)</Label>
                    <Input
                      id={`notes-${month}`}
                      type="text"
                      placeholder="Комментарий..."
                      value={revenues[month]?.notes || ''}
                      onChange={(e) => handleNotesChange(month, e.target.value)}
                      className="mt-1"
                    />
                  </div>
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};

export default RevenueInput;
