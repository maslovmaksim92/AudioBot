import React from 'react';
import { Card, StatCard } from '../UI';

const Works = () => {
  const houseStats = [
    { title: 'Центральный', value: 58, color: 'blue' },
    { title: 'Никитинский', value: 62, color: 'green' },
    { title: 'Жилетово', value: 45, color: 'purple' },
    { title: 'Северный', value: 71, color: 'yellow' },
    { title: 'Пригород', value: 53, color: 'red' },
    { title: 'Окраины', value: 59, color: 'gray' }
  ];

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Дома</h1>
          <p className="text-gray-600">Управление домами по районам Калуги</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {houseStats.map((stat, index) => (
          <StatCard
            key={index}
            title={stat.title}
            value={stat.value}
            icon={<span className="text-2xl">🏘️</span>}
            color={stat.color}
            subtitle="домов в районе"
          />
        ))}
      </div>

      <Card title="🏠 Управление домами">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🏠</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Управление домами</h3>
          <p className="text-gray-500">
            Здесь будет подробная информация о домах, их состоянии, графике уборки и ответственных бригадах.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Works;