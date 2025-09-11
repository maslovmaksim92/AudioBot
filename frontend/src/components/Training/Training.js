import React, { useState, useEffect } from 'react';
import { Card, Button, StatCard } from '../UI';

const Training = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [trainingData, setTrainingData] = useState([]);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://audiobot-qci2.onrender.com';

  const fetchLearningStats = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/learning/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching learning stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportTrainingData = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/learning/export`);
      if (response.ok) {
        const data = await response.json();
        setTrainingData(data.data || []);
        alert(`Экспортировано ${data.total_exported} диалогов для обучения`);
      }
    } catch (error) {
      console.error('Error exporting training data:', error);
      alert('Ошибка экспорта данных');
    }
  };

  const triggerTraining = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/learning/train`, {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        alert('Обучение запущено в фоновом режиме');
        fetchLearningStats(); // Refresh stats
      }
    } catch (error) {
      console.error('Error triggering training:', error);
      alert('Ошибка запуска обучения');
    }
  };

  useEffect(() => {
    fetchLearningStats();
  }, []);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Обучение AI</h1>
          <p className="text-gray-600">База знаний и самообучение</p>
        </div>
        <Button onClick={fetchLearningStats} loading={loading}>
          🔄 Обновить
        </Button>
      </div>

      {/* Learning Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Всего диалогов"
            value={stats.total_interactions || 0}
            icon={<span className="text-2xl">💬</span>}
            color="blue"
            subtitle="Общее количество"
          />
          <StatCard
            title="Средняя оценка"
            value={stats.avg_rating ? stats.avg_rating.toFixed(1) : 'N/A'}
            icon={<span className="text-2xl">⭐</span>}
            color="yellow"
            subtitle="По 5-балльной шкале"
          />
          <StatCard
            title="Положительные"
            value={stats.positive_ratings || 0}
            icon={<span className="text-2xl">👍</span>}
            color="green"
            subtitle="Оценки 4-5 звезд"
          />
          <StatCard
            title="Отрицательные"
            value={stats.negative_ratings || 0}
            icon={<span className="text-2xl">👎</span>}
            color="red"
            subtitle="Оценки 1-2 звезды"
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Training Controls */}
        <Card title="🚀 Управление обучением">
          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Экспорт данных для обучения</h4>
              <p className="text-sm text-gray-600 mb-3">
                Экспортировать качественные диалоги (рейтинг ≥ 4 звезд) для тонкой настройки модели.
              </p>
              <Button onClick={exportTrainingData} variant="secondary" className="w-full">
                📤 Экспорт данных обучения
              </Button>
            </div>

            <div>
              <h4 className="font-medium mb-2">Запуск переобучения</h4>
              <p className="text-sm text-gray-600 mb-3">
                Запустить процесс непрерывного обучения на новых данных.
              </p>
              <Button onClick={triggerTraining} variant="primary" className="w-full">
                🧠 Запустить обучение
              </Button>
            </div>

            {stats && stats.last_learning_update && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Последнее обучение:</strong><br/>
                  {new Date(stats.last_learning_update).toLocaleString('ru-RU')}
                </p>
              </div>
            )}
          </div>
        </Card>

        {/* Training Data Preview */}
        <Card title="📊 Данные для обучения">
          {trainingData.length > 0 ? (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {trainingData.slice(0, 5).map((item, index) => (
                <div key={index} className="border border-gray-200 rounded p-3 text-sm">
                  <div className="font-medium text-blue-600 mb-1">
                    Пользователь:
                  </div>
                  <div className="mb-2 text-gray-700">
                    {item.messages[0]?.content}
                  </div>
                  <div className="font-medium text-green-600 mb-1">
                    AI ответ:
                  </div>
                  <div className="text-gray-700">
                    {item.messages[1]?.content}
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    Рейтинг: {item.metadata.rating}★
                  </div>
                </div>
              ))}
              {trainingData.length > 5 && (
                <p className="text-sm text-gray-500 text-center">
                  ... и еще {trainingData.length - 5} диалогов
                </p>
              )}
            </div>
          ) : (
            <div className="text-center text-gray-500">
              <p className="text-lg mb-2">📚</p>
              <p>Нажмите "Экспорт данных обучения" чтобы увидеть данные</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default Training;