import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Trash2, Save, X, Plus } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

const BrigadeManagement = () => {
  const [brigades, setBrigades] = useState({});
  const [allUsers, setAllUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingBrigade, setEditingBrigade] = useState(null);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Загружаем всех пользователей
      const usersResponse = await fetch(`${BACKEND_URL}/api/users`);
      const usersData = await usersResponse.json();
      const users = usersData.users || [];
      
      setAllUsers(users);
      
      // Группируем пользователей по бригадам
      const brigadesMap = {};
      for (let i = 1; i <= 7; i++) {
        brigadesMap[i] = {
          number: i,
          members: users.filter(u => String(u.brigade_number) === String(i))
        };
      }
      
      setBrigades(brigadesMap);
    } catch (error) {
      console.error('Error loading data:', error);
      showNotification('Ошибка загрузки данных', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const handleAddMember = async (brigadeNumber, userId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/${userId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brigade_number: String(brigadeNumber) })
      });
      
      if (response.ok) {
        showNotification('Сотрудник добавлен в бригаду', 'success');
        loadData();
      } else {
        showNotification('Ошибка при добавлении сотрудника', 'error');
      }
    } catch (error) {
      console.error('Error adding member:', error);
      showNotification('Ошибка при добавлении сотрудника', 'error');
    }
  };

  const handleRemoveMember = async (userId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/${userId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brigade_number: null })
      });
      
      if (response.ok) {
        showNotification('Сотрудник удален из бригады', 'success');
        loadData();
      } else {
        showNotification('Ошибка при удалении сотрудника', 'error');
      }
    } catch (error) {
      console.error('Error removing member:', error);
      showNotification('Ошибка при удалении сотрудника', 'error');
    }
  };

  const getAvailableUsers = (brigadeNumber) => {
    return allUsers.filter(u => !u.brigade_number || String(u.brigade_number) !== String(brigadeNumber));
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Загрузка данных бригад...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg ${
          notification.type === 'success' ? 'bg-green-500' : 'bg-red-500'
        } text-white`}>
          {notification.message}
        </div>
      )}

      {/* Бригады */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {Object.values(brigades).map((brigade) => (
          <div key={brigade.number} className="bg-white rounded-2xl shadow-lg border-2 border-gray-200 overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-4 text-white">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <Users className="w-6 h-6" />
                  Бригада {brigade.number}
                </h3>
                <span className="bg-white/20 px-3 py-1 rounded-full text-sm font-medium">
                  {brigade.members.length} чел.
                </span>
              </div>
            </div>

            {/* Members List */}
            <div className="p-4">
              {brigade.members.length > 0 ? (
                <div className="space-y-2 mb-4">
                  {brigade.members.map((member) => (
                    <div key={member.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full flex items-center justify-center text-white text-sm font-bold">
                          {(member.full_name || 'U').charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {member.full_name || 'Без имени'}
                          </p>
                          <p className="text-xs text-gray-500 truncate">{member.email}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveMember(member.id)}
                        className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Удалить из бригады"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-400">
                  <Users className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">Нет сотрудников</p>
                </div>
              )}

              {/* Add Member */}
              {editingBrigade === brigade.number ? (
                <div className="border-t pt-4">
                  <div className="max-h-48 overflow-y-auto space-y-2 mb-3">
                    {getAvailableUsers(brigade.number).map((user) => (
                      <button
                        key={user.id}
                        onClick={() => {
                          handleAddMember(brigade.number, user.id);
                          setEditingBrigade(null);
                        }}
                        className="w-full flex items-center gap-2 p-2 hover:bg-blue-50 rounded-lg transition-colors text-left"
                      >
                        <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center text-white text-xs font-bold">
                          {(user.full_name || 'U').charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">{user.full_name || 'Без имени'}</p>
                          <p className="text-xs text-gray-500 truncate">{user.email}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => setEditingBrigade(null)}
                    className="w-full py-2 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    <X className="w-4 h-4" />
                    Отмена
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setEditingBrigade(brigade.number)}
                  className="w-full py-2 px-4 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Добавить сотрудника
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Unassigned Users */}
      {allUsers.filter(u => !u.brigade_number).length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-200 p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Users className="w-6 h-6 text-gray-600" />
            Сотрудники без бригады ({allUsers.filter(u => !u.brigade_number).length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allUsers.filter(u => !u.brigade_number).map((user) => (
              <div key={user.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-10 h-10 bg-gradient-to-r from-gray-400 to-gray-500 rounded-full flex items-center justify-center text-white font-bold">
                  {(user.full_name || 'U').charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{user.full_name || 'Без имени'}</p>
                  <p className="text-sm text-gray-500 truncate">{user.email}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BrigadeManagement;
