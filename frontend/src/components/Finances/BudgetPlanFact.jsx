import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, TrendingUp, TrendingDown } from 'lucide-react';
import { getBudgets, addBudget, updateBudget, deleteBudget, getPlanFactAnalysis } from '../../utils/financeStorage';

function BudgetPlanFact() {
  const [budgets, setBudgets] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().substring(0, 7));
  const [planFact, setPlanFact] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [formData, setFormData] = useState({ month: selectedMonth, category: '', type: 'expense', amount: '' });

  useEffect(() => {
    loadData();
  }, [selectedMonth]);

  const loadData = () => {
    setBudgets(getBudgets());
    setPlanFact(getPlanFactAnalysis(selectedMonth));
  };

  const handleSave = () => {
    addBudget({ ...formData, amount: parseFloat(formData.amount) });
    setShowDialog(false);
    loadData();
  };

  const formatCurrency = (v) => new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(v);

  const totalPlan = planFact.reduce((s, p) => s + p.plan, 0);
  const totalFact = planFact.reduce((s, p) => s + p.fact, 0);
  const totalVariance = totalFact - totalPlan;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Бюджеты и План-факт</h2>
          <Input type="month" value={selectedMonth} onChange={(e) => setSelectedMonth(e.target.value)} className="w-48 mt-2" />
        </div>
        <Button onClick={() => { setFormData({ month: selectedMonth, category: '', type: 'expense', amount: '' }); setShowDialog(true); }} className="bg-blue-600">
          <Plus className="h-4 w-4 mr-2" />Добавить бюджет
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card><CardHeader><CardTitle className="text-sm">План</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{formatCurrency(totalPlan)}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Факт</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{formatCurrency(totalFact)}</div></CardContent></Card>
        <Card className={totalVariance >= 0 ? 'bg-green-50' : 'bg-red-50'}><CardHeader><CardTitle className="text-sm">Отклонение</CardTitle></CardHeader><CardContent><div className={`text-2xl font-bold ${totalVariance >= 0 ? 'text-green-600' : 'text-red-600'}`}>{formatCurrency(totalVariance)}</div></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>План-факт анализ</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {planFact.map((item, idx) => (
              <Card key={idx} className="border-l-4 border-blue-500">
                <CardContent className="pt-6">
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <h3 className="font-semibold">{item.category}</h3>
                      <div className="flex gap-6 text-sm text-gray-600 mt-2">
                        <span>План: {formatCurrency(item.plan)}</span>
                        <span>Факт: {formatCurrency(item.fact)}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-xl font-bold ${item.variance >= 0 ? 'text-green-600' : 'text-red-600'} flex items-center gap-2`}>
                        {item.variance >= 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
                        {formatCurrency(Math.abs(item.variance))}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">{item.variance_percent.toFixed(1)}%</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {planFact.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <p>Нет данных за выбранный месяц</p>
                <p className="text-sm mt-2">Добавьте бюджет и транзакции</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Добавить бюджет</DialogTitle></DialogHeader>
          <div className="grid gap-4 py-4">
            <div><Label>Категория *</Label><Input value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})} placeholder="Зарплата, Аренда..." /></div>
            <div><Label>Тип</Label>
              <Select value={formData.type} onValueChange={(v) => setFormData({...formData, type: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="income">Доход</SelectItem><SelectItem value="expense">Расход</SelectItem></SelectContent>
              </Select>
            </div>
            <div><Label>Сумма (₽) *</Label><Input type="number" value={formData.amount} onChange={(e) => setFormData({...formData, amount: e.target.value})} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>Отмена</Button>
            <Button onClick={handleSave} disabled={!formData.category || !formData.amount}>Сохранить</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default BudgetPlanFact;
