import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Plus, Edit, Trash2, Package } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function InventoryManagement() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    quantity: '',
    unit: 'шт',
    cost: '',
    location: ''
  });

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/finances/inventory`);
      setData(response.data);
    } catch (error) {
      console.error('Error fetching inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setFormData({
        name: item.name,
        category: item.category,
        quantity: item.quantity,
        unit: item.unit,
        cost: item.cost,
        location: item.location || ''
      });
    } else {
      setEditingItem(null);
      setFormData({
        name: '',
        category: '',
        quantity: '',
        unit: 'шт',
        cost: '',
        location: ''
      });
    }
    setShowDialog(true);
  };

  const handleSave = async () => {
    try {
      const payload = {
        ...formData,
        quantity: parseInt(formData.quantity),
        cost: parseFloat(formData.cost)
      };

      if (editingItem) {
        await axios.put(`${BACKEND_URL}/api/finances/inventory/${editingItem.id}`, payload);
      } else {
        await axios.post(`${BACKEND_URL}/api/finances/inventory`, payload);
      }

      setShowDialog(false);
      fetchInventory();
    } catch (error) {
      console.error('Error saving inventory item:', error);
      alert('Ошибка при сохранении: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (itemId) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту позицию?')) {
      return;
    }

    try {
      await axios.delete(`${BACKEND_URL}/api/finances/inventory/${itemId}`);
      fetchInventory();
    } catch (error) {
      console.error('Error deleting inventory item:', error);
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

  if (loading) return <div className="text-center p-8">Загрузка...</div>;
  if (!data) return <div className="text-center p-8">Нет данных</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Управление товарными запасами</h2>
          <p className="text-gray-600">Отслеживайте все запасы и материалы</p>
        </div>
        <Button onClick={() => handleOpenDialog()} className="bg-blue-600 hover:bg-blue-700">
          <Plus className="h-4 w-4 mr-2" />
          Добавить позицию
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Общая стоимость</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(data.summary.total_value)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Всего позиций</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.summary.total_items}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Категорий</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.summary.categories}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Список запасов</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.inventory.map((item) => (
              <Card key={item.id} className="border-gray-200">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{item.name}</h3>
                        <Badge variant="outline">{item.category}</Badge>
                      </div>
                      <div className="text-sm text-gray-600">
                        Количество: {item.quantity} {item.unit} • Цена: {formatCurrency(item.cost)}
                      </div>
                      {item.location && (
                        <div className="text-sm text-gray-600">Местоположение: {item.location}</div>
                      )}
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-xl font-bold">{formatCurrency(item.value)}</div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => handleOpenDialog(item)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleDelete(item.id)}
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

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Редактировать' : 'Добавить'} позицию</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Название *</Label>
              <Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} />
            </div>
            <div className="grid gap-2">
              <Label>Категория *</Label>
              <Input value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>Количество *</Label>
                <Input type="number" value={formData.quantity} onChange={(e) => setFormData({...formData, quantity: e.target.value})} />
              </div>
              <div className="grid gap-2">
                <Label>Единица *</Label>
                <Input value={formData.unit} onChange={(e) => setFormData({...formData, unit: e.target.value})} />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>Цена (₽) *</Label>
              <Input type="number" value={formData.cost} onChange={(e) => setFormData({...formData, cost: e.target.value})} />
            </div>
            <div className="grid gap-2">
              <Label>Местоположение</Label>
              <Input value={formData.location} onChange={(e) => setFormData({...formData, location: e.target.value})} />
            </div>
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

export default InventoryManagement;
