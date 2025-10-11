import React, { useState } from 'react';
import { 
  Truck, 
  MapPin, 
  Calendar, 
  Clock,
  Users,
  Building2,
  CheckCircle,
  AlertCircle,
  Navigation,
  Filter,
  Download
} from 'lucide-react';

const Logistics = () => {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedBrigade, setSelectedBrigade] = useState('all');

  const brigades = [
    { id: 'all', name: 'Все бригады', count: 42 },
    { id: '1', name: 'Бригада 1', count: 6, driver: 'Иванов И.', status: 'active' },
    { id: '2', name: 'Бригада 2', count: 7, driver: 'Петров П.', status: 'active' },
    { id: '3', name: 'Бригада 3', count: 5, driver: 'Сидоров С.', status: 'active' },
    { id: '4', name: 'Бригада 4', count: 8, driver: 'Козлов К.', status: 'active' },
    { id: '5', name: 'Бригада 5', count: 6, driver: 'Новиков Н.', status: 'break' },
    { id: '6', name: 'Бригада 6', count: 5, driver: 'Морозов М.', status: 'active' },
    { id: '7', name: 'Бригада 7', count: 5, driver: 'Волков В.', status: 'active' }
  ];

  const routes = [
    {
      id: 1,
      brigade: '1',
      driver: 'Иванов И.',
      houses: [
        { id: 101, address: 'Билибина 6', time: '09:00', status: 'completed', entrances: 4 },
        { id: 102, address: 'Кубяка 5', time: '10:30', status: 'completed', entrances: 3 },
        { id: 103, address: 'Ленина 42', time: '12:00', status: 'in_progress', entrances: 5 },
        { id: 104, address: 'Мира 18', time: '14:00', status: 'pending', entrances: 4 },
        { id: 105, address: 'Победы 23', time: '15:30', status: 'pending', entrances: 3 },
        { id: 106, address: 'Советская 15', time: '17:00', status: 'pending', entrances: 4 }
      ],
      totalDistance: '28 км',
      estimatedTime: '8 ч',
      currentProgress: 40
    },
    {
      id: 2,
      brigade: '2',
      driver: 'Петров П.',
      houses: [
        { id: 201, address: 'Гагарина 10', time: '09:00', status: 'completed', entrances: 3 },
        { id: 202, address: 'Космонавтов 7', time: '10:00', status: 'completed', entrances: 4 },
        { id: 203, address: 'Шоссейная 45', time: '11:30', status: 'completed', entrances: 5 },
        { id: 204, address: 'Заводская 12', time: '13:00', status: 'in_progress', entrances: 3 },
        { id: 205, address: 'Молодежная 8', time: '14:30', status: 'pending', entrances: 4 },
        { id: 206, address: 'Строителей 19', time: '16:00', status: 'pending', entrances: 3 },
        { id: 207, address: 'Парковая 3', time: '17:30', status: 'pending', entrances: 2 }
      ],
      totalDistance: '32 км',
      estimatedTime: '9 ч',
      currentProgress: 55
    },
    {
      id: 3,
      brigade: '3',
      driver: 'Сидоров С.',
      houses: [
        { id: 301, address: 'Центральная 25', time: '09:30', status: 'completed', entrances: 6 },
        { id: 302, address: 'Лесная 14', time: '11:00', status: 'completed', entrances: 3 },
        { id: 303, address: 'Речная 8', time: '12:30', status: 'in_progress', entrances: 4 },
        { id: 304, address: 'Полевая 16', time: '14:00', status: 'pending', entrances: 5 },
        { id: 305, address: 'Садовая 11', time: '16:00', status: 'pending', entrances: 3 }
      ],
      totalDistance: '25 км',
      estimatedTime: '7 ч',
      currentProgress: 45
    }
  ];

  const filteredRoutes = selectedBrigade === 'all' 
    ? routes 
    : routes.filter(r => r.brigade === selectedBrigade);

  const getStatusBadge = (status) => {
    const badges = {
      completed: { label: 'Выполнено', icon: CheckCircle, class: 'bg-green-100 text-green-700' },
      in_progress: { label: 'В процессе', icon: Clock, class: 'bg-blue-100 text-blue-700' },
      pending: { label: 'Ожидание', icon: AlertCircle, class: 'bg-gray-100 text-gray-700' }
    };
    return badges[status] || badges.pending;
  };

  const stats = [
    { label: 'Домов сегодня', value: '42', icon: Building2, color: 'blue' },
    { label: 'Выполнено', value: '18', icon: CheckCircle, color: 'green' },
    { label: 'В процессе', value: '3', icon: Clock, color: 'yellow' },
    { label: 'Осталось', value: '21', icon: AlertCircle, color: 'orange' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-50 via-white to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <Truck className="w-10 h-10 text-cyan-600" />
            Логистика и маршруты
          </h1>
          <p className="text-gray-600">
            Планирование и отслеживание маршрутов бригад
          </p>
        </div>

        {/* Stats */}
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

        {/* Filters */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Date Picker */}
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">Дата</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Brigade Filter */}
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">Бригада</label>
              <select
                value={selectedBrigade}
                onChange={(e) => setSelectedBrigade(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
              >
                {brigades.map(brigade => (
                  <option key={brigade.id} value={brigade.id}>
                    {brigade.name} ({brigade.count} домов)
                  </option>
                ))}
              </select>
            </div>

            {/* Actions */}
            <div className="flex items-end gap-2">
              <button className="px-6 py-3 bg-cyan-600 text-white rounded-xl hover:bg-cyan-700 transition-all flex items-center gap-2">
                <Download className="w-5 h-5" />
                Экспорт
              </button>
            </div>
          </div>
        </div>

        {/* Routes */}
        <div className="space-y-6">
          {filteredRoutes.map(route => (
            <div key={route.id} className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
              {/* Route Header */}
              <div className="bg-gradient-to-r from-cyan-500 to-blue-600 p-6 text-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-white bg-opacity-20 rounded-xl flex items-center justify-center">
                      <Truck className="w-8 h-8" />
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold">Бригада {route.brigade}</h3>
                      <p className="text-cyan-100 flex items-center gap-2">
                        <Users className="w-4 h-4" />
                        Водитель: {route.driver}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="flex items-center gap-4 text-cyan-100">
                      <div className="flex items-center gap-1">
                        <Navigation className="w-4 h-4" />
                        <span>{route.totalDistance}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{route.estimatedTime}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-4">
                  <div className="flex justify-between text-sm text-cyan-100 mb-2">
                    <span>Прогресс маршрута</span>
                    <span>{route.currentProgress}%</span>
                  </div>
                  <div className="w-full bg-white bg-opacity-20 rounded-full h-3">
                    <div 
                      className="bg-white h-3 rounded-full transition-all duration-500"
                      style={{ width: `${route.currentProgress}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Houses List */}
              <div className="p-6">
                <div className="space-y-3">
                  {route.houses.map((house, index) => {
                    const status = getStatusBadge(house.status);
                    return (
                      <div 
                        key={house.id}
                        className={`flex items-center justify-between p-4 rounded-xl border-2 transition-all ${
                          house.status === 'completed' 
                            ? 'bg-green-50 border-green-200' 
                            : house.status === 'in_progress'
                            ? 'bg-blue-50 border-blue-200 shadow-md'
                            : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div className="flex items-center gap-4">
                          {/* Order Number */}
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold ${
                            house.status === 'completed'
                              ? 'bg-green-200 text-green-700'
                              : house.status === 'in_progress'
                              ? 'bg-blue-200 text-blue-700'
                              : 'bg-gray-200 text-gray-700'
                          }`}>
                            {index + 1}
                          </div>

                          {/* Address */}
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <MapPin className="w-4 h-4 text-gray-400" />
                              <span className="font-semibold text-gray-900">{house.address}</span>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-gray-600">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {house.time}
                              </span>
                              <span className="flex items-center gap-1">
                                <Building2 className="w-3 h-3" />
                                {house.entrances} подъездов
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Status Badge */}
                        <div className={`px-4 py-2 rounded-lg flex items-center gap-2 ${status.class}`}>
                          <status.icon className="w-4 h-4" />
                          <span className="font-medium">{status.label}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Logistics;