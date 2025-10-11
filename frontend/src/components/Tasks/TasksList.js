import React, { useState, useEffect } from 'react';
import { Calendar, RefreshCw, Plus, CheckCircle, Clock, AlertCircle, Trash2, Edit2, Brain } from 'lucide-react';
import { taskService } from '../../services/taskService';
import TaskModal from './TaskModal';
import ChecklistModal from './ChecklistModal';
import MindMapEditor from './MindMapEditor';

const TasksList = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    assigned_to_id: ''
  });
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showChecklistModal, setShowChecklistModal] = useState(false);
  const [showMindMapEditor, setShowMindMapEditor] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);

  useEffect(() => {
    loadTasks();
  }, [filters]);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const data = await taskService.getTasks({
        ...filters,
        limit: 50
      });
      setTasks(data);
    } catch (error) {
      console.error('Error loading tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = () => {
    setSelectedTask(null);
    setShowTaskModal(true);
  };

  const handleEditTask = (task) => {
    setSelectedTask(task);
    setShowTaskModal(true);
  };

  const handleDeleteTask = async (taskId) => {
    if (!window.confirm('Удалить задачу?')) return;
    
    try {
      await taskService.deleteTask(taskId);
      setTasks(tasks.filter(t => t.id !== taskId));
    } catch (error) {
      alert('Ошибка удаления задачи');
    }
  };

  const handleTaskSaved = (task) => {
    if (selectedTask) {
      setTasks(tasks.map(t => t.id === task.id ? task : t));
    } else {
      setTasks([task, ...tasks]);
    }
    setShowTaskModal(false);
  };

  const handleStatusChange = async (task, newStatus) => {
    try {
      const updated = await taskService.updateTask(task.id, { status: newStatus });
      setTasks(tasks.map(t => t.id === updated.id ? updated : t));
    } catch (error) {
      alert('Ошибка обновления статуса');
    }
  };

  const openChecklist = (task) => {
    setSelectedTask(task);
    setShowChecklistModal(true);
  };

  const openMindMap = (task) => {
    setSelectedTask(task);
    setShowMindMapEditor(true);
  };

  const getStatusColor = (status) => {
    const colors = {
      todo: 'bg-gray-100 text-gray-700',
      in_progress: 'bg-blue-100 text-blue-700',
      done: 'bg-green-100 text-green-700',
      cancelled: 'bg-red-100 text-red-700'
    };
    return colors[status] || colors.todo;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'text-gray-500',
      medium: 'text-blue-500',
      high: 'text-orange-500',
      urgent: 'text-red-500'
    };
    return colors[priority] || colors.medium;
  };

  const getPriorityLabel = (priority) => {
    const labels = {
      low: 'Низкий',
      medium: 'Средний',
      high: 'Высокий',
      urgent: 'Срочно'
    };
    return labels[priority] || priority;
  };

  const getStatusLabel = (status) => {
    const labels = {
      todo: 'К выполнению',
      in_progress: 'В работе',
      done: 'Выполнено',
      cancelled: 'Отменено'
    };
    return labels[status] || status;
  };

  return (
    <div className="p-6">
      {/* Шапка */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">📋 Задачи</h1>
          <p className="text-gray-600">Управление задачами и чеклистами</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadTasks}
            disabled={loading}
            className="px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Обновить
          </button>
          <button
            onClick={handleCreateTask}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Создать задачу
          </button>
        </div>
      </div>

      {/* Фильтры */}
      <div className="bg-white p-4 rounded-lg border mb-6">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Статус</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="">Все</option>
              <option value="todo">К выполнению</option>
              <option value="in_progress">В работе</option>
              <option value="done">Выполнено</option>
              <option value="cancelled">Отменено</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Приоритет</label>
            <select
              value={filters.priority}
              onChange={(e) => setFilters({...filters, priority: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="">Все</option>
              <option value="low">Низкий</option>
              <option value="medium">Средний</option>
              <option value="high">Высокий</option>
              <option value="urgent">Срочно</option>
            </select>
          </div>
        </div>
      </div>

      {/* Список задач */}
      <div className="grid grid-cols-1 gap-4">
        {tasks.map(task => (
          <div key={task.id} className="bg-white p-4 rounded-lg border hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold">{task.title}</h3>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(task.status)}`}>
                    {getStatusLabel(task.status)}
                  </span>
                  {task.ai_proposed && (
                    <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700">
                      🤖 AI
                    </span>
                  )}
                </div>
                <p className="text-gray-600 text-sm mb-2">{task.description}</p>
                <div className="flex gap-4 text-sm text-gray-500">
                  <span className={getPriorityColor(task.priority)}>
                    ⚡ {getPriorityLabel(task.priority)}
                  </span>
                  {task.due_date && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {new Date(task.due_date).toLocaleDateString('ru-RU')}
                    </span>
                  )}
                  {task.checklist && task.checklist.length > 0 && (
                    <span className="flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" />
                      {task.checklist.filter(item => item.done).length}/{task.checklist.length}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => openMindMap(task)}
                  className="p-2 hover:bg-gray-100 rounded"
                  title="Mind-Map"
                >
                  <Brain className="w-5 h-5 text-purple-600" />
                </button>
                {task.checklist && (
                  <button
                    onClick={() => openChecklist(task)}
                    className="p-2 hover:bg-gray-100 rounded"
                    title="Чеклист"
                  >
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  </button>
                )}
                <button
                  onClick={() => handleEditTask(task)}
                  className="p-2 hover:bg-gray-100 rounded"
                  title="Редактировать"
                >
                  <Edit2 className="w-5 h-5 text-blue-600" />
                </button>
                <button
                  onClick={() => handleDeleteTask(task.id)}
                  className="p-2 hover:bg-gray-100 rounded"
                  title="Удалить"
                >
                  <Trash2 className="w-5 h-5 text-red-600" />
                </button>
              </div>
            </div>

            {/* Быстрая смена статуса */}
            <div className="flex gap-2 mt-3 pt-3 border-t">
              {task.status !== 'done' && (
                <button
                  onClick={() => handleStatusChange(task, 'done')}
                  className="px-3 py-1 text-sm bg-green-50 text-green-700 rounded hover:bg-green-100"
                >
                  ✓ Выполнить
                </button>
              )}
              {task.status === 'todo' && (
                <button
                  onClick={() => handleStatusChange(task, 'in_progress')}
                  className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
                >
                  ▶ В работу
                </button>
              )}
              {task.status !== 'cancelled' && task.status !== 'done' && (
                <button
                  onClick={() => handleStatusChange(task, 'cancelled')}
                  className="px-3 py-1 text-sm bg-red-50 text-red-700 rounded hover:bg-red-100"
                >
                  ✕ Отменить
                </button>
              )}
            </div>
          </div>
        ))}

        {tasks.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-500">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Нет задач</p>
            <button
              onClick={handleCreateTask}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Создать первую задачу
            </button>
          </div>
        )}
      </div>

      {/* Модальные окна */}
      {showTaskModal && (
        <TaskModal
          task={selectedTask}
          onClose={() => setShowTaskModal(false)}
          onSave={handleTaskSaved}
        />
      )}

      {showChecklistModal && selectedTask && (
        <ChecklistModal
          task={selectedTask}
          onClose={() => setShowChecklistModal(false)}
          onUpdate={(updatedTask) => {
            setTasks(tasks.map(t => t.id === updatedTask.id ? updatedTask : t));
            setShowChecklistModal(false);
          }}
        />
      )}

      {showMindMapEditor && selectedTask && (
        <MindMapEditor
          task={selectedTask}
          onClose={() => setShowMindMapEditor(false)}
          onSave={() => {
            loadTasks();
            setShowMindMapEditor(false);
          }}
        />
      )}
    </div>
  );
};

export default TasksList;