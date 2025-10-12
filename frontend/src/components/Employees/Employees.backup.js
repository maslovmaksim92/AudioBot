import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserPlus, 
  Search, 
  Filter, 
  Phone,
  Mail,
  MapPin,
  Calendar,
  Award,
  TrendingUp
} from 'lucide-react';

const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [brigades, setBrigades] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBrigade, setSelectedBrigade] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Симуляция загрузки данных
    setTimeout(() => {
      setEmployees([
        {
          id: 1,
          name: 'Иванов Алексей Петрович',
          position: 'Бригадир',
          brigade: 'Бригада №1',
          phone: '+7 (999) 123-45-67',
          email: 'ivanov@vasdom.ru',
          avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
          experience: '5 лет',
          rating: 4.8,
          completedJobs: 324,
          status: 'active'
        },
        {
          id: 2,
          name: 'Петрова Мария Сергеевна',
          position: 'Клинер',
          brigade: 'Бригада №1',
          phone: '+7 (999) 234-56-78',
          email: 'petrova@vasdom.ru',
          avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face',
          experience: '3 года',
          rating: 4.9,
          completedJobs: 198,
          status: 'active'
        },
        {
          id: 3,
          name: 'Сидоров Дмитрий Владимирович',
          position: 'Бригадир',
          brigade: 'Бригада №2',
          phone: '+7 (999) 345-67-89',
          email: 'sidorov@vasdom.ru',
          avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face',
          experience: '7 лет',
          rating: 4.7,
          completedJobs: 456,
          status: 'active'
        },
        {
          id: 4,
          name: 'Козлова Анна Игоревна',
          position: 'Клинер',
          brigade: 'Бригада №2',
          phone: '+7 (999) 456-78-90',
          email: 'kozlova@vasdom.ru',
          avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face',
          experience: '2 года',
          rating: 4.6,
          completedJobs: 89,
          status: 'active'
        },
        {
          id: 5,
          name: 'Николаев Сергей Александрович',
          position: 'Бригадир',
          brigade: 'Бригада №3',
          phone: '+7 (999) 567-89-01',
          email: 'nikolaev@vasdom.ru',
          avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=face',
          experience: '4 года',
          rating: 4.8,
          completedJobs: 267,
          status: 'vacation'
        }
      ]);

      setBrigades([
        { id: 1, name: 'Бригада №1', members: 8, leader: 'Иванов А.П.', efficiency: 92 },
        { id: 2, name: 'Бригада №2', members: 12, leader: 'Сидоров Д.В.', efficiency: 88 },
        { id: 3, name: 'Бригада №3', members: 10, leader: 'Николаев С.А.', efficiency: 90 },
        { id: 4, name: 'Бригада №4', members: 9, leader: 'Смирнов И.И.', efficiency: 94 },
        { id: 5, name: 'Бригада №5', members: 11, leader: 'Попов В.В.', efficiency: 87 },
        { id: 6, name: 'Бригада №6', members: 13, leader: 'Волков А.С.', efficiency: 91 },
        { id: 7, name: 'Бригада №7', members: 9, leader: 'Морозов Е.Д.', efficiency: 89 }
      ]);

      setLoading(false);
    }, 1000);
  }, []);

  const filteredEmployees = employees.filter(employee => {
    const matchesSearch = employee.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         employee.position.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesBrigade = !selectedBrigade || employee.brigade === selectedBrigade;
    return matchesSearch && matchesBrigade;
  });

  const totalEmployees = 82;
  const activeBrigades = 7;
  const averageRating = 4.8;
  const totalJobs = 1523;

  if (loading) {
    return (
      <div className="p-8 flex justify-center items-center min-h-96">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="text-lg font-medium text-gray-600">Загрузка сотрудников...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-4 animate-fade-scale">
        <h1 className="text-3xl font-bold gradient-text flex items-center justify-center">
          <Users className="w-8 h-8 mr-3 text-blue-600" />
          Управление сотрудниками
        </h1>
        <p className="text-lg text-gray-600">
          {totalEmployees} сотрудников в {activeBrigades} бригадах
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-slide-up">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-xl shadow-elegant">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">{totalEmployees}</div>
              <div className="text-blue-100 text-sm">Всего сотрудников</div>
            </div>
            <Users className="w-8 h-8 text-blue-200" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-xl shadow-elegant">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">{activeBrigades}</div>
              <div className="text-green-100 text-sm">Активных бригад</div>
            </div>
            <Award className="w-8 h-8 text-green-200" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-xl shadow-elegant">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">{averageRating}</div>
              <div className="text-purple-100 text-sm">Средний рейтинг</div>
            </div>
            <TrendingUp className="w-8 h-8 text-purple-200" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 text-white p-6 rounded-xl shadow-elegant">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">{totalJobs}</div>
              <div className="text-orange-100 text-sm">Выполнено работ</div>
            </div>
            <Calendar className="w-8 h-8 text-orange-200" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card-modern animate-slide-up">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div className="flex items-center space-x-4">
            <div className="relative flex-1 md:w-80">
              <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск сотрудников..."
                className="w-full p-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            <select
              className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white"
              value={selectedBrigade}
              onChange={(e) => setSelectedBrigade(e.target.value)}
            >
              <option value="">Все бригады</option>
              {brigades.map(brigade => (
                <option key={brigade.id} value={brigade.name}>{brigade.name}</option>
              ))}
            </select>
          </div>
          
          <button className="btn-primary flex items-center space-x-2">
            <UserPlus className="w-4 h-4" />
            <span>Добавить сотрудника</span>
          </button>
        </div>
      </div>

      {/* Brigades Overview */}
      <div className="card-modern animate-slide-up">
        <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
          <Award className="w-5 h-5 mr-2 text-blue-600" />
          Обзор бригад
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {brigades.map(brigade => (
            <div key={brigade.id} className="bg-gradient-to-br from-gray-50 to-gray-100 p-4 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">{brigade.name}</h3>
                <div className="text-sm text-gray-600">{brigade.members} чел.</div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Бригадир:</span>
                  <span className="font-medium">{brigade.leader}</span>
                </div>
                
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Эффективность:</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-green-400 to-green-600 h-2 rounded-full" 
                        style={{ width: `${brigade.efficiency}%` }}
                      ></div>
                    </div>
                    <span className="font-medium text-green-600">{brigade.efficiency}%</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Employees List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredEmployees.map((employee, index) => (
          <div 
            key={employee.id} 
            className="card-modern shadow-hover animate-slide-up"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="flex items-center space-x-4 mb-4">
              <div className="relative">
                <img
                  src={employee.avatar}
                  alt={employee.name}
                  className="w-16 h-16 rounded-full object-cover"
                />
                <div className={`absolute bottom-0 right-0 w-4 h-4 rounded-full border-2 border-white ${
                  employee.status === 'active' ? 'bg-green-500' : 
                  employee.status === 'vacation' ? 'bg-orange-500' : 'bg-gray-500'
                }`}></div>
              </div>
              
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">{employee.name}</h3>
                <p className="text-sm text-gray-600">{employee.position}</p>
                <p className="text-sm text-blue-600">{employee.brigade}</p>
              </div>
            </div>
            
            <div className="space-y-3 mb-4">
              <div className="flex items-center space-x-2 text-sm">
                <Phone className="w-4 h-4 text-gray-400" />
                <span>{employee.phone}</span>
              </div>
              <div className="flex items-center space-x-2 text-sm">
                <Mail className="w-4 h-4 text-gray-400" />
                <span>{employee.email}</span>
              </div>
              <div className="flex items-center space-x-2 text-sm">
                <Calendar className="w-4 h-4 text-gray-400" />
                <span>Опыт: {employee.experience}</span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="text-center">
                <div className="text-lg font-bold text-blue-600">{employee.completedJobs}</div>
                <div className="text-xs text-gray-500">Выполнено</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-green-600">{employee.rating}</div>
                <div className="text-xs text-gray-500">Рейтинг</div>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                employee.status === 'active' ? 'bg-green-100 text-green-800' :
                employee.status === 'vacation' ? 'bg-orange-100 text-orange-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {employee.status === 'active' ? 'Активен' :
                 employee.status === 'vacation' ? 'В отпуске' : 'Неактивен'}
              </div>
              
              <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                Подробнее
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredEmployees.length === 0 && (
        <div className="text-center py-12 animate-fade-scale">
          <div className="text-6xl mb-4">👥</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Сотрудники не найдены</h2>
          <p className="text-gray-600">Попробуйте изменить параметры поиска</p>
        </div>
      )}
    </div>
  );
};

export default Employees;