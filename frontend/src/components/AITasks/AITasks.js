import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { apiService } from '../../services/apiService';
import { Card, Button, LoadingSpinner } from '../UI';

const AITasks = () => {
  const { actions } = useApp();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDescription, setNewTaskDescription] = useState('');

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await apiService.getAITasks();
      if (response.status === 'success') {
        setTasks(response.tasks || []);
        actions.addNotification({
          type: 'success',
          message: `Загружено ${response.tasks?.length || 0} AI задач`
        });
      }
    } catch (error) {
      console.error('❌ Error fetching AI tasks:', error);
      // Fallback demo data
      const mockTasks = [
        {
          id: 1,
          title: 'Анализ эффективности бригад',
          description: 'Проанализировать производительность каждой бригады за последний месяц',
          status: 'pending',
          scheduled_time: new Date(Date.now() + 86400000).toISOString(),
          created_at: new Date().toISOString()
        },
        {
          id: 2,
          title: 'Оптимизация маршрутов',
          description: 'Предложить оптимальные маршруты для каждой бригады на основе адресов домов',
          status: 'in_progress',
          scheduled_time: new Date(Date.now() + 172800000).toISOString(),
          created_at: new Date(Date.now() - 86400000).toISOString()
        }
      ];
      setTasks(mockTasks);
      actions.addNotification({
        type: 'warning',
        message: 'Показаны демо AI задачи'
      });
    } finally {
      setLoading(false);
    }
  };

  const createTask = async () => {
    if (!newTaskTitle.trim() || !newTaskDescription.trim()) {
      actions.addNotification({
        type: 'warning',
        message: 'Заполните название и описание задачи'
      });
      return;
    }

    try {
      const taskData = {
        title: newTaskTitle,
        description: newTaskDescription,
        scheduled_time: new Date(Date.now() + 86400000).toISOString() // Tomorrow
      };

      const response = await apiService.createAITask(taskData);
      if (response.status === 'success') {
        setNewTaskTitle('');
        setNewTaskDescription('');
        await fetchTasks();
        actions.addNotification({
          type: 'success',
          message: 'AI задача создана'
        });
      }
    } catch (error) {
      console.error('❌ Error creating AI task:', error);
      actions.addNotification({
        type: 'error',
        message: 'Ошибка создания AI задачи'
      });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    const statusMap = {
      'pending': 'Ожидает',
      'in_progress': 'Выполняется',
      'completed': 'Завершена',
      'failed': 'Ошибка'
    };
    return statusMap[status] || status;
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Задачи</h1>
          <p className="text-gray-600">Умные задачи и автоматизация</p>
        </div>
        <Button onClick={fetchTasks} loading={loading}>
          🔄 Обновить
        </Button>
      </div>

      {/* Create New Task */}
      <Card title="➕ Создать новую AI задачу" className="mb-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Название задачи
            </label>
            <input
              type="text"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              placeholder="Введите название..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Описание задачи
            </label>
            <textarea
              value={newTaskDescription}
              onChange={(e) => setNewTaskDescription(e.target.value)}
              placeholder="Опишите что должен сделать AI..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <Button onClick={createTask} disabled={!newTaskTitle.trim() || !newTaskDescription.trim()}>
            🧠 Создать AI задачу
          </Button>
        </div>
      </Card>

      {/* Tasks List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" text="Загрузка AI задач..." />
        </div>
      ) : tasks.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {tasks.map(task => (
            <Card key={task.id} className="hover:shadow-lg transition-shadow">
              <div className="space-y-4">
                <div className="flex justify-between items-start">
                  <h3 className="font-semibold text-gray-900">{task.title}</h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                    {getStatusText(task.status)}
                  </span>
                </div>
                
                <p className="text-gray-700 text-sm">{task.description}</p>
                
                <div className="space-y-2 text-sm text-gray-600">
                  {task.scheduled_time && (
                    <div className="flex justify-between">
                      <span>Запланировано:</span>
                      <span>{new Date(task.scheduled_time).toLocaleString('ru-RU')}</span>
                    </div>
                  )}
                  
                  {task.created_at && (
                    <div className="flex justify-between">
                      <span>Создана:</span>
                      <span>{new Date(task.created_at).toLocaleString('ru-RU')}</span>
                    </div>
                  )}
                  
                  {task.recurring && (
                    <div className="flex justify-between">
                      <span>Повторяющаяся:</span>
                      <span className="text-blue-600">Да</span>
                    </div>
                  )}
                </div>
                
                <div className="pt-3 border-t border-gray-100">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">ID: {task.id}</span>
                    <div className="flex space-x-2">
                      {task.status === 'pending' && (
                        <Button size="sm" variant="primary">▶️ Запустить</Button>
                      )}
                      {task.status === 'in_progress' && (
                        <Button size="sm" variant="warning">⏸️ Приостановить</Button>
                      )}
                      <Button size="sm" variant="ghost">👁️ Детали</Button>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🧠</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Нет AI задач</h3>
            <p className="text-gray-600">
              Создайте первую умную задачу для автоматизации бизнес-процессов
            </p>
          </div>
        </Card>
      )}

      {/* AI Features Info */}
      <Card title="🤖 Возможности AI" className="mt-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-600">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Аналитика и отчеты:</h4>
            <ul className="space-y-1">
              <li>• Анализ эффективности бригад</li>
              <li>• Прогнозирование объемов работ</li>
              <li>• Выявление проблемных домов</li>
              <li>• Оптимизация расписаний</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Автоматизация:</h4>
            <ul className="space-y-1">
              <li>• Автоматическое планирование задач</li>
              <li>• Уведомления о критических ситуациях</li>
              <li>• Обработка обратной связи клиентов</li>
              <li>• Предложения по улучшению процессов</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AITasks;