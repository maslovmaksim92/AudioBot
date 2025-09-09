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
    &lt;div className="p-6"&gt;
      &lt;div className="flex justify-between items-center mb-6"&gt;
        &lt;div&gt;
          &lt;h1 className="text-3xl font-bold text-gray-900"&gt;AI Задачи&lt;/h1&gt;
          &lt;p className="text-gray-600"&gt;Умные задачи и автоматизация&lt;/p&gt;
        &lt;/div&gt;
        &lt;Button onClick={fetchTasks} loading={loading}&gt;
          🔄 Обновить
        &lt;/Button&gt;
      &lt;/div&gt;

      {/* Create New Task */}
      &lt;Card title="➕ Создать новую AI задачу" className="mb-6"&gt;
        &lt;div className="space-y-4"&gt;
          &lt;div&gt;
            &lt;label className="block text-sm font-medium text-gray-700 mb-1"&gt;
              Название задачи
            &lt;/label&gt;
            &lt;input
              type="text"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              placeholder="Введите название..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            /&gt;
          &lt;/div&gt;
          
          &lt;div&gt;
            &lt;label className="block text-sm font-medium text-gray-700 mb-1"&gt;
              Описание задачи
            &lt;/label&gt;
            &lt;textarea
              value={newTaskDescription}
              onChange={(e) => setNewTaskDescription(e.target.value)}
              placeholder="Опишите что должен сделать AI..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            /&gt;
          &lt;/div&gt;
          
          &lt;Button onClick={createTask} disabled={!newTaskTitle.trim() || !newTaskDescription.trim()}&gt;
            🧠 Создать AI задачу
          &lt;/Button&gt;
        &lt;/div&gt;
      &lt;/Card&gt;

      {/* Tasks List */}
      {loading ? (
        &lt;div className="flex justify-center py-12"&gt;
          &lt;LoadingSpinner size="lg" text="Загрузка AI задач..." /&gt;
        &lt;/div&gt;
      ) : tasks.length > 0 ? (
        &lt;div className="grid grid-cols-1 lg:grid-cols-2 gap-6"&gt;
          {tasks.map(task => (
            &lt;Card key={task.id} className="hover:shadow-lg transition-shadow"&gt;
              &lt;div className="space-y-4"&gt;
                &lt;div className="flex justify-between items-start"&gt;
                  &lt;h3 className="font-semibold text-gray-900"&gt;{task.title}&lt;/h3&gt;
                  &lt;span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}&gt;
                    {getStatusText(task.status)}
                  &lt;/span&gt;
                &lt;/div&gt;
                
                &lt;p className="text-gray-700 text-sm"&gt;{task.description}&lt;/p&gt;
                
                &lt;div className="space-y-2 text-sm text-gray-600"&gt;
                  {task.scheduled_time && (
                    &lt;div className="flex justify-between"&gt;
                      &lt;span&gt;Запланировано:&lt;/span&gt;
                      &lt;span&gt;{new Date(task.scheduled_time).toLocaleString('ru-RU')}&lt;/span&gt;
                    &lt;/div&gt;
                  )}
                  
                  {task.created_at && (
                    &lt;div className="flex justify-between"&gt;
                      &lt;span&gt;Создана:&lt;/span&gt;
                      &lt;span&gt;{new Date(task.created_at).toLocaleString('ru-RU')}&lt;/span&gt;
                    &lt;/div&gt;
                  )}
                  
                  {task.recurring && (
                    &lt;div className="flex justify-between"&gt;
                      &lt;span&gt;Повторяющаяся:&lt;/span&gt;
                      &lt;span className="text-blue-600"&gt;Да&lt;/span&gt;
                    &lt;/div&gt;
                  )}
                &lt;/div&gt;
                
                &lt;div className="pt-3 border-t border-gray-100"&gt;
                  &lt;div className="flex justify-between items-center"&gt;
                    &lt;span className="text-xs text-gray-500"&gt;ID: {task.id}&lt;/span&gt;
                    &lt;div className="flex space-x-2"&gt;
                      {task.status === 'pending' && (
                        &lt;Button size="sm" variant="primary"&gt;▶️ Запустить&lt;/Button&gt;
                      )}
                      {task.status === 'in_progress' && (
                        &lt;Button size="sm" variant="warning"&gt;⏸️ Приостановить&lt;/Button&gt;
                      )}
                      &lt;Button size="sm" variant="ghost"&gt;👁️ Детали&lt;/Button&gt;
                    &lt;/div&gt;
                  &lt;/div&gt;
                &lt;/div&gt;
              &lt;/div&gt;
            &lt;/Card&gt;
          ))}
        &lt;/div&gt;
      ) : (
        &lt;Card&gt;
          &lt;div className="text-center py-12"&gt;
            &lt;div className="text-6xl mb-4"&gt;🧠&lt;/div&gt;
            &lt;h3 className="text-lg font-medium text-gray-900 mb-2"&gt;Нет AI задач&lt;/h3&gt;
            &lt;p className="text-gray-600"&gt;
              Создайте первую умную задачу для автоматизации бизнес-процессов
            &lt;/p&gt;
          &lt;/div&gt;
        &lt;/Card&gt;
      )}

      {/* AI Features Info */}
      &lt;Card title="🤖 Возможности AI" className="mt-6"&gt;
        &lt;div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-600"&gt;
          &lt;div&gt;
            &lt;h4 className="font-medium text-gray-900 mb-2"&gt;Аналитика и отчеты:&lt;/h4&gt;
            &lt;ul className="space-y-1"&gt;
              &lt;li&gt;• Анализ эффективности бригад&lt;/li&gt;
              &lt;li&gt;• Прогнозирование объемов работ&lt;/li&gt;
              &lt;li&gt;• Выявление проблемных домов&lt;/li&gt;
              &lt;li&gt;• Оптимизация расписаний&lt;/li&gt;
            &lt;/ul&gt;
          &lt;/div&gt;
          &lt;div&gt;
            &lt;h4 className="font-medium text-gray-900 mb-2"&gt;Автоматизация:&lt;/h4&gt;
            &lt;ul className="space-y-1"&gt;
              &lt;li&gt;• Автоматическое планирование задач&lt;/li&gt;
              &lt;li&gt;• Уведомления о критических ситуациях&lt;/li&gt;
              &lt;li&gt;• Обработка обратной связи клиентов&lt;/li&gt;
              &lt;li&gt;• Предложения по улучшению процессов&lt;/li&gt;
            &lt;/ul&gt;
          &lt;/div&gt;
        &lt;/div&gt;
      &lt;/Card&gt;
    &lt;/div&gt;
  );
};

export default AITasks;