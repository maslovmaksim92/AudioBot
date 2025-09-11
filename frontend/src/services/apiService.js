import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

console.log('🔗 API Service initialized');
console.log('🔗 Backend URL:', BACKEND_URL);
console.log('🔗 API URL:', API);

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging and error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.config.url}`, response.data);
    return response;
  },
  (error) => {
    console.error(`❌ API Error: ${error.config?.url}`, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const apiService = {
  // Dashboard
  getDashboardStats: async () => {
    const response = await apiClient.get('/dashboard');
    return response.data;
  },

  // Voice Chat
  sendVoiceMessage: async (message) => {
    const response = await apiClient.post('/voice/process', {
      text: message,
      user_id: 'dashboard_user'
    });
    return response.data;
  },

  // Meetings
  startMeeting: async (title) => {
    const response = await apiClient.post('/meetings/start-recording', { title });
    return response.data;
  },

  stopMeeting: async (meetingId) => {
    const response = await apiClient.post('/meetings/stop-recording', { meeting_id: meetingId });
    return response.data;
  },

  getMeetings: async () => {
    const response = await apiClient.get('/meetings');
    return response.data;
  },

  // Houses/Cleaning
  getHouses: async () => {
    const response = await apiClient.get('/cleaning/houses');
    return response.data;
  },

  getCleaningStats: async () => {
    const response = await apiClient.get('/cleaning/stats');
    return response.data;
  },

  // AI Tasks
  getAITasks: async () => {
    const response = await apiClient.get('/ai-tasks');
    return response.data;
  },

  createAITask: async (task) => {
    const response = await apiClient.post('/ai-tasks', task);
    return response.data;
  },

  // Employees
  getEmployees: async () => {
    const response = await apiClient.get('/employees');
    return response.data;
  },

  // Logs
  getLogs: async () => {
    const response = await apiClient.get('/logs');
    return response.data;
  },

  getAILogs: async () => {
    const response = await apiClient.get('/logs/ai');
    return response.data;
  },

  // Bitrix24
  testBitrix24: async () => {
    const response = await apiClient.get('/bitrix24/test');
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Self-learning
  getSelfLearningStatus: async () => {
    const response = await apiClient.get('/self-learning/status');
    return response.data;
  },

  testSelfLearning: async () => {
    const response = await apiClient.get('/self-learning/test');
    return response.data;
  },

  // Telegram
  getTelegramStatus: async () => {
    const response = await apiClient.get('/telegram/status');
    return response.data;
  }
};

export default apiService;