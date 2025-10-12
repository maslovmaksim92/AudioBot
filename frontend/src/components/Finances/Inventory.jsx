import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Package, MapPin, DollarSign, Hash } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function Inventory() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return <div className="text-center p-8">Загрузка...</div>;
  }

  if (!data) {
    return <div className="text-center p-8">Нет данных</div>;
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-teal-50 to-teal-100 border-teal-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-teal-800 flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Общая стоимость
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-teal-900">
              {formatCurrency(data.summary.total_value)}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-blue-800 flex items-center gap-2">
              <Hash className="h-4 w-4" />
              Всего единиц
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">
              {data.summary.total_items}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-purple-800 flex items-center gap-2">
              <Package className="h-4 w-4" />
              Категорий
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-900">
              {data.summary.categories}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Inventory Table */}
      <Card>
        <CardHeader>
          <CardTitle>Товарные запасы</CardTitle>
          <CardDescription>Детальная информация по складским остаткам</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">Наименование</th>
                  <th className="text-left py-3 px-4">Категория</th>
                  <th className="text-right py-3 px-4">Количество</th>
                  <th className="text-right py-3 px-4">Ед. изм.</th>
                  <th className="text-right py-3 px-4">Цена за ед.</th>
                  <th className="text-right py-3 px-4">Стоимость</th>
                  <th className="text-left py-3 px-4">Склад</th>
                </tr>
              </thead>
              <tbody>
                {data.inventory.map((item) => (
                  <tr key={item.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{item.name}</td>
                    <td className="py-3 px-4">
                      <Badge variant="outline">{item.category}</Badge>
                    </td>
                    <td className="text-right py-3 px-4 font-semibold">{item.quantity}</td>
                    <td className="text-right py-3 px-4 text-gray-600">{item.unit}</td>
                    <td className="text-right py-3 px-4">{formatCurrency(item.cost)}</td>
                    <td className="text-right py-3 px-4 font-semibold text-teal-600">
                      {formatCurrency(item.value)}
                    </td>
                    <td className="py-3 px-4 text-gray-600 flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {item.location}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 font-bold bg-gray-50">
                  <td colSpan="5" className="py-3 px-4">Итого</td>
                  <td className="text-right py-3 px-4 text-teal-600">
                    {formatCurrency(data.summary.total_value)}
                  </td>
                  <td className="py-3 px-4"></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Inventory by Category */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(
          data.inventory.reduce((acc, item) => {
            if (!acc[item.category]) {
              acc[item.category] = { items: 0, value: 0 };
            }
            acc[item.category].items += item.quantity;
            acc[item.category].value += item.value;
            return acc;
          }, {})
        ).map(([category, stats]) => (
          <Card key={category} className="border-teal-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Package className="h-4 w-4 text-teal-600" />
                {category}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Единиц:</span>
                  <span className="font-semibold">{stats.items}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Стоимость:</span>
                  <span className="font-semibold text-teal-600">
                    {formatCurrency(stats.value)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default Inventory;
