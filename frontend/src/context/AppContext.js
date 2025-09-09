import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { apiService } from '../services/apiService';

// Initial state
const initialState = {
  currentSection: 'general',
  isMenuCollapsed: false,
  dashboardStats: {
    employees: 82,
    houses: 348,
    entrances: 1131,
    apartments: 36232,
    floors: 2958,
    meetings: 0,
    ai_tasks: 0
  },
  loading: false,
  apiStatus: 'connecting',
  user: null,
  notifications: []
};

// Action types
export const actionTypes = {
  SET_CURRENT_SECTION: 'SET_CURRENT_SECTION',
  TOGGLE_MENU: 'TOGGLE_MENU',
  SET_DASHBOARD_STATS: 'SET_DASHBOARD_STATS',
  SET_LOADING: 'SET_LOADING',
  SET_API_STATUS: 'SET_API_STATUS',
  SET_USER: 'SET_USER',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION'
};

// Reducer
function appReducer(state, action) {
  switch (action.type) {
    case actionTypes.SET_CURRENT_SECTION:
      return { ...state, currentSection: action.payload };
    
    case actionTypes.TOGGLE_MENU:
      return { ...state, isMenuCollapsed: !state.isMenuCollapsed };
    
    case actionTypes.SET_DASHBOARD_STATS:
      return { ...state, dashboardStats: action.payload };
    
    case actionTypes.SET_LOADING:
      return { ...state, loading: action.payload };
    
    case actionTypes.SET_API_STATUS:
      return { ...state, apiStatus: action.payload };
    
    case actionTypes.SET_USER:
      return { ...state, user: action.payload };
    
    case actionTypes.ADD_NOTIFICATION:
      return { 
        ...state, 
        notifications: [...state.notifications, { id: Date.now(), ...action.payload }]
      };
    
    case actionTypes.REMOVE_NOTIFICATION:
      return { 
        ...state, 
        notifications: state.notifications.filter(n => n.id !== action.payload)
      };
    
    default:
      return state;
  }
}

// Context
const AppContext = createContext();

// Provider component
export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Actions
  const actions = {
    setCurrentSection: (section) => 
      dispatch({ type: actionTypes.SET_CURRENT_SECTION, payload: section }),
    
    toggleMenu: () => 
      dispatch({ type: actionTypes.TOGGLE_MENU }),
    
    setDashboardStats: (stats) => 
      dispatch({ type: actionTypes.SET_DASHBOARD_STATS, payload: stats }),
    
    setLoading: (loading) => 
      dispatch({ type: actionTypes.SET_LOADING, payload: loading }),
    
    setApiStatus: (status) => 
      dispatch({ type: actionTypes.SET_API_STATUS, payload: status }),
    
    setUser: (user) => 
      dispatch({ type: actionTypes.SET_USER, payload: user }),
    
    addNotification: (notification) => 
      dispatch({ type: actionTypes.ADD_NOTIFICATION, payload: notification }),
    
    removeNotification: (id) => 
      dispatch({ type: actionTypes.REMOVE_NOTIFICATION, payload: id }),

    // Dashboard data fetching
    fetchDashboardStats: async () => {
      actions.setLoading(true);
      try {
        const data = await apiService.getDashboardStats();
        actions.setDashboardStats(data.stats);
        actions.setApiStatus('connected');
        actions.addNotification({
          type: 'success',
          message: `✅ Данные обновлены: ${data.stats.houses} домов`
        });
      } catch (error) {
        console.error('❌ Dashboard data error:', error);
        actions.setApiStatus('error');
        actions.addNotification({
          type: 'error',
          message: 'Ошибка загрузки данных дашборда'
        });
      } finally {
        actions.setLoading(false);
      }
    }
  };

  // Auto-refresh effect
  useEffect(() => {
    console.log('🚀 VasDom AudioBot App Context initialized');
    
    // Initial data load
    actions.fetchDashboardStats();
    
    // Auto-refresh every 2 minutes
    const interval = setInterval(() => {
      console.log('🔄 Auto-refresh dashboard...');
      actions.fetchDashboardStats();
    }, 2 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <AppContext.Provider value={{ state, actions }}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook to use the context
export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}