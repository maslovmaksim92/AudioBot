import React from 'react';
import { Card } from '../UI';

const Tasks = () => {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Задачи</h1>
          <p className="text-gray-600">Управление задачами и заданиями</p>
        </div>
      </div>

      <Card title="📋 Список задач">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Задачи скоро появятся</h3>
          <p className="text-gray-500">
            Здесь будет система управления задачами для бригад и контроль их выполнения.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Tasks;