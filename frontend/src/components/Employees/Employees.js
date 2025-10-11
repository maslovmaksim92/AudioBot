import React, { useState, useEffect } from 'react';
import { Users, List, Shield, Plus, Edit2, Trash2, Phone, Mail, Briefcase, X, Save, Search } from 'lucide-react';
import BrigadeManagement from './BrigadeManagement';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

const Employees = () => {
  const [activeTab, setActiveTab] = useState('employees');
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create' or 'edit'
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [positionFilter, setPositionFilter] = useState('');
  const [positions, setPositions] = useState([]);
  const [notification, setNotification] = useState(null);
  
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    phone: '',
    position: '',
    brigade_number: '',
    password: ''
  });

  useEffect(() => {
    if (activeTab === 'employees') {
      loadEmployees();
      loadPositions();
    }
  }, [activeTab, searchQuery, positionFilter]);

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const loadPositions = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/employees/positions/list`);
      const data = await response.json();
      setPositions(data || []);
    } catch (error) {
      console.error('Error loading positions:', error);
    }
  };

  const loadEmployees = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (positionFilter) params.append('position', positionFilter);
      
      const response = await fetch(`${BACKEND_URL}/api/employees?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to load employees');
      
      const data = await response.json();
      setEmployees(data || []);
    } catch (error) {
      console.error('Error loading employees:', error);
      showNotification('Ошибка при загрузке сотрудников', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (mode, employee = null) => {
    setModalMode(mode);
    setSelectedEmployee(employee);
    
    if (mode === 'edit' && employee) {
      setFormData({
        email: employee.email,
        full_name: employee.full_name,
        phone: employee.phone || '',
        position: employee.position || '',
        brigade_number: employee.brigade_number || '',
        password: '' // не показываем пароль при редактировании
      });
    } else {
      setFormData({
        email: '',
        full_name: '',
        phone: '',
        position: '',
        brigade_number: '',
        password: ''
      });
    }
    
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedEmployee(null);
    setFormData({
      email: '',
      full_name: '',
      phone: '',
      position: '',
      brigade_number: '',
      password: ''
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      let response;
      
      if (modalMode === 'create') {
        // Создание нового сотрудника
        if (!formData.password || formData.password.length < 6) {
          showNotification('Пароль должен содержать минимум 6 символов', 'error');
          return;
        }
        
        response = await fetch(`${BACKEND_URL}/api/employees`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
      } else {
        // Редактирование существующего сотрудника
        const updateData = {
          full_name: formData.full_name,
          phone: formData.phone,
          position: formData.position || null,
          brigade_number: formData.brigade_number || null
        };
        
        response = await fetch(`${BACKEND_URL}/api/employees/${selectedEmployee.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateData)
        });
      }
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Operation failed');
      }
      
      showNotification(
        modalMode === 'create' ? 'Сотрудник успешно создан' : 'Данные сотрудника обновлены',
        'success'
      );
      
      handleCloseModal();
      loadEmployees();
    } catch (error) {
      console.error('Error saving employee:', error);
      showNotification(error.message || 'Ошибка при сохранении данных', 'error');
    }
  };

  const handleDelete = async (employeeId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этого сотрудника?')) {
      return;
    }
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/employees/${employeeId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to delete employee');
      
      showNotification('Сотрудник успешно удален', 'success');
      loadEmployees();
    } catch (error) {
      console.error('Error deleting employee:', error);
      showNotification('Ошибка при удалении сотрудника', 'error');
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg ${
          notification.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        }`}>
          {notification.message}
        </div>
      )}

      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Users className="w-8 h-8 mr-3 text-blue-600"/>
          Сотрудники
        </h1>
      </div>

      {/* Вкладки */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('employees')}
            className={`pb-4 px-2 font-medium transition-colors relative ${
              activeTab === 'employees'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <List className="w-5 h-5" />
              Сотрудники
            </div>
          </button>
          <button
            onClick={() => setActiveTab('brigades')}
            className={`pb-4 px-2 font-medium transition-colors relative ${
              activeTab === 'brigades'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Управление бригадами
            </div>
          </button>
        </nav>
      </div>

      {/* Вкладка "Сотрудники" */}
      {activeTab === 'employees' && (
        <div>
          {/* Фильтры и кнопка добавления */}
          <div className="mb-6 flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="flex flex-1 gap-4 w-full md:w-auto">
              {/* Поиск */}
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Поиск по ФИО или email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              {/* Фильтр по должности */}
              <select
                value={positionFilter}
                onChange={(e) => setPositionFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Все должности</option>
                {positions.map(pos => (
                  <option key={pos.value} value={pos.value}>{pos.label}</option>
                ))}
              </select>
            </div>
            
            {/* Кнопка добавления */}
            <button
              onClick={() => handleOpenModal('create')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              Добавить сотрудника
            </button>
          </div>

          {/* Список сотрудников */}
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Загрузка сотрудников...</p>
            </div>
          ) : employees.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 text-lg">Сотрудников не найдено</p>
              <p className="text-gray-500 text-sm mt-2">Добавьте первого сотрудника, нажав кнопку выше</p>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Сотрудник
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Контакты
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Должность
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Бригада
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Статус
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Действия
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {employees.map((employee) => (
                    <tr key={employee.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                            {(employee.full_name || 'U').charAt(0).toUpperCase()}
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">{employee.full_name}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900 flex items-center gap-1">
                          <Mail className="w-4 h-4 text-gray-400" />
                          {employee.email}
                        </div>
                        {employee.phone && (
                          <div className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                            <Phone className="w-4 h-4 text-gray-400" />
                            {employee.phone}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {employee.position_display ? (
                          <span className="px-3 py-1 inline-flex items-center gap-1 text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                            <Briefcase className="w-3 h-3" />
                            {employee.position_display}
                          </span>
                        ) : (
                          <span className="text-sm text-gray-400">Не указана</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {employee.brigade_number || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          employee.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {employee.is_active ? 'Активен' : 'Неактивен'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => handleOpenModal('edit', employee)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                          title="Редактировать"
                        >
                          <Edit2 className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleDelete(employee.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Удалить"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Вкладка "Управление бригадами" */}
      {activeTab === 'brigades' && (
        <BrigadeManagement />
      )}

      {/* Модальное окно создания/редактирования */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">
                {modalMode === 'create' ? 'Добавить сотрудника' : 'Редактировать сотрудника'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6">
              <div className="space-y-4">
                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email *
                  </label>
                  <input
                    type="email"
                    required
                    disabled={modalMode === 'edit'}
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="example@vasdom.ru"
                  />
                </div>

                {/* ФИО */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ФИО *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Иванов Иван Иванович"
                  />
                </div>

                {/* Телефон */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Телефон
                  </label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="+7 (999) 123-45-67"
                  />
                </div>

                {/* Должность */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Должность
                  </label>
                  <select
                    value={formData.position}
                    onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Не указана</option>
                    {positions.map(pos => (
                      <option key={pos.value} value={pos.value}>{pos.label}</option>
                    ))}
                  </select>
                </div>

                {/* Номер бригады */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Номер бригады
                  </label>
                  <input
                    type="text"
                    value={formData.brigade_number}
                    onChange={(e) => setFormData({ ...formData, brigade_number: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="1"
                  />
                </div>

                {/* Пароль (только при создании) */}
                {modalMode === 'create' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Пароль *
                    </label>
                    <input
                      type="password"
                      required
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Минимум 6 символов"
                      minLength="6"
                    />
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="flex gap-3 mt-6 pt-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                >
                  <Save className="w-5 h-5" />
                  {modalMode === 'create' ? 'Создать' : 'Сохранить'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Employees;