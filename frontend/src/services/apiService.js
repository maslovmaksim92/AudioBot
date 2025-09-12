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

  startMeetingRecording: async (title) => {
    const response = await fetch(`${BACKEND_URL}/api/meetings/start-recording`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ title }),
    });
    return response.json();
  },

  stopMeetingRecording: async (meetingId) => {
    const response = await fetch(`${BACKEND_URL}/api/meetings/stop-recording`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ meeting_id: meetingId }),
    });
    return response.json();
  },

  // Houses and cleaning - ОБНОВЛЕНО для загрузки 490 домов
  getCleaningHouses: async (filters = {}) => {
    // Используем новый endpoint для 490 домов из правильной категории Bitrix24
    const url = `${BACKEND_URL}/api/cleaning/houses-490`;
    console.log('🏠 Fetching houses from:', url);
    
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      console.log('✅ Houses data received:', data);
      return data;
    } catch (error) {
      console.error('❌ Houses API error:', error);
      // Fallback к принудительной загрузки
      try {
        console.log('🔄 Trying force houses endpoint...');
        const forceResponse = await fetch(`${BACKEND_URL}/api/force-houses-490`);
        const forceData = await forceResponse.json();
        console.log('🔥 Force houses result:', forceData);
        
        // Если принудительная загрузка успешна, повторяем основной запрос
        if (forceData.status === '✅ FORCE SUCCESS') {
          const retryResponse = await fetch(`${BACKEND_URL}/api/cleaning/houses-490`);
          return retryResponse.json();
        }
        
        return { status: 'error', message: 'Failed to load houses', houses: [] };
      } catch (fallbackError) {
        console.error('❌ Fallback failed:', fallbackError);
        return { status: 'error', message: 'All endpoints failed', houses: [] };
      }
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
  }
};

export { apiService };