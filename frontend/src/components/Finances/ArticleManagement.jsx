import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Alert, AlertDescription } from '../ui/alert';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const AVAILABLE_CATEGORIES = [
  "Зарплата",
  "Материалы",
  "Аренда",
  "Коммунальные услуги",
  "Транспорт",
  "Реклама и маркетинг",
  "Налоги",
  "Страхование",
  "Оборудование",
  "Покупка авто",
  "Канцтовары",
  "Юридические услуги",
  "Аутсорсинг",
  "Лизинг",
  "Кредиты",
  "Мобильная связь",
  "Продукты питания",
  "Цифровая техника",
  "Прочие расходы"
];

const ArticleManagement = () => {
  const [unmappedArticles, setUnmappedArticles] = useState([]);
  const [allArticles, setAllArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('unmapped');
  const [changes, setChanges] = useState({});
  const [message, setMessage] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [unmappedRes, allRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/finances/articles/unmapped`),
        fetch(`${BACKEND_URL}/api/finances/articles`)
      ]);

      const unmappedData = await unmappedRes.json();
      const allData = await allRes.json();

      setUnmappedArticles(unmappedData.unmapped_articles || []);
      setAllArticles(allData.articles || []);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
      setMessage({ type: 'error', text: 'Ошибка загрузки данных' });
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryChange = (article, newCategory) => {
    setChanges(prev => ({
      ...prev,
      [article]: newCategory
    }));
  };

  const saveChanges = async () => {
    if (Object.keys(changes).length === 0) {
      setMessage({ type: 'warning', text: 'Нет изменений для сохранения' });
      return;
    }

    setLoading(true);
    try {
      const mappings = Object.entries(changes).map(([article, category]) => ({
        article,
        category
      }));

      const response = await fetch(`${BACKEND_URL}/api/finances/articles/update-mapping`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mappings })
      });

      const result = await response.json();

      if (result.success) {
        setMessage({
          type: 'success',
          text: `Успешно обновлено ${result.updated_transactions} транзакций для ${result.updated_articles} статей`
        });
        setChanges({});
        setTimeout(() => loadData(), 1000);
      }
    } catch (error) {
      console.error('Ошибка сохранения:', error);
      setMessage({ type: 'error', text: 'Ошибка сохранения изменений' });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const filteredArticles = allArticles.filter(article =>
    article.article.toLowerCase().includes(searchQuery.toLowerCase()) ||
    article.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Управление статьями расходов</h1>
        <Button
          onClick={saveChanges}
          disabled={loading || Object.keys(changes).length === 0}
          className="bg-blue-600 hover:bg-blue-700"
        >
          {loading ? 'Сохранение...' : `Сохранить изменения (${Object.keys(changes).length})`}
        </Button>
      </div>

      {message && (
        <Alert className={message.type === 'error' ? 'bg-red-50' : message.type === 'success' ? 'bg-green-50' : 'bg-yellow-50'}>
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('unmapped')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'unmapped'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Не назначенные ({unmappedArticles.length})
        </button>
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'all'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Все статьи ({allArticles.length})
        </button>
      </div>

      {activeTab === 'unmapped' && (
        <Card>
          <CardHeader>
            <CardTitle>Статьи без категории</CardTitle>
          </CardHeader>
          <CardContent>
            {unmappedArticles.length === 0 ? (
              <p className="text-gray-500">Все статьи назначены на категории ✓</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Статья</TableHead>
                    <TableHead>Транзакций</TableHead>
                    <TableHead>Сумма</TableHead>
                    <TableHead>Примеры</TableHead>
                    <TableHead>Назначить категорию</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {unmappedArticles.map((article) => (
                    <TableRow key={article.article}>
                      <TableCell className="font-mono font-bold">{article.article}</TableCell>
                      <TableCell>{article.transaction_count}</TableCell>
                      <TableCell>{formatCurrency(article.total_amount)}</TableCell>
                      <TableCell className="max-w-xs truncate text-sm text-gray-600">
                        {article.sample_descriptions.join(', ')}
                      </TableCell>
                      <TableCell>
                        <Select
                          value={changes[article.article] || ''}
                          onValueChange={(value) => handleCategoryChange(article.article, value)}
                        >
                          <SelectTrigger className="w-48">
                            <SelectValue placeholder="Выберите категорию" />
                          </SelectTrigger>
                          <SelectContent>
                            {AVAILABLE_CATEGORIES.map((cat) => (
                              <SelectItem key={cat} value={cat}>
                                {cat}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      {activeTab === 'all' && (
        <Card>
          <CardHeader>
            <CardTitle>Все статьи расходов</CardTitle>
            <div className="mt-4">
              <Input
                type="text"
                placeholder="Поиск по статье или категории..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="max-w-md"
              />
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Статья</TableHead>
                  <TableHead>Текущая категория</TableHead>
                  <TableHead>Транзакций</TableHead>
                  <TableHead>Сумма</TableHead>
                  <TableHead>Изменить категорию</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredArticles.map((article) => (
                  <TableRow key={article.article}>
                    <TableCell className="font-mono font-bold">{article.article}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded text-sm ${
                        article.is_mapped ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {article.category}
                      </span>
                    </TableCell>
                    <TableCell>{article.transaction_count}</TableCell>
                    <TableCell>{formatCurrency(article.total_amount)}</TableCell>
                    <TableCell>
                      <Select
                        value={changes[article.article] || article.mapped_category}
                        onValueChange={(value) => handleCategoryChange(article.article, value)}
                      >
                        <SelectTrigger className="w-48">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {AVAILABLE_CATEGORIES.map((cat) => (
                            <SelectItem key={cat} value={cat}>
                              {cat}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ArticleManagement;
