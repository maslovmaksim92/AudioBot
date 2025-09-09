import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, Button } from '../UI';

const Training = () => {
  const { actions } = useApp();
  const [selectedCategory, setSelectedCategory] = useState('all');

  const knowledgeBase = [
    {
      id: 1,
      title: 'Стандарты уборки подъездов',
      category: 'standards',
      description: 'Полное руководство по стандартам уборки многоквартирных домов',
      content: 'Подробное описание процедур уборки подъездов, включая мытье полов, протирку почтовых ящиков, уборку лестничных пролетов...',
      keywords: ['уборка', 'подъезд', 'стандарты', 'процедуры'],
      created_at: '2024-01-15'
    },
    {
      id: 2,
      title: 'Работа с Bitrix24 CRM',
      category: 'systems',
      description: 'Инструкция по использованию CRM системы для управления домами',
      content: 'Как создавать сделки, обновлять статусы, работать с клиентами в Bitrix24...',
      keywords: ['bitrix24', 'crm', 'сделки', 'клиенты'],
      created_at: '2024-01-20'
    },
    {
      id: 3,
      title: 'Техника безопасности',
      category: 'safety',
      description: 'Правила безопасности при выполнении клининговых работ',
      content: 'Использование средств индивидуальной защиты, работа с химическими средствами, действия в экстренных ситуациях...',
      keywords: ['безопасность', 'сиз', 'химия', 'экстренная ситуация'],
      created_at: '2024-01-10'
    },
    {
      id: 4,
      title: 'Общение с жильцами',
      category: 'communication',
      description: 'Правила взаимодействия с жильцами многоквартирных домов',
      content: 'Как вежливо общаться с жильцами, решать конфликтные ситуации, принимать жалобы и предложения...',
      keywords: ['общение', 'жильцы', 'конфликты', 'жалобы'],
      created_at: '2024-01-25'
    }
  ];

  const trainingModules = [
    {
      id: 1,
      title: 'Основы клининга',
      description: 'Базовый курс для новых сотрудников',
      duration: '2 часа',
      completed: false,
      progress: 0
    },
    {
      id: 2,
      title: 'Работа с CRM системой',
      description: 'Обучение использованию Bitrix24',
      duration: '1 час',
      completed: true,
      progress: 100
    },
    {
      id: 3,
      title: 'Техника безопасности',
      description: 'Обязательный курс по технике безопасности',
      duration: '1.5 часа',
      completed: false,
      progress: 60
    }
  ];

  const categories = [
    { id: 'all', name: 'Все категории', count: knowledgeBase.length },
    { id: 'standards', name: 'Стандарты', count: knowledgeBase.filter(item => item.category === 'standards').length },
    { id: 'systems', name: 'Системы', count: knowledgeBase.filter(item => item.category === 'systems').length },
    { id: 'safety', name: 'Безопасность', count: knowledgeBase.filter(item => item.category === 'safety').length },
    { id: 'communication', name: 'Общение', count: knowledgeBase.filter(item => item.category === 'communication').length }
  ];

  const filteredKnowledge = selectedCategory === 'all' 
    ? knowledgeBase 
    : knowledgeBase.filter(item => item.category === selectedCategory);

  const getCategoryColor = (category) => {
    switch (category) {
      case 'standards': return 'bg-blue-100 text-blue-800';
      case 'systems': return 'bg-green-100 text-green-800';
      case 'safety': return 'bg-red-100 text-red-800';
      case 'communication': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryName = (category) => {
    const categoryMap = {
      'standards': 'Стандарты',
      'systems': 'Системы', 
      'safety': 'Безопасность',
      'communication': 'Общение'
    };
    return categoryMap[category] || category;
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Обучение</h1>
          <p className="text-gray-600">База знаний и обучающие модули</p>
        </div>
        <Button variant="primary">
          ➕ Добавить материал
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Categories Sidebar */}
        <div>
          <Card title="📂 Категории">
            <div className="space-y-2">
              {categories.map(category => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    selectedCategory === category.id
                      ? 'bg-blue-100 text-blue-700'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{category.name}</span>
                    <span className="text-xs bg-gray-200 px-2 py-1 rounded-full">
                      {category.count}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </Card>

          {/* Training Progress */}
          <Card title="📊 Прогресс обучения" className="mt-4">
            <div className="space-y-3">
              {trainingModules.map(module => (
                <div key={module.id} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium truncate">{module.title}</span>
                    <span className="text-xs text-gray-500">{module.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        module.completed ? 'bg-green-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${module.progress}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Knowledge Base Content */}
        <div className="lg:col-span-3">
          {/* Knowledge Articles */}
          <div className="space-y-4">
            {filteredKnowledge.map(item => (
              <Card key={item.id} className="hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">{item.title}</h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getCategoryColor(item.category)}`}>
                    {getCategoryName(item.category)}
                  </span>
                </div>
                
                <p className="text-gray-700 mb-3">{item.description}</p>
                
                <p className="text-sm text-gray-600 mb-4 line-clamp-3">{item.content}</p>
                
                <div className="flex flex-wrap gap-2 mb-4">
                  {item.keywords.map(keyword => (
                    <span 
                      key={keyword}
                      className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                    >
                      #{keyword}
                    </span>
                  ))}
                </div>
                
                <div className="flex justify-between items-center pt-3 border-t border-gray-100">
                  <span className="text-xs text-gray-500">
                    Создано: {new Date(item.created_at).toLocaleDateString('ru-RU')}
                  </span>
                  <div className="flex space-x-2">
                    <Button size="sm" variant="primary">👁️ Читать</Button>
                    <Button size="sm" variant="secondary">✏️ Редактировать</Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {filteredKnowledge.length === 0 && (
            <Card>
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📚</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Нет материалов в этой категории</h3>
                <p className="text-gray-600">
                  Выберите другую категорию или добавьте новый материал
                </p>
              </div>
            </Card>
          )}

          {/* Training Modules */}
          <Card title="🎓 Обучающие модули" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {trainingModules.map(module => (
                <div
                  key={module.id}
                  className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-gray-900">{module.title}</h4>
                    {module.completed ? (
                      <span className="text-green-600 text-xl">✅</span>
                    ) : (
                      <span className="text-gray-400 text-xl">⏳</span>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-3">{module.description}</p>
                  
                  <div className="flex justify-between items-center text-xs text-gray-500 mb-3">
                    <span>Длительность: {module.duration}</span>
                    <span>Прогресс: {module.progress}%</span>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                    <div 
                      className={`h-2 rounded-full ${
                        module.completed ? 'bg-green-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${module.progress}%` }}
                    ></div>
                  </div>
                  
                  <Button 
                    size="sm" 
                    variant={module.completed ? 'secondary' : 'primary'}
                    className="w-full"
                  >
                    {module.completed ? '✅ Завершен' : module.progress > 0 ? '▶️ Продолжить' : '🚀 Начать'}
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Training;