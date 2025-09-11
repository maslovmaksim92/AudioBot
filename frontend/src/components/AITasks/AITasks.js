import React from 'react';
import { Card } from '../UI';

const AITasks = () => {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Задачи</h1>
          <p className="text-gray-600">Умные задачи с ИИ анализом</p>
        </div>
      </div>

      <Card title="🧠 AI Задачи">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🧠</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">AI задачи в разработке</h3>
          <p className="text-gray-500">
            Здесь будут умные задачи, автоматически создаваемые на основе анализа данных и машинного обучения.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default AITasks;