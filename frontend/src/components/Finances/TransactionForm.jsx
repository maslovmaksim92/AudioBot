import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { Plus, Upload } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function TransactionForm({ open, onOpenChange, onSuccess }) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState({ income: [], expense: [] });
  const [formData, setFormData] = useState({
    date: new Date().toISOString().slice(0, 16),
    amount: '',
    category: '',
    type: 'expense',
    description: '',
    payment_method: '',
    counterparty: '',
    project: ''
  });

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/finances/categories`);
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${BACKEND_URL}/api/finances/transactions`, {
        ...formData,
        amount: parseFloat(formData.amount),
        date: new Date(formData.date).toISOString()
      });

      toast({
        title: "Успешно",
        description: "Транзакция добавлена",
      });

      // Reset form
      setFormData({
        date: new Date().toISOString().slice(0, 16),
        amount: '',
        category: '',
        type: 'expense',
        description: '',
        payment_method: '',
        counterparty: '',
        project: ''
      });

      onSuccess && onSuccess();
      onOpenChange(false);
    } catch (error) {
      toast({
        title: "Ошибка",
        description: error.response?.data?.detail || "Не удалось добавить транзакцию",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const currentCategories = formData.type === 'income' ? categories.income : categories.expense;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Добавить транзакцию</DialogTitle>
          <DialogDescription>
            Введите данные о финансовой операции
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Тип транзакции */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Тип операции*</Label>
              <Select value={formData.type} onValueChange={(value) => setFormData({ ...formData, type: value, category: '' })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="income">Доход</SelectItem>
                  <SelectItem value="expense">Расход</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Дата и время*</Label>
              <Input
                type="datetime-local"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                required
              />
            </div>
          </div>

          {/* Сумма и категория */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Сумма (₽)*</Label>
              <Input
                type="number"
                step="0.01"
                placeholder="10000"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label>Категория*</Label>
              <Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value })}>
                <SelectTrigger>
                  <SelectValue placeholder="Выберите категорию" />
                </SelectTrigger>
                <SelectContent>
                  {currentCategories.map((cat) => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Контрагент и способ оплаты */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Контрагент (от кого/кому)</Label>
              <Input
                placeholder="ООО Компания"
                value={formData.counterparty}
                onChange={(e) => setFormData({ ...formData, counterparty: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label>Способ оплаты</Label>
              <Select value={formData.payment_method} onValueChange={(value) => setFormData({ ...formData, payment_method: value })}>
                <SelectTrigger>
                  <SelectValue placeholder="Выберите способ" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Наличные">Наличные</SelectItem>
                  <SelectItem value="Банковский перевод">Банковский перевод</SelectItem>
                  <SelectItem value="Карта">Карта</SelectItem>
                  <SelectItem value="Электронный кошелек">Электронный кошелек</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Проект */}
          <div className="space-y-2">
            <Label>Проект (опционально)</Label>
            <Input
              placeholder="Название проекта"
              value={formData.project}
              onChange={(e) => setFormData({ ...formData, project: e.target.value })}
            />
          </div>

          {/* Описание */}
          <div className="space-y-2">
            <Label>Описание</Label>
            <Textarea
              placeholder="Комментарий к транзакции"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Сохранение...' : 'Добавить'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default TransactionForm;
