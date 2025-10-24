import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { AlertCircle, CheckCircle, Clock, CreditCard, Plus, Edit, Trash2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function DebtsManagement() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDebts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/finances/debts`);
      setData(response.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDebts();
  }, []);

  const handleSave = () => {
    const payload = { ...formData, amount: parseFloat(formData.amount) };
    if (editingDebt) {
      const updatedDebts = data.debts.map(d => d.id === editingDebt.id ? { ...d, ...payload } : d);
      const newData = { debts: updatedDebts, summary: calculateSummary(updatedDebts) };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newData));
      setData(newData);
    } else {
      const newDebt = { id: `debt-${Date.now()}`, ...payload, created_at: new Date().toISOString() };
      const updatedDebts = [...data.debts, newDebt];
      const newData = { debts: updatedDebts, summary: calculateSummary(updatedDebts) };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newData));
      setData(newData);
    }
    setShowDialog(false);
    setEditingDebt(null);
  };

  const handleDelete = (debtId) => {
    if (!window.confirm('Удалить?')) return;
    const updatedDebts = data.debts.filter(d => d.id !== debtId);
    const newData = { debts: updatedDebts, summary: calculateSummary(updatedDebts) };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newData));
    setData(newData);
  };

  const formatCurrency = (value) => new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(value);

  if (loading) return <div className="text-center p-8">Загрузка...</div>;
  if (!data) return <div className="text-center p-8">Нет данных</div>;

  // Убедимся, что summary и debts существуют
  const summary = data.summary || { total: 0, overdue: 0, active: 0, count: 0 };
  const debts = data.debts || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Задолженности</h2>
          <p className="text-sm text-gray-600">Список активных задолженностей компании</p>
        </div>
      </div>
      
      <div className="grid grid-cols-4 gap-4">
        <Card><CardHeader><CardTitle className="text-sm">Общая</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{formatCurrency(summary.total)}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Просроченная</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-600">{formatCurrency(summary.overdue)}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Активная</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{formatCurrency(summary.active)}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Количество</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{summary.count}</div></CardContent></Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="space-y-3">
            {debts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                Нет данных. Добавьте задолженности.
              </div>
            ) : (
              debts.map((debt) => (
                <Card key={debt.id} className={debt.status === 'overdue' ? 'border-red-200 bg-red-50' : ''}>
                  <CardContent className="pt-6 flex justify-between">
                    <div>
                      <h3 className="font-semibold">{debt.creditor}</h3>
                      <div className="text-sm text-gray-600">{debt.due_date}</div>
                    </div>
                    <div className="flex gap-2 items-center">
                      <div className="text-xl font-bold">{formatCurrency(debt.amount)}</div>
                      <Badge variant={debt.status === 'overdue' ? 'destructive' : 'default'}>
                        {debt.status === 'active' ? 'Активна' : 'Просрочена'}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default DebtsManagement;
