import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, Check } from 'lucide-react';
import { taskService } from '../../services/taskService';

const ChecklistModal = ({ task, onClose, onUpdate }) => {
  const [checklist, setChecklist] = useState([]);
  const [newItemText, setNewItemText] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (task && task.checklist) {
      setChecklist(task.checklist);
    }
  }, [task]);

  const addItem = () => {
    if (!newItemText.trim()) return;

    const newItem = {
      id: Date.now().toString(),
      text: newItemText.trim(),
      done: false
    };

    setChecklist([...checklist, newItem]);
    setNewItemText('');
  };

  const toggleItem = (itemId) => {
    setChecklist(checklist.map(item =>
      item.id === itemId ? { ...item, done: !item.done } : item
    ));
  };

  const deleteItem = (itemId) => {
    setChecklist(checklist.filter(item => item.id !== itemId));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await taskService.updateChecklist(task.id, checklist);
      const updatedTask = await taskService.getTask(task.id);
      onUpdate(updatedTask);
    } catch (error) {
      alert('Ошибка сохранения чеклиста: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const completedCount = checklist.filter(item => item.done).length;
  const totalCount = checklist.length;
  const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Заголовок */}
        <div className="p-6 border-b">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Чеклист задачи</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <p className="text-gray-600 mb-4">{task.title}</p>

          {/* Прогресс-бар */}
          <div className="mb-2">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Прогресс</span>
              <span className="font-medium">
                {completedCount} / {totalCount} ({Math.round(progress)}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Список чеклиста */}
        <div className="p-6">
          <div className="space-y-2 mb-4">
            {checklist.map(item => (
              <div
                key={item.id}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <button
                  onClick={() => toggleItem(item.id)}
                  className={`w-6 h-6 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                    item.done
                      ? 'bg-green-500 border-green-500'
                      : 'border-gray-300 hover:border-green-500'
                  }`}
                >
                  {item.done && <Check className="w-4 h-4 text-white" />}
                </button>
                <span
                  className={`flex-1 ${
                    item.done ? 'line-through text-gray-500' : ''
                  }`}
                >
                  {item.text}
                </span>
                <button
                  onClick={() => deleteItem(item.id)}
                  className="p-2 hover:bg-red-100 rounded text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}

            {checklist.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <p>Чеклист пуст</p>
                <p className="text-sm mt-1">Добавьте первый пункт ниже</p>
              </div>
            )}
          </div>

          {/* Добавить новый пункт */}
          <div className="flex gap-2">
            <input
              type="text"
              value={newItemText}
              onChange={(e) => setNewItemText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addItem()}
              className="flex-1 px-3 py-2 border rounded-lg"
              placeholder="Добавить пункт..."
            />
            <button
              onClick={addItem}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Добавить
            </button>
          </div>
        </div>

        {/* Кнопки */}
        <div className="flex justify-end gap-3 p-6 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            Отмена
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChecklistModal;