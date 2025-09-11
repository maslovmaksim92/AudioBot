import React from 'react';
import { Card } from '../UI';

const Meetings = () => {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Планерки</h1>
          <p className="text-gray-600">Записи совещаний и планёрок</p>
        </div>
      </div>

      <Card title="🎤 Записи планерок">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🎤</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Планерки скоро появятся</h3>
          <p className="text-gray-500">
            Здесь будут отображаться записи планерок и совещаний с автоматической транскрипцией и анализом.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Meetings;