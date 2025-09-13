// API Service - Centralized HTTP client
// Backend URL from environment variable
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

console.log('🔗 API Service initialized with backend URL:', BACKEND_URL);

const apiService = {
  // Dashboard statistics
  getDashboardStats: async () => {
    const response = await fetch(`${BACKEND_URL}/api/dashboard`);
    return response.json();
  },

  // Voice processing
  processVoice: async (text, userId = 'user') => {
    const response = await fetch(`${BACKEND_URL}/api/voice/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, user_id: userId }),
    });
    return response.json();
  },

  // Meetings
  getMeetings: async () => {
    const response = await fetch(`${BACKEND_URL}/api/meetings`);
    return response.json();
  },

  startMeeting: async (title) => {
    const response = await fetch(`${BACKEND_URL}/api/meetings/start-recording`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title }),
    });
    return response.json();
  },

  stopMeeting: async (meetingId) => {
    const response = await fetch(`${BACKEND_URL}/api/meetings/stop-recording`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ meeting_id: meetingId }),
    });
    return response.json();
  },

  // Aliases for backward compatibility
  startMeetingRecording: async (title) => {
    return apiService.startMeeting(title);
  },

  stopMeetingRecording: async (meetingId) => {
    return apiService.stopMeeting(meetingId);
  },

  // Houses and cleaning - УНИФИЦИРОВАННЫЙ для загрузки 490 домов
  getCleaningHouses: async (filters = {}, onProgress = null) => {
    const url = `${BACKEND_URL}/api/cleaning/houses-490`;
    console.log('🏠 Fetching 490 houses from:', url);
    
    // Прогресс-бар callback
    if (onProgress) onProgress({ stage: 'connecting', message: 'Подключение к серверу...', progress: 10 });
    
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        timeout: 30000 // 30 seconds timeout
      });
      
      if (onProgress) onProgress({ stage: 'receiving', message: 'Получение данных от Bitrix24...', progress: 50 });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Houses data received:', {
        status: data.status,
        total: data.total,
        houses_count: data.houses?.length || 0,
        source: data.source
      });
      
      if (onProgress) onProgress({ stage: 'processing', message: `Обработка ${data.houses?.length || 0} домов...`, progress: 90 });
      
      // Проверяем корректность данных
      if (!data.houses || !Array.isArray(data.houses)) {
        throw new Error('Invalid data format: houses array not found');
      }
      
      if (onProgress) onProgress({ stage: 'complete', message: `✅ Загружено ${data.houses.length} домов из 490`, progress: 100 });
      
      return data;
    } catch (error) {
      console.error('❌ Houses API error:', error);
      if (onProgress) onProgress({ stage: 'error', message: `❌ Ошибка: ${error.message}`, progress: 0 });
      
      // Возвращаем структурированную ошибку
      return { 
        status: 'error', 
        message: error.message, 
        houses: [],
        total: 0,
        error_details: error.toString()
      };
    }
  },

  getBrigades: async () => {
    const response = await fetch(`${BACKEND_URL}/api/cleaning/brigades`);
    return response.json();
  },

  // System logs
  getLogs: async () => {
    const response = await fetch(`${BACKEND_URL}/api/logs`);
    return response.json();
  },

  // Health check
  getHealth: async () => {
    const response = await fetch(`${BACKEND_URL}/api/health`);
    return response.json();
  },

  // Voice message processing (alias for processVoice)
  sendVoiceMessage: async (text, userId = 'user') => {
    return apiService.processVoice(text, userId);
  }
};

export { apiService };