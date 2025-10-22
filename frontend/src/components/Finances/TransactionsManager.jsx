import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Plus, Edit, Trash2, TrendingUp, TrendingDown } from 'lucide-react';
import { getTransactions, addTransaction, updateTransaction, deleteTransaction } from '../../utils/financeStorage';

function TransactionsManager() {
  const [transactions, setTransactions] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    type: 'expense',
    category: '',
    amount: '',
    description: '',
    payment_method: 'cash',
    vat_rate: 5
  });

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = () => {
    const data = getTransactions();
    setTransactions(data.sort((a, b) => new Date(b.date) - new Date(a.date)));
  };

  const handleOpenDialog = (transaction = null) => {
    if (transaction) {
      setEditingTransaction(transaction);
      setFormData({
        date: transaction.date,
        type: transaction.type,
        category: transaction.category || '',
        amount: transaction.amount,
        description: transaction.description || '',
        payment_method: transaction.payment_method || 'cash'
      });
    } else {
      setEditingTransaction(null);
      setFormData({
        date: new Date().toISOString().split('T')[0],
        type: 'expense',
        category: '',
        amount: '',
        description: '',
        payment_method: 'cash'
      });
    }
    setShowDialog(true);
  };

  const handleSave = () => {
    const data = {
      ...formData,
      amount: parseFloat(formData.amount)
    };

    if (editingTransaction) {
      updateTransaction(editingTransaction.id, data);
    } else {
      addTransaction(data);
    }

    setShowDialog(false);
    loadTransactions();
  };

  const handleDelete = (id) => {
    if (window.confirm('Удалить транзакцию?')) {
      deleteTransaction(id);
      loadTransactions();
    }
  };

  const formatCurrency = (value) => new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(value);

  const totalIncome = transactions.filter(t => t.type === 'income').reduce((sum, t) => sum + parseFloat(t.amount), 0);
  const totalExpense = transactions.filter(t => t.type === 'expense').reduce((sum, t) => sum + parseFloat(t.amount), 0);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Транзакции</h2>
          <p className="text-gray-600">Управление доходами и расходами</p>
        </div>
        <Button onClick={() => handleOpenDialog()} className="bg-blue-600">
          <Plus className="h-4 w-4 mr-2" />Добавить транзакцию
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-green-50 border-green-200">
          <CardHeader><CardTitle className="text-sm flex items-center gap-2"><TrendingUp className="h-4 w-4 text-green-600" />Доходы</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-600">{formatCurrency(totalIncome)}</div></CardContent>
        </Card>
        <Card className="bg-red-50 border-red-200">
          <CardHeader><CardTitle className="text-sm flex items-center gap-2"><TrendingDown className="h-4 w-4 text-red-600" />Расходы</CardTitle></CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-600">{formatCurrency(totalExpense)}</div></CardContent>
        </Card>
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader><CardTitle className="text-sm">Баланс</CardTitle></CardHeader>
          <CardContent><div className={`text-2xl font-bold ${totalIncome - totalExpense >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>{formatCurrency(totalIncome - totalExpense)}</div></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Все транзакции ({transactions.length})</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {transactions.map(t => (
              <Card key={t.id} className={`border-l-4 ${t.type === 'income' ? 'border-green-500' : 'border-red-500'}`}>
                <CardContent className="pt-6 flex justify-between items-center">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{t.category || 'Без категории'}</h3>
                      <span className={`text-xs px-2 py-1 rounded ${t.type === 'income' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {t.type === 'income' ? 'Доход' : 'Расход'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{t.description}</p>
                    <p className="text-xs text-gray-500 mt-1">{new Date(t.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className={`text-2xl font-bold ${t.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                      {t.type === 'income' ? '+' : '-'}{formatCurrency(Math.abs(t.amount))}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleOpenDialog(t)}><Edit className="h-4 w-4" /></Button>
                      <Button variant="outline" size="sm" onClick={() => handleDelete(t.id)} className="text-red-600"><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {transactions.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg mb-2">Нет транзакций</p>
                <p className="text-sm">Добавьте первую транзакцию, чтобы начать учет</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-xl">
          <DialogHeader><DialogTitle>{editingTransaction ? 'Редактировать' : 'Добавить'} транзакцию</DialogTitle></DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Дата *</Label><Input type="date" value={formData.date} onChange={(e) => setFormData({...formData, date: e.target.value})} /></div>
              <div><Label>Тип *</Label>
                <Select value={formData.type} onValueChange={(v) => setFormData({...formData, type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="income">Доход</SelectItem>
                    <SelectItem value="expense">Расход</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div><Label>Категория *</Label><Input value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})} placeholder="Зарплата, Аренда, Материалы..." /></div>
            <div><Label>Сумма (₽) *</Label><Input type="number" value={formData.amount} onChange={(e) => setFormData({...formData, amount: e.target.value})} placeholder="0" /></div>
            <div><Label>Способ оплаты</Label>
              <Select value={formData.payment_method} onValueChange={(v) => setFormData({...formData, payment_method: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="cash">Наличные</SelectItem>
                  <SelectItem value="card">Карта</SelectItem>
                  <SelectItem value="bank_transfer">Банковский перевод</SelectItem>
                  <SelectItem value="other">Другое</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div><Label>Описание</Label><Textarea value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} placeholder="Дополнительная информация" rows={3} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>Отмена</Button>
            <Button onClick={handleSave} className="bg-blue-600" disabled={!formData.date || !formData.amount || !formData.category}>Сохранить</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default TransactionsManager;
