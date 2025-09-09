// API Service - Centralized HTTP client
// Backend URL from environment variable
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://audiobot-qci2.onrender.com';

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

  // Houses and cleaning
  getCleaningHouses: async (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });
    
    const url = `${BACKEND_URL}/api/cleaning/houses${params.toString() ? '?' + params.toString() : ''}`;
    const response = await fetch(url);
    return response.json();
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