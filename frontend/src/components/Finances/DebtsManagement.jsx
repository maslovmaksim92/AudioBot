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
const STORAGE_KEY = 'vasdom_debts';

function DebtsManagement() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingDebt, setEditingDebt] = useState(null);
  const [formData, setFormData] = useState({ creditor: '', amount: '', due_date: '', status: 'active', type: 'loan', description: '' });

  const calculateSummary = (debts) => {
    const total = debts.reduce((sum, d) => sum + d.amount, 0);
    const overdue = debts.filter(d => d.status === 'overdue').reduce((sum, d) => sum + d.amount, 0);
    const active = debts.filter(d => d.status === 'active').reduce((sum, d) => sum + d.amount, 0);
    return { total, overdue, active, count: debts.length };
  };

  useEffect(() => {
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
          <h2 className="text-2xl font-bold">Управление задолженностями</h2>
          <p className="text-xs text-orange-600">⚠️ Демо: данные в браузере</p>
        </div>
        <Button onClick={() => { setEditingDebt(null); setFormData({ creditor: '', amount: '', due_date: '', status: 'active', type: 'loan', description: '' }); setShowDialog(true); }} className="bg-blue-600">
          <Plus className="h-4 w-4 mr-2" />Добавить
        </Button>
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
                      <Button variant="outline" size="sm" onClick={() => { setEditingDebt(debt); setFormData({ creditor: debt.creditor, amount: debt.amount, due_date: debt.due_date, status: debt.status, type: debt.type, description: debt.description || '' }); setShowDialog(true); }}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleDelete(debt.id)} className="text-red-600">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editingDebt ? 'Редактировать' : 'Добавить'}</DialogTitle></DialogHeader>
          <div className="grid gap-4 py-4">
            <div><Label>Кредитор</Label><Input value={formData.creditor} onChange={(e) => setFormData({...formData, creditor: e.target.value})} /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Сумма</Label><Input type="number" value={formData.amount} onChange={(e) => setFormData({...formData, amount: e.target.value})} /></div>
              <div><Label>Срок</Label><Input type="date" value={formData.due_date} onChange={(e) => setFormData({...formData, due_date: e.target.value})} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Тип</Label><Select value={formData.type} onValueChange={(v) => setFormData({...formData, type: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="loan">Кредит</SelectItem><SelectItem value="credit_line">Кредитная линия</SelectItem><SelectItem value="accounts_payable">Задолженность</SelectItem><SelectItem value="lease">Лизинг</SelectItem></SelectContent></Select></div>
              <div><Label>Статус</Label><Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="active">Активна</SelectItem><SelectItem value="overdue">Просрочена</SelectItem><SelectItem value="paid">Оплачена</SelectItem></SelectContent></Select></div>
            </div>
            <div><Label>Описание</Label><Textarea value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} rows={2} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>Отмена</Button>
            <Button onClick={handleSave} className="bg-blue-600">Сохранить</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default DebtsManagement;
