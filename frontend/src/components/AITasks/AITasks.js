import React, { useState, useEffect } from 'react';
import './AITasks.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

const AITasks = () => {
  const [aiTasks, setAiTasks] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date());
  // Используем первого пользователя из БД (Маслов Максим)
  const userId = '7be8f89e-f2bd-4f24-9798-286fddc58358';
  
  const [taskForm, setTaskForm] = useState({
    title: '',
    type: 'remind',
    time: '12:00',
    date: new Date().toISOString().split('T')[0],
    description: '',
    repeat: 'once'
  });

  useEffect(() => {
    loadAiTasks();
  }, []);

  const loadAiTasks = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/ai/tasks?user_id=${userId}&limit=100`);
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data = await res.json();
      
      // Преобразуем данные из API в формат UI
      const formattedTasks = data.map(task => ({
        id: task.id,
        title: task.title,
        type: mapTaskTypeToUI(task.task_type),
        time: task.scheduled_at ? new Date(task.scheduled_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : 'Не назначено',
        repeat: 'once', // TODO: Добавить поле is_recurring в модель
        status: task.status === 'pending' ? 'active' : task.status,
        description: task.description || '',
        last_run: task.completed_at ? new Date(task.completed_at).toLocaleString('ru-RU') : 'Не выполнялась',
        next_run: task.scheduled_at ? new Date(task.scheduled_at).toLocaleString('ru-RU') : 'Не назначено'
      }));
      
      // Добавляем предустановленные системные задачи
      const systemTasks = [
        {
          id: 'system-1',
          title: 'Напоминание о планерке',
          type: 'telegram',
          time: '08:25',
          repeat: 'daily',
          status: 'active',
          description: 'Отправить сообщение всем сотрудникам о планерке в 8:30',
          last_run: new Date().toLocaleString('ru-RU'),
          next_run: new Date(Date.now() + 86400000).toLocaleString('ru-RU')
        },
        {
          id: 'system-2',
          title: 'Синхронизация Bitrix24',
          type: 'sync',
          time: 'каждые 30 мин',
          repeat: 'interval',
          status: 'active',
          description: 'Автоматическая загрузка домов, графиков уборки, задач из Bitrix24',
          last_run: new Date().toLocaleString('ru-RU'),
          next_run: new Date(Date.now() + 1800000).toLocaleString('ru-RU')
        }
      ];
      
      setAiTasks([...systemTasks, ...formattedTasks]);
    } catch (e) {
      console.error('Error loading AI tasks:', e);
      // Fallback к предустановленным задачам при ошибке
      setAiTasks([
        {
          id: 'fallback-1',
          title: 'Синхронизация Bitrix24',
          type: 'sync',
          time: 'каждые 30 мин',
          repeat: 'interval',
          status: 'active',
          description: 'Автоматическая загрузка домов, графиков уборки, задач из Bitrix24',
          last_run: new Date().toLocaleString('ru-RU'),
          next_run: new Date(Date.now() + 1800000).toLocaleString('ru-RU')
        }
      ]);
    }
  };

  // Маппинг типов задач из API в UI
  const mapTaskTypeToUI = (apiType) => {
    const mapping = {
      'send_schedule': 'email',
      'reminder': 'remind',
      'report': 'report',
      'notification': 'telegram',
      'custom': 'remind'
    };
    return mapping[apiType] || 'remind';
  };

  // Маппинг типов задач из UI в API
  const mapTaskTypeToAPI = (uiType) => {
    const mapping = {
      'email': 'send_schedule',
      'remind': 'reminder',
      'report': 'report',
      'telegram': 'notification',
      'call': 'custom',
      'sync': 'custom'
    };
    return mapping[uiType] || 'custom';
  };

  // Создание новой задачи
  const handleCreateTask = async () => {
    try {
      if (!taskForm.title.trim()) {
        alert('Пожалуйста, введите название задачи');
        return;
      }
      
      // Формируем дату и время для scheduled_at
      const scheduledAt = `${taskForm.date}T${taskForm.time}:00`;
      
      const requestBody = {
        message: `Создай задачу: ${taskForm.title}. Тип: ${taskForm.type}. Описание: ${taskForm.description || 'Нет описания'}. Запланировано на: ${scheduledAt}`,
        user_id: userId
      };

      const res = await fetch(`${BACKEND_URL}/api/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      // Закрываем модальное окно и перезагружаем задачи
      setShowAddModal(false);
      setTaskForm({
        title: '',
        type: 'remind',
        time: '12:00',
        date: new Date().toISOString().split('T')[0],
        description: '',
        repeat: 'once'
      });
      
      // Перезагружаем список задач
      await loadAiTasks();
      
      alert('Задача успешно создана!');
    } catch (e) {
      console.error('Error creating task:', e);
      alert(`Ошибка при создании задачи: ${e.message}`);
    }
  };

  const taskTypes = [
    { value: 'remind', label: '🔔 Напомнить', icon: '🔔' },
    { value: 'call', label: '📞 Позвонить', icon: '📞' },
    { value: 'telegram', label: '✉️ Отправить в Telegram', icon: '✉️' },
    { value: 'email', label: '📧 Отправить Email', icon: '📧' },
    { value: 'sync', label: '🔄 Синхронизация', icon: '🔄' },
    { value: 'report', label: '📊 Сформировать отчет', icon: '📊' }
  ];

  const getTypeIcon = (type) => {
    const typeObj = taskTypes.find(t => t.value === type);
    return typeObj ? typeObj.icon : '📋';
  };

  const getTypeColor = (type) => {
    const colors = {
      remind: '#3b82f6',
      call: '#8b5cf6',
      telegram: '#06b6d4',
      email: '#f59e0b',
      sync: '#10b981',
      report: '#6366f1'
    };
    return colors[type] || '#64748b';
  };

  // Простой календарь на месяц
  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const days = [];
    
    for (let d = 1; d <= lastDay.getDate(); d++) {
      days.push(new Date(year, month, d));
    }
    
    return days;
  };

  const monthDays = getDaysInMonth(selectedDate);

  return (
    <div className="ai-tasks-container">
      {/* Шапка */}
      <div className="ai-tasks-header">
        <div>
          <h1>🤖 AI Задачи и Автоматизация</h1>
          <p className="subtitle">Автоматическое выполнение задач по расписанию</p>
        </div>
        <button onClick={() => setShowAddModal(true)} className="btn btn-add">
          ➕ Создать AI задачу
        </button>
      </div>

      {/* Статистика */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{background: '#dbeafe'}}>📋</div>
          <div className="stat-content">
            <div className="stat-value">{aiTasks.length}</div>
            <div className="stat-label">Всего задач</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{background: '#d1fae5'}}>🟢</div>
          <div className="stat-content">
            <div className="stat-value">{aiTasks.filter(t => t.status === 'active').length}</div>
            <div className="stat-label">Активных</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{background: '#fef3c7'}}>⏰</div>
          <div className="stat-content">
            <div className="stat-value">24/7</div>
            <div className="stat-label">Работает</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{background: '#e0e7ff'}}>💰</div>
          <div className="stat-content">
            <div className="stat-value">~2.5 ч</div>
            <div className="stat-label">Экономия/день</div>
          </div>
        </div>
      </div>

      {/* Календарь */}
      <div className="calendar-section">
        <h2>📅 Календарь AI задач - {selectedDate.toLocaleString('ru-RU', { month: 'long', year: 'numeric' })}</h2>
        <div className="calendar-grid">
          {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map(day => (
            <div key={day} className="calendar-day-header">{day}</div>
          ))}
          {monthDays.map(day => {
            const isToday = day.toDateString() === new Date().toDateString();
            const hasTasks = aiTasks.some(t => t.repeat === 'daily' || t.repeat === 'interval');
            
            return (
              <div 
                key={day.toISOString()} 
                className={`calendar-day ${isToday ? 'today' : ''}`}
              >
                <div className="day-number">{day.getDate()}</div>
                {hasTasks && <div className="day-indicator">●</div>}
              </div>
            );
          })}
        </div>
      </div>

      {/* Список AI задач */}
      <div className="ai-tasks-list">
        <h2>🤖 Активные AI задачи</h2>
        <div className="tasks-grid">
          {aiTasks.map(task => (
            <div key={task.id} className="ai-task-card">
              <div className="task-header">
                <div className="task-icon" style={{background: getTypeColor(task.type)}}>
                  {getTypeIcon(task.type)}
                </div>
                <div className="task-info">
                  <h3>{task.title}</h3>
                  <p className="task-time">⏰ {task.time}</p>
                </div>
                <div className={`status-badge ${task.status}`}>
                  {task.status === 'active' ? '🟢 Активна' : '⏸️ Пауза'}
                </div>
              </div>

              <p className="task-description">{task.description}</p>

              <div className="task-schedule">
                <div className="schedule-item">
                  <span className="label">Повтор:</span>
                  <span className="value">
                    {task.repeat === 'daily' ? '📆 Ежедневно' : 
                     task.repeat === 'interval' ? '🔄 Каждые 15 мин' : 
                     '🔘 Однократно'}
                  </span>
                </div>
                <div className="schedule-item">
                  <span className="label">Последний запуск:</span>
                  <span className="value">{task.last_run}</span>
                </div>
                <div className="schedule-item">
                  <span className="label">Следующий запуск:</span>
                  <span className="value next">{task.next_run}</span>
                </div>
              </div>

              <div className="task-actions">
                <button className="btn-small">✏️ Редактировать</button>
                <button className="btn-small">⚡ Запустить сейчас</button>
                {task.status === 'active' ? (
                  <button className="btn-small">⏸️ Пауза</button>
                ) : (
                  <button className="btn-small">▶️ Активировать</button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Подсказки */}
      <div className="ai-suggestions">
        <h3>💡 AI Предложения для новых задач</h3>
        <div className="suggestions-grid">
          <div className="suggestion-card" onClick={() => {
            setTaskForm({
              ...taskForm,
              title: 'Обзвон клиентов для отзывов',
              type: 'call',
              time: '14:00',
              description: 'Позвонить клиентам после выполнения работ и попросить оставить отзыв'
            });
            setShowAddModal(true);
          }}>
            <span className="suggestion-icon">📞</span>
            <span className="suggestion-text">Обзвон клиентов для отзывов</span>
          </div>
          <div className="suggestion-card" onClick={() => {
            setTaskForm({
              ...taskForm,
              title: 'Еженедельный отчет руководителям',
              type: 'report',
              time: '18:00',
              description: 'Сформировать и отправить отчет о выполненных работах за неделю'
            });
            setShowAddModal(true);
          }}>
            <span className="suggestion-icon">📊</span>
            <span className="suggestion-text">Еженедельный отчет руководителям</span>
          </div>
          <div className="suggestion-card" onClick={() => {
            setTaskForm({
              ...taskForm,
              title: 'Проверка просроченных актов',
              type: 'remind',
              time: '10:00',
              description: 'Проверить дома с неподписанными актами и отправить напоминания'
            });
            setShowAddModal(true);
          }}>
            <span className="suggestion-icon">📋</span>
            <span className="suggestion-text">Проверка просроченных актов</span>
          </div>
        </div>
      </div>

      {/* Модальное окно создания задачи */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>🤖 Создать AI задачу</h2>
              <button onClick={() => setShowAddModal(false)} className="close-btn">✕</button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label>Название задачи *</label>
                <input
                  type="text"
                  value={taskForm.title}
                  onChange={(e) => setTaskForm({...taskForm, title: e.target.value})}
                  placeholder="Например: Напомнить о планерке"
                />
              </div>

              <div className="form-group">
                <label>Тип задачи *</label>
                <select
                  value={taskForm.type}
                  onChange={(e) => setTaskForm({...taskForm, type: e.target.value})}
                >
                  {taskTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Дата *</label>
                  <input
                    type="date"
                    value={taskForm.date}
                    onChange={(e) => setTaskForm({...taskForm, date: e.target.value})}
                  />
                </div>

                <div className="form-group">
                  <label>Время *</label>
                  <input
                    type="time"
                    value={taskForm.time}
                    onChange={(e) => setTaskForm({...taskForm, time: e.target.value})}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Повторение</label>
                <select
                  value={taskForm.repeat}
                  onChange={(e) => setTaskForm({...taskForm, repeat: e.target.value})}
                >
                  <option value="once">Однократно</option>
                  <option value="daily">Ежедневно</option>
                  <option value="weekly">Еженедельно</option>
                  <option value="monthly">Ежемесячно</option>
                </select>
              </div>

              <div className="form-group">
                <label>Описание</label>
                <textarea
                  value={taskForm.description}
                  onChange={(e) => setTaskForm({...taskForm, description: e.target.value})}
                  rows="3"
                  placeholder="Что должна делать эта задача?"
                />
              </div>
            </div>

            <div className="modal-footer">
              <button onClick={() => setShowAddModal(false)} className="btn btn-cancel">
                Отмена
              </button>
              <button onClick={handleCreateTask} className="btn btn-save">
                Создать задачу
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AITasks;
