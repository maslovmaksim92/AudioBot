import React from 'react';
import { Card, StatCard } from '../UI';

const Employees = () => {
  const employeeStats = [
    { title: 'Общее количество', value: 82, color: 'blue', subtitle: 'активных сотрудников' },
    { title: 'Бригады', value: 6, color: 'green', subtitle: 'рабочих бригад' },
    { title: 'Центральный', value: 14, color: 'purple', subtitle: 'сотрудников' },
    { title: 'Никитинский', value: 15, color: 'yellow', subtitle: 'сотрудников' },
    { title: 'Жилетово', value: 12, color: 'red', subtitle: 'сотрудников' },
    { title: 'Остальные', value: 41, color: 'gray', subtitle: 'сотрудников' }
  ];

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Сотрудники</h1>
          <p className="text-gray-600">Управление бригадами и персоналом</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {employeeStats.map((stat, index) => (
          <StatCard
            key={index}
            title={stat.title}
            value={stat.value}
            icon={<span className="text-2xl">👥</span>}
            color={stat.color}
            subtitle={stat.subtitle}
          />
        ))}
      </div>

      <Card title="👥 Управление персоналом">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">👥</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Управление сотрудниками</h3>
          <p className="text-gray-500">
            Здесь будет подробная информация о сотрудниках, их графиках работы, достижениях и задачах.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Employees;