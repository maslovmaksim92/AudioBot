import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Calendar, Plus, Edit, Trash2, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { getPaymentCalendar, addPaymentEvent, updatePaymentEvent, deletePaymentEvent } from '../../utils/financeStorage';

function PaymentCalendar() {
  const [payments, setPayments] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [editingPayment, setEditingPayment] = useState(null);
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    type: 'expense',
    counterparty: '',
    amount: '',
    description: '',
    status: 'planned'
  });

  useEffect(() => {
    loadPayments();
  }, []);

  const loadPayments = () => {
    const data = getPaymentCalendar();
    setPayments(data.sort((a, b) => new Date(a.date) - new Date(b.date)));
  };

  const handleOpenDialog = (payment = null) => {
    if (payment) {
      setEditingPayment(payment);
      setFormData({
        date: payment.date,
        type: payment.type,
        counterparty: payment.counterparty,
        amount: payment.amount,
        description: payment.description || '',
        status: payment.status
      });
    } else {
      setEditingPayment(null);
      setFormData({
        date: new Date().toISOString().split('T')[0],
        type: 'expense',
        counterparty: '',
        amount: '',
        description: '',
        status: 'planned'
      });
    }
    setShowDialog(true);
  };

  const handleSave = () => {
    const data = { ...formData, amount: parseFloat(formData.amount) };
    
    if (editingPayment) {
      updatePaymentEvent(editingPayment.id, data);
    } else {
      addPaymentEvent(data);
    }
    
    setShowDialog(false);
    loadPayments();
  };

  const handleDelete = (id) => {
    if (window.confirm('Удалить платеж?')) {
      deletePaymentEvent(id);
      loadPayments();
    }
  };

  const handleStatusChange = (id, newStatus) => {
    updatePaymentEvent(id, { status: newStatus });
    loadPayments();
  };

  const formatCurrency = (value) => new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(value);

  const today = new Date().toISOString().split('T')[0];
  const upcomingPayments = payments.filter(p => p.date >= today && p.status === 'planned');
  const overduePayments = payments.filter(p => p.date < today && p.status === 'planned');
  const paidPayments = payments.filter(p => p.status === 'paid');

  const totalPlanned = upcomingPayments.reduce((sum, p) => sum + parseFloat(p.amount), 0);
  const totalOverdue = overduePayments.reduce((sum, p) => sum + parseFloat(p.amount), 0);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Платежный календарь</h2>
          <p className="text-gray-600">Управление предстоящими платежами</p>
        </div>
        <Button onClick={() => handleOpenDialog()} className="bg-blue-600">
          <Plus className="h-4 w-4 mr-2" />Добавить платеж
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader><CardTitle className="text-sm flex items-center gap-2"><Clock className="h-4 w-4 text-blue-600" />Предстоящие</CardTitle></CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{formatCurrency(totalPlanned)}</div>
            <p className="text-xs text-gray-600 mt-1">{upcomingPayments.length} платежей</p>
          </CardContent>
        </Card>
        <Card className="bg-red-50 border-red-200">
          <CardHeader><CardTitle className="text-sm flex items-center gap-2"><AlertCircle className="h-4 w-4 text-red-600" />Просрочено</CardTitle></CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{formatCurrency(totalOverdue)}</div>
            <p className="text-xs text-gray-600 mt-1">{overduePayments.length} платежей</p>
          </CardContent>
        </Card>
        <Card className="bg-green-50 border-green-200">
          <CardHeader><CardTitle className="text-sm flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-600" />Оплачено</CardTitle></CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{paidPayments.length}</div>
            <p className="text-xs text-gray-600 mt-1">за все время</p>
          </CardContent>
        </Card>
      </div>

      {overduePayments.length > 0 && (
        <Card className="border-red-300 bg-red-50">
          <CardHeader><CardTitle className="text-red-800">Просроченные платежи</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {overduePayments.map(p => (
                <Card key={p.id} className="border-red-200">
                  <CardContent className="pt-6 flex justify-between items-center">
                    <div className="flex-1">
                      <h3 className="font-semibold text-red-800">{p.counterparty}</h3>
                      <p className="text-sm text-gray-600">{p.description}</p>
                      <p className="text-xs text-red-600 mt-1">Срок: {new Date(p.date).toLocaleDateString('ru-RU')}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-xl font-bold text-red-600">{formatCurrency(p.amount)}</div>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={() => handleStatusChange(p.id, 'paid')} className="bg-green-600">Оплатить</Button>
                        <Button variant="outline" size="sm" onClick={() => handleOpenDialog(p)}><Edit className="h-4 w-4" /></Button>
                        <Button variant="outline" size="sm" onClick={() => handleDelete(p.id)} className="text-red-600"><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Предстоящие платежи</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {upcomingPayments.map(p => (
              <Card key={p.id} className="border-blue-200">
                <CardContent className="pt-6 flex justify-between items-center">
                  <div className="flex-1">
                    <h3 className="font-semibold">{p.counterparty}</h3>
                    <p className="text-sm text-gray-600">{p.description}</p>
                    <p className="text-xs text-gray-500 mt-1">{new Date(p.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-xl font-bold">{formatCurrency(p.amount)}</div>
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => handleStatusChange(p.id, 'paid')} className="bg-green-600">Оплатить</Button>
                      <Button variant="outline" size="sm" onClick={() => handleOpenDialog(p)}><Edit className="h-4 w-4" /></Button>
                      <Button variant="outline" size="sm" onClick={() => handleDelete(p.id)} className="text-red-600"><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {upcomingPayments.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-lg mb-2">Нет предстоящих платежей</p>
                <p className="text-sm">Добавьте платежи для планирования</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editingPayment ? 'Редактировать' : 'Добавить'} платеж</DialogTitle></DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Дата платежа *</Label><Input type="date" value={formData.date} onChange={(e) => setFormData({...formData, date: e.target.value})} /></div>
              <div><Label>Тип *</Label>
                <Select value={formData.type} onValueChange={(v) => setFormData({...formData, type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="income">Поступление</SelectItem>
                    <SelectItem value="expense">Платеж</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div><Label>Контрагент *</Label><Input value={formData.counterparty} onChange={(e) => setFormData({...formData, counterparty: e.target.value})} placeholder="Название организации или ФИО" /></div>
            <div><Label>Сумма (₽) *</Label><Input type="number" value={formData.amount} onChange={(e) => setFormData({...formData, amount: e.target.value})} placeholder="0" /></div>
            <div><Label>Описание</Label><Textarea value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} placeholder="Назначение платежа" rows={2} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>Отмена</Button>
            <Button onClick={handleSave} className="bg-blue-600" disabled={!formData.date || !formData.amount || !formData.counterparty}>Сохранить</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default PaymentCalendar;
