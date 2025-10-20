import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { AlertCircle, CheckCircle, Clock, CreditCard, Plus, Edit, Trash2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function DebtsManagement() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingDebt, setEditingDebt] = useState(null);
  const [formData, setFormData] = useState({
    creditor: '',
    amount: '',
    due_date: '',
    status: 'active',
    type: 'loan',
    description: ''
  });

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

  const handleOpenDialog = (debt = null) => {
    if (debt) {
      setEditingDebt(debt);
      setFormData({
        creditor: debt.creditor,
        amount: debt.amount,
        due_date: debt.due_date,
        status: debt.status,
        type: debt.type,
        description: debt.description || ''
      });
    } else {
      setEditingDebt(null);
      setFormData({
        creditor: '',
        amount: '',
        due_date: '',
        status: 'active',
        type: 'loan',
        description: ''
      });
    }
    setShowDialog(true);
  };

  const handleCloseDialog = () => {
    setShowDialog(false);
    setEditingDebt(null);
  };

  const handleSave = async () => {
    try {
      const payload = {
        ...formData,
        amount: parseFloat(formData.amount)
      };

      if (editingDebt) {
        await axios.put(`${BACKEND_URL}/api/finances/debts/${editingDebt.id}`, payload);
      } else {
        await axios.post(`${BACKEND_URL}/api/finances/debts`, payload);
      }

      handleCloseDialog();
      fetchDebts();
    } catch (error) {
      console.error('Error saving debt:', error);
      alert('Ошибка при сохранении: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (debtId) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту задолженность?')) {
      return;
    }

    try {
      await axios.delete(`${BACKEND_URL}/api/finances/debts/${debtId}`);
      fetchDebts();
    } catch (error) {
      console.error('Error deleting debt:', error);
      alert('Ошибка при удалении: ' + (error.response?.data?.detail || error.message));
    }
  };

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
    } else if (status === 'paid') {
      return <Badge className="bg-blue-100 text-blue-800 border-blue-200">Оплачена</Badge>;
    }
    return <Badge>{status}</Badge>;
  };

  const getTypeLabel = (type) => {
    const types = {
      'loan': 'Кредит',
      'credit_line': 'Кредитная линия',
      'accounts_payable': 'Кредиторская задолженность',
      'lease': 'Лизинг',
      'other': 'Другое'
    };
    return types[type] || type;
  };

  if (loading) {
    return <div className="text-center p-8">Загрузка...</div>;
  }

  if (!data) {
    return <div className="text-center p-8">Нет данных</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Управление задолженностями</h2>
          <p className="text-gray-600">Добавляйте, редактируйте и отслеживайте все обязательства</p>
        </div>
        <Button onClick={() => handleOpenDialog()} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="h-4 w-4 mr-2" />
          Добавить задолженность
        </Button>
      </div>

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
                      {debt.description && (
                        <div className="text-sm text-gray-600">
                          {debt.description}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-4">
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
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleOpenDialog(debt)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(debt.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Edit/Create Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingDebt ? 'Редактировать задолженность' : 'Добавить задолженность'}
            </DialogTitle>
            <DialogDescription>
              Заполните информацию о задолженности
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="creditor">Кредитор *</Label>
              <Input
                id="creditor"
                value={formData.creditor}
                onChange={(e) => setFormData({ ...formData, creditor: e.target.value })}
                placeholder="Название организации или лица"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="amount">Сумма (₽) *</Label>
                <Input
                  id="amount"
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  placeholder="0"
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="due_date">Срок погашения *</Label>
                <Input
                  id="due_date"
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="type">Тип *</Label>
                <Select value={formData.type} onValueChange={(value) => setFormData({ ...formData, type: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="loan">Кредит</SelectItem>
                    <SelectItem value="credit_line">Кредитная линия</SelectItem>
                    <SelectItem value="accounts_payable">Кредиторская задолженность</SelectItem>
                    <SelectItem value="lease">Лизинг</SelectItem>
                    <SelectItem value="other">Другое</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="status">Статус *</Label>
                <Select value={formData.status} onValueChange={(value) => setFormData({ ...formData, status: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Активна</SelectItem>
                    <SelectItem value="overdue">Просрочена</SelectItem>
                    <SelectItem value="paid">Оплачена</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Описание</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Дополнительная информация о задолженности"
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCloseDialog}>
              Отмена
            </Button>
            <Button onClick={handleSave} className="bg-blue-600 hover:bg-blue-700">
              {editingDebt ? 'Сохранить' : 'Добавить'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default DebtsManagement;
