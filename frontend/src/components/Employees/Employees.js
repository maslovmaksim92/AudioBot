import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { apiService } from '../../services/apiService';
import { Card, Button, LoadingSpinner } from '../UI';

const Employees = () => {
  const { actions } = useApp();
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const response = await apiService.getEmployees();
      if (response.status === 'success') {
        setEmployees(response.employees || []);
        actions.addNotification({
          type: 'success',
          message: `Загружено ${response.employees?.length || 0} сотрудников`
        });
      }
    } catch (error) {
      console.error('❌ Error fetching employees:', error);
      // Fallback данные для демонстрации
      const mockEmployees = [
        { id: 1, name: 'Анна Петровна', brigade: '1 бригада', position: 'Бригадир', phone: '+7 (900) 123-45-67', district: 'Центральный' },
        { id: 2, name: 'Мария Иванова', brigade: '1 бригада', position: 'Уборщица', phone: '+7 (900) 123-45-68', district: 'Центральный' },
        { id: 3, name: 'Ольга Сидорова', brigade: '2 бригада', position: 'Бригадир', phone: '+7 (900) 123-45-69', district: 'Никитинский' },
        { id: 4, name: 'Елена Козлова', brigade: '2 бригада', position: 'Уборщица', phone: '+7 (900) 123-45-70', district: 'Никитинский' },
        { id: 5, name: 'Татьяна Морозова', brigade: '3 бригада', position: 'Бригадир', phone: '+7 (900) 123-45-71', district: 'Жилетово' }
      ];
      setEmployees(mockEmployees);
      actions.addNotification({
        type: 'warning',
        message: 'Показаны демо-данные сотрудников'
      });
    } finally {
      setLoading(false);
    }
  };

  const brigades = [
    { id: 1, name: '1 бригада', district: 'Центральный', houses: 58 },
    { id: 2, name: '2 бригада', district: 'Никитинский', houses: 62 },
    { id: 3, name: '3 бригада', district: 'Жилетово', houses: 45 },
    { id: 4, name: '4 бригада', district: 'Северный', houses: 67 },
    { id: 5, name: '5 бригада', district: 'Пригород', houses: 54 },
    { id: 6, name: '6 бригада', district: 'Окраины', houses: 62 }
  ];

  const groupedEmployees = employees.reduce((acc, employee) => {
    const brigade = employee.brigade || 'Без бригады';
    if (!acc[brigade]) {
      acc[brigade] = [];
    }
    acc[brigade].push(employee);
    return acc;
  }, {});

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Сотрудники</h1>
          <p className="text-gray-600">Управление бригадами и сотрудниками</p>
        </div>
        <Button onClick={fetchEmployees} loading={loading}>
          🔄 Обновить
        </Button>
      </div>

      {/* Brigades Overview */}
      <Card title="👥 Обзор бригад" className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {brigades.map(brigade => (
            <div
              key={brigade.id}
              className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-gray-900">{brigade.name}</h3>
                <span className="text-sm text-gray-500">{brigade.houses} домов</span>
              </div>
              <p className="text-sm text-gray-600">{brigade.district} район</p>
              <div className="mt-2 text-xs text-gray-500">
                Сотрудников: {groupedEmployees[brigade.name]?.length || 0}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Employees List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" text="Загрузка сотрудников..." />
        </div>
      ) : Object.keys(groupedEmployees).length > 0 ? (
        <div className="space-y-6">
          {Object.entries(groupedEmployees).map(([brigade, brigadeEmployees]) => (
            <Card key={brigade} title={`${brigade} (${brigadeEmployees.length} чел.)`}>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {brigadeEmployees.map(employee => (
                  <div
                    key={employee.id}
                    className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{employee.name}</h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        employee.position === 'Бригадир' 
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {employee.position}
                      </span>
                    </div>
                    
                    <div className="space-y-1 text-sm text-gray-600">
                      {employee.phone && (
                        <div className="flex items-center">
                          <span className="mr-2">📞</span>
                          <a href={`tel:${employee.phone}`} className="hover:text-blue-600">
                            {employee.phone}
                          </a>
                        </div>
                      )}
                      
                      {employee.district && (
                        <div className="flex items-center">
                          <span className="mr-2">🏢</span>
                          <span>{employee.district} район</span>
                        </div>
                      )}
                      
                      {employee.email && (
                        <div className="flex items-center">
                          <span className="mr-2">📧</span>
                          <a href={`mailto:${employee.email}`} className="hover:text-blue-600 truncate">
                            {employee.email}
                          </a>
                        </div>
                      )}
                    </div>
                    
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-gray-500">ID: {employee.id}</span>
                        <div className="flex space-x-1">
                          <Button size="sm" variant="ghost" className="p-1">📞</Button>
                          <Button size="sm" variant="ghost" className="p-1">✉️</Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <div className="text-center py-12">
            <div className="text-6xl mb-4">👥</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Нет данных о сотрудниках</h3>
            <p className="text-gray-600">
              Данные о сотрудниках будут загружены из системы управления
            </p>
          </div>
        </Card>
      )}

      {/* Statistics */}
      <Card title="📊 Статистика" className="mt-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">82</div>
            <div className="text-sm text-gray-600">Всего сотрудников</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">6</div>
            <div className="text-sm text-gray-600">Бригад</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">348</div>
            <div className="text-sm text-gray-600">Домов в работе</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">13.7</div>
            <div className="text-sm text-gray-600">Сотр./бригада</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Employees;