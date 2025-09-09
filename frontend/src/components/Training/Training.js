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
    &lt;div className="p-6"&gt;
      &lt;div className="flex justify-between items-center mb-6"&gt;
        &lt;div&gt;
          &lt;h1 className="text-3xl font-bold text-gray-900"&gt;Обучение&lt;/h1&gt;
          &lt;p className="text-gray-600"&gt;База знаний и обучающие модули&lt;/p&gt;
        &lt;/div&gt;
        &lt;Button variant="primary"&gt;
          ➕ Добавить материал
        &lt;/Button&gt;
      &lt;/div&gt;

      &lt;div className="grid grid-cols-1 lg:grid-cols-4 gap-6"&gt;
        {/* Categories Sidebar */}
        &lt;div&gt;
          &lt;Card title="📂 Категории"&gt;
            &lt;div className="space-y-2"&gt;
              {categories.map(category => (
                &lt;button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                    selectedCategory === category.id
                      ? 'bg-blue-100 text-blue-700'
                      : 'hover:bg-gray-100'
                  }`}
                &gt;
                  &lt;div className="flex justify-between items-center"&gt;
                    &lt;span className="text-sm font-medium"&gt;{category.name}&lt;/span&gt;
                    &lt;span className="text-xs bg-gray-200 px-2 py-1 rounded-full"&gt;
                      {category.count}
                    &lt;/span&gt;
                  &lt;/div&gt;
                &lt;/button&gt;
              ))}
            &lt;/div&gt;
          &lt;/Card&gt;

          {/* Training Progress */}
          &lt;Card title="📊 Прогресс обучения" className="mt-4"&gt;
            &lt;div className="space-y-3"&gt;
              {trainingModules.map(module => (
                &lt;div key={module.id} className="space-y-2"&gt;
                  &lt;div className="flex justify-between items-center"&gt;
                    &lt;span className="text-sm font-medium truncate"&gt;{module.title}&lt;/span&gt;
                    &lt;span className="text-xs text-gray-500"&gt;{module.progress}%&lt;/span&gt;
                  &lt;/div&gt;
                  &lt;div className="w-full bg-gray-200 rounded-full h-2"&gt;
                    &lt;div 
                      className={`h-2 rounded-full ${
                        module.completed ? 'bg-green-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${module.progress}%` }}
                    &gt;&lt;/div&gt;
                  &lt;/div&gt;
                &lt;/div&gt;
              ))}
            &lt;/div&gt;
          &lt;/Card&gt;
        &lt;/div&gt;

        {/* Knowledge Base Content */}
        &lt;div className="lg:col-span-3"&gt;
          {/* Knowledge Articles */}
          &lt;div className="space-y-4"&gt;
            {filteredKnowledge.map(item => (
              &lt;Card key={item.id} className="hover:shadow-lg transition-shadow"&gt;
                &lt;div className="flex justify-between items-start mb-3"&gt;
                  &lt;h3 className="text-lg font-semibold text-gray-900"&gt;{item.title}&lt;/h3&gt;
                  &lt;span className={`px-3 py-1 rounded-full text-xs font-medium ${getCategoryColor(item.category)}`}&gt;
                    {getCategoryName(item.category)}
                  &lt;/span&gt;
                &lt;/div&gt;
                
                &lt;p className="text-gray-700 mb-3"&gt;{item.description}&lt;/p&gt;
                
                &lt;p className="text-sm text-gray-600 mb-4 line-clamp-3"&gt;{item.content}&lt;/p&gt;
                
                &lt;div className="flex flex-wrap gap-2 mb-4"&gt;
                  {item.keywords.map(keyword => (
                    &lt;span 
                      key={keyword}
                      className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                    &gt;
                      #{keyword}
                    &lt;/span&gt;
                  ))}
                &lt;/div&gt;
                
                &lt;div className="flex justify-between items-center pt-3 border-t border-gray-100"&gt;
                  &lt;span className="text-xs text-gray-500"&gt;
                    Создано: {new Date(item.created_at).toLocaleDateString('ru-RU')}
                  &lt;/span&gt;
                  &lt;div className="flex space-x-2"&gt;
                    &lt;Button size="sm" variant="primary"&gt;👁️ Читать&lt;/Button&gt;
                    &lt;Button size="sm" variant="secondary"&gt;✏️ Редактировать&lt;/Button&gt;
                  &lt;/div&gt;
                &lt;/div&gt;
              &lt;/Card&gt;
            ))}
          &lt;/div&gt;

          {filteredKnowledge.length === 0 && (
            &lt;Card&gt;
              &lt;div className="text-center py-12"&gt;
                &lt;div className="text-6xl mb-4"&gt;📚&lt;/div&gt;
                &lt;h3 className="text-lg font-medium text-gray-900 mb-2"&gt;Нет материалов в этой категории&lt;/h3&gt;
                &lt;p className="text-gray-600"&gt;
                  Выберите другую категорию или добавьте новый материал
                &lt;/p&gt;
              &lt;/div&gt;
            &lt;/Card&gt;
          )}

          {/* Training Modules */}
          &lt;Card title="🎓 Обучающие модули" className="mt-6"&gt;
            &lt;div className="grid grid-cols-1 md:grid-cols-2 gap-4"&gt;
              {trainingModules.map(module => (
                &lt;div
                  key={module.id}
                  className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                &gt;
                  &lt;div className="flex justify-between items-start mb-2"&gt;
                    &lt;h4 className="font-medium text-gray-900"&gt;{module.title}&lt;/h4&gt;
                    {module.completed ? (
                      &lt;span className="text-green-600 text-xl"&gt;✅&lt;/span&gt;
                    ) : (
                      &lt;span className="text-gray-400 text-xl"&gt;⏳&lt;/span&gt;
                    )}
                  &lt;/div&gt;
                  
                  &lt;p className="text-sm text-gray-600 mb-3"&gt;{module.description}&lt;/p&gt;
                  
                  &lt;div className="flex justify-between items-center text-xs text-gray-500 mb-3"&gt;
                    &lt;span&gt;Длительность: {module.duration}&lt;/span&gt;
                    &lt;span&gt;Прогресс: {module.progress}%&lt;/span&gt;
                  &lt;/div&gt;
                  
                  &lt;div className="w-full bg-gray-200 rounded-full h-2 mb-3"&gt;
                    &lt;div 
                      className={`h-2 rounded-full ${
                        module.completed ? 'bg-green-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${module.progress}%` }}
                    &gt;&lt;/div&gt;
                  &lt;/div&gt;
                  
                  &lt;Button 
                    size="sm" 
                    variant={module.completed ? 'secondary' : 'primary'}
                    className="w-full"
                  &gt;
                    {module.completed ? '✅ Завершен' : module.progress > 0 ? '▶️ Продолжить' : '🚀 Начать'}
                  &lt;/Button&gt;
                &lt;/div&gt;
              ))}
            &lt;/div&gt;
          &lt;/Card&gt;
        &lt;/div&gt;
      &lt;/div&gt;
    &lt;/div&gt;
  );
};

export default Training;