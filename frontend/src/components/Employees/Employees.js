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
    &lt;div className="p-6"&gt;
      &lt;div className="flex justify-between items-center mb-6"&gt;
        &lt;div&gt;
          &lt;h1 className="text-3xl font-bold text-gray-900"&gt;Сотрудники&lt;/h1&gt;
          &lt;p className="text-gray-600"&gt;Управление бригадами и сотрудниками&lt;/p&gt;
        &lt;/div&gt;
        &lt;Button onClick={fetchEmployees} loading={loading}&gt;
          🔄 Обновить
        &lt;/Button&gt;
      &lt;/div&gt;

      {/* Brigades Overview */}
      &lt;Card title="👥 Обзор бригад" className="mb-6"&gt;
        &lt;div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"&gt;
          {brigades.map(brigade => (
            &lt;div
              key={brigade.id}
              className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
            &gt;
              &lt;div className="flex justify-between items-start mb-2"&gt;
                &lt;h3 className="font-semibold text-gray-900"&gt;{brigade.name}&lt;/h3&gt;
                &lt;span className="text-sm text-gray-500"&gt;{brigade.houses} домов&lt;/span&gt;
              &lt;/div&gt;
              &lt;p className="text-sm text-gray-600"&gt;{brigade.district} район&lt;/p&gt;
              &lt;div className="mt-2 text-xs text-gray-500"&gt;
                Сотрудников: {groupedEmployees[brigade.name]?.length || 0}
              &lt;/div&gt;
            &lt;/div&gt;
          ))}
        &lt;/div&gt;
      &lt;/Card&gt;

      {/* Employees List */}
      {loading ? (
        &lt;div className="flex justify-center py-12"&gt;
          &lt;LoadingSpinner size="lg" text="Загрузка сотрудников..." /&gt;
        &lt;/div&gt;
      ) : Object.keys(groupedEmployees).length > 0 ? (
        &lt;div className="space-y-6"&gt;
          {Object.entries(groupedEmployees).map(([brigade, brigadeEmployees]) => (
            &lt;Card key={brigade} title={`${brigade} (${brigadeEmployees.length} чел.)`}&gt;
              &lt;div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"&gt;
                {brigadeEmployees.map(employee => (
                  &lt;div
                    key={employee.id}
                    className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                  &gt;
                    &lt;div className="flex items-start justify-between mb-2"&gt;
                      &lt;h4 className="font-medium text-gray-900"&gt;{employee.name}&lt;/h4&gt;
                      &lt;span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        employee.position === 'Бригадир' 
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}&gt;
                        {employee.position}
                      &lt;/span&gt;
                    &lt;/div&gt;
                    
                    &lt;div className="space-y-1 text-sm text-gray-600"&gt;
                      {employee.phone && (
                        &lt;div className="flex items-center"&gt;
                          &lt;span className="mr-2"&gt;📞&lt;/span&gt;
                          &lt;a href={`tel:${employee.phone}`} className="hover:text-blue-600"&gt;
                            {employee.phone}
                          &lt;/a&gt;
                        &lt;/div&gt;
                      )}
                      
                      {employee.district && (
                        &lt;div className="flex items-center"&gt;
                          &lt;span className="mr-2"&gt;🏢&lt;/span&gt;
                          &lt;span&gt;{employee.district} район&lt;/span&gt;
                        &lt;/div&gt;
                      )}
                      
                      {employee.email && (
                        &lt;div className="flex items-center"&gt;
                          &lt;span className="mr-2"&gt;📧&lt;/span&gt;
                          &lt;a href={`mailto:${employee.email}`} className="hover:text-blue-600 truncate"&gt;
                            {employee.email}
                          &lt;/a&gt;
                        &lt;/div&gt;
                      )}
                    &lt;/div&gt;
                    
                    &lt;div className="mt-3 pt-3 border-t border-gray-100"&gt;
                      &lt;div className="flex justify-between items-center"&gt;
                        &lt;span className="text-xs text-gray-500"&gt;ID: {employee.id}&lt;/span&gt;
                        &lt;div className="flex space-x-1"&gt;
                          &lt;Button size="sm" variant="ghost" className="p-1"&gt;📞&lt;/Button&gt;
                          &lt;Button size="sm" variant="ghost" className="p-1"&gt;✉️&lt;/Button&gt;
                        &lt;/div&gt;
                      &lt;/div&gt;
                    &lt;/div&gt;
                  &lt;/div&gt;
                ))}
              &lt;/div&gt;
            &lt;/Card&gt;
          ))}
        &lt;/div&gt;
      ) : (
        &lt;Card&gt;
          &lt;div className="text-center py-12"&gt;
            &lt;div className="text-6xl mb-4"&gt;👥&lt;/div&gt;
            &lt;h3 className="text-lg font-medium text-gray-900 mb-2"&gt;Нет данных о сотрудниках&lt;/h3&gt;
            &lt;p className="text-gray-600"&gt;
              Данные о сотрудниках будут загружены из системы управления
            &lt;/p&gt;
          &lt;/div&gt;
        &lt;/Card&gt;
      )}

      {/* Statistics */}
      &lt;Card title="📊 Статистика" className="mt-6"&gt;
        &lt;div className="grid grid-cols-2 md:grid-cols-4 gap-4"&gt;
          &lt;div className="text-center"&gt;
            &lt;div className="text-2xl font-bold text-blue-600"&gt;82&lt;/div&gt;
            &lt;div className="text-sm text-gray-600"&gt;Всего сотрудников&lt;/div&gt;
          &lt;/div&gt;
          &lt;div className="text-center"&gt;
            &lt;div className="text-2xl font-bold text-green-600"&gt;6&lt;/div&gt;
            &lt;div className="text-sm text-gray-600"&gt;Бригад&lt;/div&gt;
          &lt;/div&gt;
          &lt;div className="text-center"&gt;
            &lt;div className="text-2xl font-bold text-purple-600"&gt;348&lt;/div&gt;
            &lt;div className="text-sm text-gray-600"&gt;Домов в работе&lt;/div&gt;
          &lt;/div&gt;
          &lt;div className="text-center"&gt;
            &lt;div className="text-2xl font-bold text-orange-600"&gt;13.7&lt;/div&gt;
            &lt;div className="text-sm text-gray-600"&gt;Сотр./бригада&lt;/div&gt;
          &lt;/div&gt;
        &lt;/div&gt;
      &lt;/Card&gt;
    &lt;/div&gt;
  );
};

export default Employees;