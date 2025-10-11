/**
 * Task Service - API для работы с задачами
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

export const taskService = {
  // Получить список задач с фильтрами
  async getTasks(filters = {}) {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.priority) params.append('priority', filters.priority);
    if (filters.assigned_to_id) params.append('assigned_to_id', filters.assigned_to_id);
    if (filters.house_id) params.append('house_id', filters.house_id);
    if (filters.ai_proposed !== undefined) params.append('ai_proposed', filters.ai_proposed);
    if (filters.skip) params.append('skip', filters.skip);
    if (filters.limit) params.append('limit', filters.limit);

    const response = await fetch(`${BACKEND_URL}/api/tasks?${params}`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch tasks: ${response.statusText}`);
    }
    
    return await response.json();
  },

  // Получить задачу по ID
  async getTask(taskId) {
    const response = await fetch(`${BACKEND_URL}/api/tasks/${taskId}`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch task: ${response.statusText}`);
    }
    
    return await response.json();
  },

  // Создать задачу
  async createTask(taskData) {
    const response = await fetch(`${BACKEND_URL}/api/tasks/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(taskData)
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create task: ${response.statusText}`);
    }
    
    return await response.json();
  },

  // Обновить задачу
  async updateTask(taskId, updates) {
    const response = await fetch(`${BACKEND_URL}/api/tasks/${taskId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(updates)
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update task: ${response.statusText}`);
    }
    
    return await response.json();
  },

  // Удалить задачу
  async deleteTask(taskId) {
    const response = await fetch(`${BACKEND_URL}/api/tasks/${taskId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete task: ${response.statusText}`);
    }
    
    return await response.json();
  },

  // Обновить чеклист
  async updateChecklist(taskId, checklist) {
    const response = await fetch(`${BACKEND_URL}/api/tasks/${taskId}/checklist`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(checklist)
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update checklist: ${response.statusText}`);
    }
    
    return await response.json();
  },

  // Обновить mind-map
  async updateMindmap(taskId, mindmap) {
    const response = await fetch(`${BACKEND_URL}/api/tasks/${taskId}/mindmap`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(mindmap)
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update mindmap: ${response.statusText}`);
    }
    
    return await response.json();
  },

  // Генерация AI задач
  async generateAITasks(context) {
    const response = await fetch(`${BACKEND_URL}/api/tasks/ai/generate`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(context)
    });
    
    if (!response.ok) {
      throw new Error(`Failed to generate AI tasks: ${response.statusText}`);
    }
    
    return await response.json();
  },

  // Получить задачи из Bitrix24
  async getBitrixTasks() {
    const response = await fetch(`${BACKEND_URL}/api/tasks/bitrix/list`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch Bitrix tasks: ${response.statusText}`);
    }
    
    return await response.json();
  }
};
