import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Edit, Trash2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const STORAGE_KEY = 'vasdom_inventory';

function InventoryManagement() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({ name: '', category: '', quantity: '', unit: 'шт', cost: '', location: '' });

  const calculateSummary = (items) => {
    const total_value = items.reduce((sum, i) => sum + i.value, 0);
    const total_items = items.reduce((sum, i) => sum + i.quantity, 0);
    const categories = new Set(items.map(i => i.category)).size;
    return { total_value, total_items, categories };
  };

  useEffect(() => {
    const fetchInventory = async () => {
      try {
        setLoading(true);
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          setData(JSON.parse(stored));
        } else {
          const response = await axios.get(`${BACKEND_URL}/api/finances/inventory`);
          localStorage.setItem(STORAGE_KEY, JSON.stringify(response.data));
          setData(response.data);
        }
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchInventory();
  }, []);

  const handleSave = () => {
    const quantity = parseInt(formData.quantity);
    const cost = parseFloat(formData.cost);
    const value = quantity * cost;
    const payload = { ...formData, quantity, cost, value };
    
    if (editingItem) {
      const updatedItems = data.inventory.map(i => i.id === editingItem.id ? { ...i, ...payload } : i);
      const newData = { inventory: updatedItems, summary: calculateSummary(updatedItems) };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newData));
      setData(newData);
    } else {
      const newItem = { id: `inv-${Date.now()}`, ...payload, created_at: new Date().toISOString() };
      const updatedItems = [...data.inventory, newItem];
      const newData = { inventory: updatedItems, summary: calculateSummary(updatedItems) };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newData));
      setData(newData);
    }
    setShowDialog(false);
    setEditingItem(null);
  };

  const handleDelete = (itemId) => {
    if (!window.confirm('Удалить?')) return;
    const updatedItems = data.inventory.filter(i => i.id !== itemId);
    const newData = { inventory: updatedItems, summary: calculateSummary(updatedItems) };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newData));
    setData(newData);
  };

  const formatCurrency = (value) => new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(value);

  if (loading) return <div className="text-center p-8">Загрузка...</div>;
  if (!data) return <div className="text-center p-8">Нет данных</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Управление запасами</h2>
          <p className="text-xs text-orange-600">⚠️ Демо: данные в браузере</p>
        </div>
        <Button onClick={() => { setEditingItem(null); setFormData({ name: '', category: '', quantity: '', unit: 'шт', cost: '', location: '' }); setShowDialog(true); }} className="bg-blue-600">
          <Plus className="h-4 w-4 mr-2" />Добавить
        </Button>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        <Card><CardHeader><CardTitle className="text-sm">Общая стоимость</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{formatCurrency(data.summary.total_value)}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Всего позиций</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{data.summary.total_items}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Категорий</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{data.summary.categories}</div></CardContent></Card>
      </div>

      <Card><CardContent className="pt-6"><div className="space-y-3">
        {data.inventory.map((item) => (
          <Card key={item.id}>
            <CardContent className="pt-6 flex justify-between">
              <div>
                <h3 className="font-semibold">{item.name}</h3>
                <div className="text-sm text-gray-600">{item.category} • {item.quantity} {item.unit} × {formatCurrency(item.cost)}</div>
                {item.location && <div className="text-xs text-gray-500">{item.location}</div>}
              </div>
              <div className="flex gap-2 items-center">
                <div className="text-xl font-bold">{formatCurrency(item.value)}</div>
                <Button variant="outline" size="sm" onClick={() => { setEditingItem(item); setFormData({ name: item.name, category: item.category, quantity: item.quantity, unit: item.unit, cost: item.cost, location: item.location || '' }); setShowDialog(true); }}><Edit className="h-4 w-4" /></Button>
                <Button variant="outline" size="sm" onClick={() => handleDelete(item.id)} className="text-red-600"><Trash2 className="h-4 w-4" /></Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div></CardContent></Card>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editingItem ? 'Редактировать' : 'Добавить'}</DialogTitle></DialogHeader>
          <div className="grid gap-4 py-4">
            <div><Label>Название</Label><Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} /></div>
            <div><Label>Категория</Label><Input value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})} /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Количество</Label><Input type="number" value={formData.quantity} onChange={(e) => setFormData({...formData, quantity: e.target.value})} /></div>
              <div><Label>Единица</Label><Input value={formData.unit} onChange={(e) => setFormData({...formData, unit: e.target.value})} /></div>
            </div>
            <div><Label>Цена (₽)</Label><Input type="number" value={formData.cost} onChange={(e) => setFormData({...formData, cost: e.target.value})} /></div>
            <div><Label>Местоположение</Label><Input value={formData.location} onChange={(e) => setFormData({...formData, location: e.target.value})} /></div>
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
