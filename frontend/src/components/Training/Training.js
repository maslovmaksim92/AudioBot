import React, { useState } from 'react';
import { 
  BookOpen, 
  Video, 
  FileText, 
  CheckCircle, 
  Clock, 
  Award,
  Play,
  Download,
  Search,
  Filter,
  TrendingUp,
  Users
} from 'lucide-react';

const Training = () => {
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const categories = [
    { id: 'all', name: 'Все курсы', count: 12 },
    { id: 'cleaning', name: 'Технология уборки', count: 5 },
    { id: 'safety', name: 'Техника безопасности', count: 3 },
    { id: 'customer', name: 'Работа с клиентами', count: 2 },
    { id: 'equipment', name: 'Оборудование', count: 2 }
  ];

  const courses = [
    {
      id: 1,
      title: 'Стандарты уборки подъездов',
      description: 'Пошаговая инструкция по уборке подъездов многоквартирных домов',
      category: 'cleaning',
      duration: '45 мин',
      progress: 100,
      type: 'video',
      status: 'completed',
      lessons: 8,
      students: 24
    },
    {
      id: 2,
      title: 'Работа с химическими средствами',
      description: 'Правила безопасности при использовании профессиональной химии',
      category: 'safety',
      duration: '30 мин',
      progress: 60,
      type: 'video',
      status: 'in_progress',
      lessons: 5,
      students: 18
    },
    {
      id: 3,
      title: 'Общение со старшими домов',
      description: 'Как эффективно взаимодействовать с представителями УК и жильцами',
      category: 'customer',
      duration: '25 мин',
      progress: 0,
      type: 'document',
      status: 'new',
      lessons: 4,
      students: 12
    },
    {
      id: 4,
      title: 'Эксплуатация поломоечных машин',
      description: 'Правильное использование и обслуживание профессионального оборудования',
      category: 'equipment',
      duration: '40 мин',
      progress: 0,
      type: 'video',
      status: 'new',
      lessons: 6,
      students: 15
    },
    {
      id: 5,
      title: 'Бизнес-процессы компании',
      description: 'Понимание workflow от лидогенерации до выполнения работ',
      category: 'cleaning',
      duration: '50 мин',
      progress: 30,
      type: 'document',
      status: 'in_progress',
      lessons: 7,
      students: 32
    }
  ];

  const filteredCourses = courses.filter(course => {
    const matchesCategory = selectedCategory === 'all' || course.category === selectedCategory;
    const matchesSearch = course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         course.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const stats = [
    { label: 'Всего курсов', value: '12', icon: BookOpen, color: 'blue' },
    { label: 'Завершено', value: '8', icon: CheckCircle, color: 'green' },
    { label: 'В процессе', value: '3', icon: Clock, color: 'yellow' },
    { label: 'Сертификаты', value: '5', icon: Award, color: 'purple' }
  ];

  const getStatusBadge = (status) => {
    const badges = {
      completed: { label: 'Завершено', class: 'bg-green-100 text-green-700' },
      in_progress: { label: 'В процессе', class: 'bg-yellow-100 text-yellow-700' },
      new: { label: 'Новый', class: 'bg-blue-100 text-blue-700' }
    };
    return badges[status] || badges.new;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <BookOpen className="w-10 h-10 text-purple-600" />
            Обучение персонала
          </h1>
          <p className="text-gray-600">
            Система обучения и развития сотрудников VasDom
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                </div>
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-${stat.color}-100`}>
                  <stat.icon className={`w-6 h-6 text-${stat.color}-600`} />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Search and Filters */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск курсов..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Category Filter */}
            <div className="flex gap-2 overflow-x-auto pb-2">
              {categories.map(category => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`px-4 py-2 rounded-xl whitespace-nowrap transition-all ${
                    selectedCategory === category.id
                      ? 'bg-purple-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {category.name} ({category.count})
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Courses Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCourses.map(course => {
            const statusBadge = getStatusBadge(course.status);
            return (
              <div 
                key={course.id} 
                className="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100 hover:shadow-xl transition-all group cursor-pointer"
              >
                {/* Course Header */}
                <div className={`h-32 bg-gradient-to-br ${
                  course.type === 'video' 
                    ? 'from-purple-400 to-indigo-500' 
                    : 'from-blue-400 to-cyan-500'
                } p-6 flex items-center justify-center relative overflow-hidden`}>
                  <div className="absolute inset-0 bg-black bg-opacity-10 group-hover:bg-opacity-0 transition-all" />
                  {course.type === 'video' ? (
                    <Video className="w-16 h-16 text-white relative z-10" />
                  ) : (
                    <FileText className="w-16 h-16 text-white relative z-10" />
                  )}
                </div>

                {/* Course Content */}
                <div className="p-6">
                  <div className="flex items-start justify-between mb-3">
                    <span className={`px-3 py-1 rounded-lg text-xs font-semibold ${statusBadge.class}`}>
                      {statusBadge.label}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {course.duration}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-purple-600 transition-colors">
                    {course.title}
                  </h3>
                  
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                    {course.description}
                  </p>

                  {/* Progress Bar */}
                  {course.progress > 0 && (
                    <div className="mb-4">
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Прогресс</span>
                        <span>{course.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-purple-500 to-indigo-600 h-2 rounded-full transition-all"
                          style={{ width: `${course.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Course Meta */}
                  <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                    <span className="flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      {course.lessons} уроков
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      {course.students} студентов
                    </span>
                  </div>

                  {/* Action Button */}
                  <button className="w-full py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl hover:from-purple-700 hover:to-indigo-700 transition-all flex items-center justify-center gap-2 group-hover:shadow-lg">
                    {course.progress > 0 ? (
                      <>
                        <Play className="w-4 h-4" />
                        Продолжить
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        Начать
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Business Process Visualization */}
        <div className="mt-8 bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-7 h-7 text-purple-600" />
              Бизнес-процессы компании
            </h2>
            <button className="flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-xl hover:bg-purple-200 transition-all">
              <Download className="w-4 h-4" />
              Скачать схему
            </button>
          </div>

          <div className="bg-gradient-to-br from-gray-50 to-purple-50 rounded-xl p-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Лидогенерация */}
              <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-blue-500">
                <h3 className="font-bold text-gray-900 mb-3 text-lg">1. Лидогенерация</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    <span>Внесение лида / автоматика из каналов</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    <span>Уведомление в ТГ группу</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    <span>Фиксирование запуска процесса</span>
                  </li>
                </ul>
              </div>

              {/* Продажа */}
              <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-green-500">
                <h3 className="font-bold text-gray-900 mb-3 text-lg">2. Продажа</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Внесение в воронку</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Подготовка КП и договоров</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Внесение в статистику</span>
                  </li>
                </ul>
              </div>

              {/* Выполнение */}
              <div className="bg-white rounded-xl p-6 shadow-md border-l-4 border-purple-500">
                <h3 className="font-bold text-gray-900 mb-3 text-lg">3. Выполнение</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                    <span>Ведение воронки работ</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                    <span>Приём отчётности и фото</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                    <span>Контроль дедлайнов</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Training;