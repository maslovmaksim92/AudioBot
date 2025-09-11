import React, { createContext, useContext, useReducer, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://audiobot-qci2.onrender.com';

// Initial State
const initialState = {
  currentSection: 'general',
  isMenuCollapsed: false,
  loading: false,
  dashboardStats: {
    employees: 82,
    houses: 50,
    entrances: 166,
    apartments: 5344,
    floors: 432,
    meetings: 0
  },
  apiStatus: 'connected',
  notifications: [],
  user: {
    name: 'Администратор',
    role: 'admin'
  }
};

// Action Types
const actionTypes = {
  SET_CURRENT_SECTION: 'SET_CURRENT_SECTION',
  TOGGLE_MENU: 'TOGGLE_MENU',
  SET_LOADING: 'SET_LOADING',
  SET_DASHBOARD_STATS: 'SET_DASHBOARD_STATS',
  SET_API_STATUS: 'SET_API_STATUS',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION'
};

// Reducer
const appReducer = (state, action) => {
  switch (action.type) {
    case actionTypes.SET_CURRENT_SECTION:
      return { ...state, currentSection: action.payload };
    
    case actionTypes.TOGGLE_MENU:
      return { ...state, isMenuCollapsed: !state.isMenuCollapsed };
    
    case actionTypes.SET_LOADING:
      return { ...state, loading: action.payload };
    
    case actionTypes.SET_DASHBOARD_STATS:
      return { ...state, dashboardStats: { ...state.dashboardStats, ...action.payload } };
    
    case actionTypes.SET_API_STATUS:
      return { ...state, apiStatus: action.payload };
    
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
};

// Context
const AppContext = createContext();

// Provider Component
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Actions
  const actions = {
    setCurrentSection: (section) => {
      dispatch({ type: actionTypes.SET_CURRENT_SECTION, payload: section });
    },
    
    toggleMenu: () => {
      dispatch({ type: actionTypes.TOGGLE_MENU });
    },
    
    setLoading: (loading) => {
      dispatch({ type: actionTypes.SET_LOADING, payload: loading });
    },
    
    fetchDashboardStats: async () => {
      try {
        dispatch({ type: actionTypes.SET_LOADING, payload: true });
        
        const response = await fetch(`${BACKEND_URL}/api/dashboard`);
        if (response.ok) {
          const data = await response.json();
          dispatch({ type: actionTypes.SET_DASHBOARD_STATS, payload: data });
          dispatch({ type: actionTypes.SET_API_STATUS, payload: 'connected' });
        } else {
          throw new Error('Failed to fetch dashboard stats');
        }
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
        dispatch({ type: actionTypes.SET_API_STATUS, payload: 'error' });
        actions.addNotification({
          type: 'error',
          title: 'Ошибка подключения',
          message: 'Не удалось загрузить статистику дашборда'
        });
      } finally {
        dispatch({ type: actionTypes.SET_LOADING, payload: false });
      }
    },
    
    addNotification: (notification) => {
      dispatch({ type: actionTypes.ADD_NOTIFICATION, payload: notification });
      
      // Auto-remove after 5 seconds
      setTimeout(() => {
        actions.removeNotification(notification.id);
      }, 5000);
    },
    
    removeNotification: (id) => {
      dispatch({ type: actionTypes.REMOVE_NOTIFICATION, payload: id });
    }
  };

  // Load dashboard stats on mount
  useEffect(() => {
    actions.fetchDashboardStats();
  }, []);

  return (
    <AppContext.Provider value={{ state, actions, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};

// Hook to use context
export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};