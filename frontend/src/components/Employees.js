import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Enhanced Employees Component
const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newEmployee, setNewEmployee] = useState({
    name: '',
    position: 'cleaner',
    email: '',
    phone: '',
    hire_date: new Date().toISOString().split('T')[0],
    city: 'Калуга'
  });
  const [ratings, setRatings] = useState([]);

  useEffect(() => {
    fetchEmployees();
    fetchRatings();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/employees`);
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRatings = async () => {
    try {
      const response = await axios.get(`${API}/ratings/top-performers?limit=20`);
      setRatings(response.data.top_performers || []);
    } catch (error) {
      console.error('Error fetching ratings:', error);
    }
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/employees`, newEmployee);
      setNewEmployee({
        name: '',
        position: 'cleaner',
        email: '',
        phone: '',
        hire_date: new Date().toISOString().split('T')[0],
        city: 'Калуга'
      });
      setShowAddForm(false);
      fetchEmployees();
      alert('✅ Сотрудник добавлен успешно!');
    } catch (error) {
      console.error('Error adding employee:', error);
      alert('❌ Ошибка при добавлении сотрудника');
    }
  };

  const deleteEmployee = async (employeeId) => {
    if (!window.confirm('Удалить сотрудника?')) return;
    
    try {
      await axios.delete(`${API}/employees/${employeeId}`);
      fetchEmployees();
      alert('✅ Сотрудник удален');
    } catch (error) {
      console.error('Error deleting employee:', error);
      alert('❌ Ошибка при удалении');
    }
  };

  const rateEmployee = async (employeeId, rating) => {
    try {
      await axios.post(`${API}/ratings/employee`, {
        employee_id: employeeId,
        rating: rating,
        category: 'overall',
        comment: 'Оценка через веб-интерфейс'
      });
      fetchRatings();
      alert(`✅ Оценка ${rating}/5 поставлена!`);
    } catch (error) {
      console.error('Error rating employee:', error);
      alert('❌ Ошибка при оценке');
    }
  };

  const getPositionName = (position) => {
    const positions = {
      'general_director': 'Генеральный директор',
      'director': 'Директор',
      'accountant': 'Бухгалтер',
      'hr_manager': 'HR менеджер',
      'cleaning_manager': 'Менеджер по клинингу',
      'construction_manager': 'Менеджер по строительству',
      'architect': 'Архитектор',
      'cleaner': 'Уборщик',
      'other': 'Другое'
    };
    return positions[position] || position;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Загружаем сотрудников...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">👥 Управление сотрудниками</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
        >
          {showAddForm ? '❌ Отмена' : '➕ Добавить сотрудника'}
        </button>
      </div>

      {/* Add Employee Form */}
      {showAddForm && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">➕ Новый сотрудник</h3>
          <form onSubmit={handleAddEmployee} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Имя *</label>
              <input
                type="text"
                value={newEmployee.name}
                onChange={(e) => setNewEmployee({...newEmployee, name: e.target.value})}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
                required
                placeholder="Иван Петров"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Должность</label>
              <select
                value={newEmployee.position}
                onChange={(e) => setNewEmployee({...newEmployee, position: e.target.value})}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
              >
                <option value="cleaner">Уборщик</option>
                <option value="cleaning_manager">Менеджер по клинингу</option>
                <option value="construction_manager">Менеджер по строительству</option>
                <option value="accountant">Бухгалтер</option>
                <option value="hr_manager">HR менеджер</option>
                <option value="director">Директор</option>
                <option value="other">Другое</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
              <input
                type="email"
                value={newEmployee.email}
                onChange={(e) => setNewEmployee({...newEmployee, email: e.target.value})}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
                placeholder="ivan@vasdom.ru"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Телефон</label>
              <input
                type="tel"
                value={newEmployee.phone}
                onChange={(e) => setNewEmployee({...newEmployee, phone: e.target.value})}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
                placeholder="+7 (999) 123-45-67"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Дата приема</label>
              <input
                type="date"
                value={newEmployee.hire_date}
                onChange={(e) => setNewEmployee({...newEmployee, hire_date: e.target.value})}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Город</label>
              <select
                value={newEmployee.city}
                onChange={(e) => setNewEmployee({...newEmployee, city: e.target.value})}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500"
              >
                <option value="Калуга">Калуга</option>
                <option value="Кемерово">Кемерово</option>
              </select>
            </div>
            
            <div className="md:col-span-2">
              <button
                type="submit"
                className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition-colors"
              >
                ✅ Добавить сотрудника
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Employees List */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            📋 Список сотрудников ({employees.length})
          </h3>
        </div>
        
        {employees.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-gray-400 text-6xl mb-4">👥</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Нет сотрудников</h3>
            <p className="text-gray-600 mb-4">Добавьте первого сотрудника в систему</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600"
            >
              ➕ Добавить сотрудника
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Сотрудник
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Должность
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Город
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Контакты
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Дата приема
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Рейтинг
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {employees.map((employee) => {
                  const employeeRating = ratings.find(r => r.employee_id === employee.id);
                  return (
                    <tr key={employee.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
                              {employee.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {employee.name}
                            </div>
                            <div className="text-sm text-gray-500">
                              ID: {employee.id.slice(0, 8)}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                          {getPositionName(employee.position)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {employee.city}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div>
                          {employee.email && <div>📧 {employee.email}</div>}
                          {employee.phone && <div>📱 {employee.phone}</div>}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(employee.hire_date).toLocaleDateString('ru-RU')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          {employeeRating ? (
                            <div className="flex items-center">
                              <span className="text-yellow-400">
                                {'⭐'.repeat(Math.floor(employeeRating.average_rating))}
                              </span>
                              <span className="ml-2 text-sm text-gray-600">
                                {employeeRating.average_rating.toFixed(1)}
                              </span>
                            </div>
                          ) : (
                            <div className="flex space-x-1">
                              {[1, 2, 3, 4, 5].map(rating => (
                                <button
                                  key={rating}
                                  onClick={() => rateEmployee(employee.id, rating)}
                                  className="text-gray-300 hover:text-yellow-400 transition-colors"
                                  title={`Оценить на ${rating} звезд`}
                                >
                                  ⭐
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => deleteEmployee(employee.id)}
                          className="text-red-600 hover:text-red-900 transition-colors"
                        >
                          🗑️ Удалить
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Top Performers */}
      {ratings.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4">⭐ Лучшие сотрудники</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {ratings.slice(0, 6).map((rating, index) => (
              <div key={rating.employee_id} className="border rounded-lg p-4 bg-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{rating.employee_name || `Сотрудник ${index + 1}`}</span>
                  <span className="text-2xl">
                    {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '⭐'}
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="text-yellow-400">
                    {'⭐'.repeat(Math.floor(rating.average_rating))}
                  </span>
                  <span className="ml-2 text-sm text-gray-600">
                    {rating.average_rating.toFixed(1)} ({rating.total_ratings} оценок)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-600">Всего сотрудников</h3>
          <p className="text-3xl font-bold text-blue-600 mt-2">{employees.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-600">В Калуге</h3>
          <p className="text-3xl font-bold text-green-600 mt-2">
            {employees.filter(e => e.city === 'Калуга').length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-600">В Кемерово</h3>
          <p className="text-3xl font-bold text-purple-600 mt-2">
            {employees.filter(e => e.city === 'Кемерово').length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-600">Средний рейтинг</h3>
          <p className="text-3xl font-bold text-orange-600 mt-2">
            {ratings.length > 0 ? 
              (ratings.reduce((sum, r) => sum + r.average_rating, 0) / ratings.length).toFixed(1) : 
              '—'
            }
          </p>
        </div>
      </div>
    </div>
  );
};

export default Employees;