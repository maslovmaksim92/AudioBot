import React, { useState } from 'react';
import { Sparkles, Loader, CheckCircle } from 'lucide-react';
import { taskService } from '../../services/taskService';

const AITaskGenerator = () => {
  const [context, setContext] = useState({
    description: '',
    count: 3
  });
  const [generatedTasks, setGeneratedTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    if (!context.description.trim()) {
      setError('Пожалуйста, опишите контекст для генерации задач');
      return;
    }

    setLoading(true);
    setError('');
    setGeneratedTasks([]);

    try {
      const result = await taskService.generateAITasks(context);
      setGeneratedTasks(result.tasks);
    } catch (err) {
      setError('Ошибка генерации задач: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const presets = [
    {
      title: '📋 Еженедельная отчётность',
      description: 'Создать задачи для еженедельной отчётности по всем объектам: проверка выполненных работ, актов, оплат, рекламаций'
    },
    {
      title: '🏠 Новый объект',
      description: 'Создать задачи для организации работы на новом объекте: осмотр, составление графика, выбор бригады, первая уборка'
    },
    {
      title: '🔧 Рекламация',
      description: 'Создать задачи для обработки рекламации: связаться с клиентом, повторная уборка, подписание акта, анализ причин'
    },
    {
      title: '📞 Обзвон клиентов',
      description: 'Создать задачи для обзвона клиентов: сбор обратной связи, выявление проблем, предложение дополнительных услуг'
    }
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2">🤖 AI Генератор задач</h1>
        <p className="text-gray-600">
          Опишите контекст или ситуацию, и AI сгенерирует подходящие задачи с приоритетами и описаниями
        </p>
      </div>

      {/* Пресеты */}
      <div className="mb-6">
        <h3 className="font-medium mb-3">Быстрые сценарии:</h3>
        <div className="grid grid-cols-2 gap-3">
          {presets.map((preset, index) => (
            <button
              key={index}
              onClick={() => setContext({...context, description: preset.description})}
              className="p-4 text-left bg-white border rounded-lg hover:border-blue-500 hover:shadow-md transition-all"
            >
              <div className="font-medium mb-1">{preset.title}</div>
              <div className="text-sm text-gray-600">{preset.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Форма генерации */}
      <div className="bg-white rounded-lg border p-6 mb-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Опишите контекст или ситуацию *
            </label>
            <textarea
              value={context.description}
              onChange={(e) => setContext({...context, description: e.target.value})}
              className="w-full px-3 py-2 border rounded-lg"
              rows="4"
              placeholder="Например: У нас новый дом на Пушкина 10, 3 подъезда, 5 этажей. Нужно организовать работу, выбрать бригаду и провести первую уборку"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Количество задач
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={context.count}
              onChange={(e) => setContext({...context, count: parseInt(e.target.value)})}
              className="w-32 px-3 py-2 border rounded-lg"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Генерация задач...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Сгенерировать задачи
              </>
            )}
          </button>
        </div>
      </div>

      {/* Результаты */}
      {generatedTasks.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <h3 className="text-lg font-semibold">
              Сгенерировано {generatedTasks.length} задач
            </h3>
          </div>

          <div className="space-y-4">
            {generatedTasks.map((task, index) => (
              <div key={task.id} className="bg-white border rounded-lg p-5 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-lg font-semibold">#{index + 1}</span>
                      <h4 className="text-lg font-semibold">{task.title}</h4>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        task.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                        task.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                        task.priority === 'medium' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {task.priority === 'urgent' ? '🔥 Срочно' :
                         task.priority === 'high' ? '⚡ Высокий' :
                         task.priority === 'medium' ? '📌 Средний' :
                         '📋 Низкий'}
                      </span>
                    </div>
                    <p className="text-gray-700 mb-3">{task.description}</p>
                    {task.ai_reasoning && (
                      <div className="bg-purple-50 border border-purple-200 rounded p-3">
                        <div className="text-sm font-medium text-purple-900 mb-1">
                          💡 Обоснование AI:
                        </div>
                        <div className="text-sm text-purple-800">
                          {task.ai_reasoning}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg text-center">
            <p className="text-green-800">
              ✅ Все задачи успешно созданы и добавлены в список задач
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default AITaskGenerator;
