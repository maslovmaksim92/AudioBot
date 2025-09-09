import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';

const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [filteredTasks, setFilteredTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  
  // Состояния фильтров
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    responsible_id: ''
  });
  
  // Состояние формы создания задачи
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    responsible_id: 1,
    priority: 1,
    deadline: '',
    group_id: null
  });

  const { state } = useApp();
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://audiobot-qci2.onrender.com';

  useEffect(() => {
    loadTasks();
    loadUsers();
    loadStats();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [tasks, filters]);

  const loadTasks = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.responsible_id) params.append('responsible_id', filters.responsible_id);
      
      const response = await fetch(`${backendUrl}/api/tasks?${params}`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setTasks(data.tasks || []);
        console.log('✅ Tasks loaded:', data.tasks?.length);
      } else {
        console.error('❌ Failed to load tasks:', data.message);
        setTasks([]);
      }
    } catch (error) {
      console.error('❌ Error loading tasks:', error);
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/tasks/users`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setUsers(data.users || []);
      }
    } catch (error) {
      console.error('❌ Error loading users:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/tasks/stats`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setStats(data.stats);
      }
    } catch (error) {
      console.error('❌ Error loading stats:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...tasks];
    
    if (filters.status) {
      filtered = filtered.filter(task => task.status === filters.status);
    }
    
    if (filters.priority) {
      filtered = filtered.filter(task => task.priority === filters.priority);
    }
    
    if (filters.responsible_id) {
      filtered = filtered.filter(task => task.responsible_name.includes(filters.responsible_id));
    }
    
    setFilteredTasks(filtered);
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    
    if (!newTask.title.trim()) {
      alert('Название задачи обязательно');
      return;
    }

    try {
      setLoading(true);
      
      const response = await fetch(`${backendUrl}/api/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newTask)
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        alert(`✅ Задача создана в Bitrix24!\nID: ${data.task_id}`);
        setShowCreateModal(false);
        setNewTask({
          title: '',
          description: '',
          responsible_id: 1,
          priority: 1,
          deadline: '',
          group_id: null
        });
        loadTasks(); // Перезагружаем список
        loadStats(); // Обновляем статистику
      } else {
        alert(`❌ Ошибка создания задачи: ${data.message}`);
      }
    } catch (error) {
      console.error('❌ Error creating task:', error);
      alert('❌ Ошибка создания задачи');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case '0': return 'text-gray-600';
      case '1': return 'text-blue-600';
      case '2': return 'text-red-600';
      default: return 'text-blue-600';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case '1': return 'bg-gray-100 text-gray-800';
      case '2': return 'bg-yellow-100 text-yellow-800';
      case '3': return 'bg-blue-100 text-blue-800';
      case '4': return 'bg-purple-100 text-purple-800';
      case '5': return 'bg-green-100 text-green-800';
      case '6': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-6">
      {/* Заголовок */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              📋 Управление задачами
            </h1>
            <p className="text-gray-600 mt-2">Создание и синхронизация с Bitrix24</p>
          </div>
          
          {/* Переливающаяся кнопка как на картинке */}
          <div className="relative">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 rounded-xl blur opacity-70 animate-pulse"></div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="relative px-6 py-3 bg-gray-900 text-white rounded-xl font-semibold hover:bg-gray-800 transition-all duration-200 flex items-center space-x-2"
            >
              <span>➕</span>
              <span>Создать задачу</span>
            </button>
          </div>
        </div>
      </div>

      {/* Статистика с переливающимися эффектами */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {/* Переливающийся блок 1 */}
          <div className="group relative">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-400 via-cyan-500 to-blue-600 rounded-xl blur opacity-20 group-hover:opacity-50 transition duration-500 animate-pulse"></div>
            <div className="relative bg-gradient-to-r from-blue-400 to-blue-600 rounded-xl p-6 text-white">
              <div className="text-3xl font-bold">{stats.total_tasks}</div>
              <div className="text-blue-100">Всего задач</div>
            </div>
          </div>
          
          {/* Переливающийся блок 2 */}
          <div className="group relative">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-red-400 via-pink-500 to-red-600 rounded-xl blur opacity-20 group-hover:opacity-50 transition duration-500"></div>
            <div className="relative bg-gradient-to-r from-red-400 to-red-600 rounded-xl p-6 text-white">
              <div className="text-3xl font-bold">{stats.overdue_tasks}</div>
              <div className="text-red-100">Просрочено</div>
            </div>
          </div>
          
          {/* Переливающийся блок 3 */}
          <div className="group relative">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-yellow-400 via-orange-500 to-yellow-600 rounded-xl blur opacity-20 group-hover:opacity-50 transition duration-500"></div>
            <div className="relative bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-xl p-6 text-white">
              <div className="text-3xl font-bold">{stats.today_deadline}</div>
              <div className="text-yellow-100">Сегодня дедлайн</div>
            </div>
          </div>
          
          {/* Переливающийся блок 4 */}
          <div className="group relative">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-green-400 via-emerald-500 to-green-600 rounded-xl blur opacity-20 group-hover:opacity-50 transition duration-500"></div>
            <div className="relative bg-gradient-to-r from-green-400 to-green-600 rounded-xl p-6 text-white">
              <div className="text-3xl font-bold">{stats.by_status?.['Завершена'] || 0}</div>
              <div className="text-green-100">Завершено</div>
            </div>
          </div>
        </div>
      )}

      {/* Фильтры с переливающимся эффектом */}
      <div className="group relative mb-8">
        <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-300 via-blue-400 to-purple-400 rounded-xl blur opacity-10 group-hover:opacity-25 transition duration-500"></div>
        <div className="relative bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <h3 className="text-lg font-semibold mb-4">🔍 Фильтры</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Статус</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({...filters, status: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Все статусы</option>
                <option value="1">Новая</option>
                <option value="2">Ждет выполнения</option>
                <option value="3">Выполняется</option>
                <option value="4">Ждет контроля</option>
                <option value="5">Завершена</option>
                <option value="6">Отложена</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Приоритет</label>
              <select
                value={filters.priority}
                onChange={(e) => setFilters({...filters, priority: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Все приоритеты</option>
                <option value="0">Низкий</option>
                <option value="1">Обычный</option>
                <option value="2">Высокий</option>
              </select>
            </div>
            
            <div className="flex items-end">
              <button
                onClick={() => setFilters({status: '', priority: '', responsible_id: ''})}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                🔄 Сбросить
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Список задач с переливающимся эффектом */}
      <div className="group relative">
        <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-300 via-blue-400 to-cyan-400 rounded-xl blur opacity-10 group-hover:opacity-20 transition duration-500"></div>
        <div className="relative bg-white rounded-xl shadow-lg border border-gray-100">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold">
              📝 Задачи ({loading ? '...' : filteredTasks.length})
            </h3>
          </div>

          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Загрузка задач...</p>
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              📋 Задачи не найдены
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {filteredTasks.map((task) => (
                <div key={task.id} className="group relative">
                  <div className="absolute -inset-x-2 -inset-y-1 bg-gradient-to-r from-transparent via-blue-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-lg"></div>
                  <div className="relative p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h4 className="text-lg font-semibold text-gray-900">{task.title}</h4>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                            {task.status_text}
                          </span>
                          <span className={`text-sm font-medium ${getPriorityColor(task.priority)}`}>
                            {task.priority_text}
                          </span>
                        </div>
                        
                        {task.description && (
                          <p className="text-gray-600 mb-3">{task.description}</p>
                        )}
                        
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>👤 {task.responsible_name}</span>
                          <span>📅 Создано: {new Date(task.created_date).toLocaleDateString()}</span>
                          {task.deadline && (
                            <span>⏰ Дедлайн: {new Date(task.deadline).toLocaleDateString()}</span>
                          )}
                        </div>
                      </div>
                      
                      {task.bitrix_url && (
                        <div className="relative group/link">
                          <div className="absolute -inset-1 bg-gradient-to-r from-blue-400 to-cyan-400 rounded-lg blur opacity-0 group-hover/link:opacity-30 transition duration-300"></div>
                          <a
                            href={task.bitrix_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="relative ml-4 px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm hover:bg-blue-200 transition-colors"
                          >
                            🔗 Bitrix24
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Модальное окно создания задачи */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="group relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 rounded-xl blur opacity-30"></div>
            <div className="relative bg-white rounded-xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-bold">➕ Создать задачу</h2>
                <p className="text-gray-600 text-sm mt-1">Задача будет создана в Bitrix24</p>
              </div>
              
              <form onSubmit={handleCreateTask} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Название задачи *
                  </label>
                  <input
                    type="text"
                    value={newTask.title}
                    onChange={(e) => setNewTask({...newTask, title: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Введите название задачи"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Описание
                  </label>
                  <textarea
                    value={newTask.description}
                    onChange={(e) => setNewTask({...newTask, description: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows="3"
                    placeholder="Описание задачи"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ответственный
                  </label>
                  <select
                    value={newTask.responsible_id}
                    onChange={(e) => setNewTask({...newTask, responsible_id: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {users.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.name} {user.position && `(${user.position})`}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Приоритет
                  </label>
                  <select
                    value={newTask.priority}
                    onChange={(e) => setNewTask({...newTask, priority: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value={0}>Низкий</option>
                    <option value={1}>Обычный</option>
                    <option value={2}>Высокий</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Дедлайн
                  </label>
                  <input
                    type="date"
                    value={newTask.deadline}
                    onChange={(e) => setNewTask({...newTask, deadline: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div className="flex space-x-3 pt-4">
                  {/* Переливающаяся кнопка создания */}
                  <div className="relative flex-1">
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg blur opacity-40"></div>
                    <button
                      type="submit"
                      disabled={loading}
                      className="relative w-full px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all duration-200 disabled:opacity-50"
                    >
                      {loading ? '⏳ Создание...' : '✅ Создать в Bitrix24'}
                    </button>
                  </div>
                  
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                  >
                    ❌ Отмена
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tasks;