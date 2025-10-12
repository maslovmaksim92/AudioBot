import React, { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Home, CheckCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

const CleaningCalendar = () => {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [cleanings, setCleanings] = useState({});
  const [selectedDate, setSelectedDate] = useState(null);
  const [housesOnDate, setHousesOnDate] = useState([]);
  const [loading, setLoading] = useState(true);

  const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

  useEffect(() => {
    loadCleaningSchedule();
  }, [currentMonth]);

  const loadCleaningSchedule = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/cleaning/houses?limit=1000`);
      const data = await response.json();
      
      // Парсим все даты уборок
      const cleaningMap = {};
      
      (data.houses || []).forEach(house => {
        if (house.cleaning_dates) {
          Object.values(house.cleaning_dates).forEach(period => {
            if (period.dates) {
              period.dates.forEach(date => {
                if (!cleaningMap[date]) {
                  cleaningMap[date] = [];
                }
                cleaningMap[date].push({
                  id: house.id,
                  address: house.address || house.title,
                  brigade: house.brigade_name || house.brigade,
                  type: period.type
                });
              });
            }
          });
        }
      });
      
      setCleanings(cleaningMap);
    } catch (error) {
      console.error('Error loading cleaning schedule:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1; // Monday = 0
    
    return { daysInMonth, startingDayOfWeek };
  };

  const formatDate = (year, month, day) => {
    const m = String(month + 1).padStart(2, '0');
    const d = String(day).padStart(2, '0');
    return `${year}-${m}-${d}`;
  };

  const handleDateClick = (dateStr) => {
    setSelectedDate(dateStr);
    setHousesOnDate(cleanings[dateStr] || []);
  };

  const previousMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1));
  };

  const { daysInMonth, startingDayOfWeek } = getDaysInMonth(currentMonth);
  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <CalendarIcon className="w-10 h-10 text-blue-600" />
            Календарь уборок
          </h1>
          <p className="text-gray-600">График уборок на {months[month]} {year}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Calendar */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
              {/* Month Navigation */}
              <div className="flex items-center justify-between mb-6">
                <button
                  onClick={previousMonth}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <ChevronLeft className="w-6 h-6 text-gray-600" />
                </button>
                
                <h2 className="text-2xl font-bold text-gray-900">
                  {months[month]} {year}
                </h2>
                
                <button
                  onClick={nextMonth}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <ChevronRight className="w-6 h-6 text-gray-600" />
                </button>
              </div>

              {/* Calendar Grid */}
              <div className="grid grid-cols-7 gap-2">
                {/* Day Headers */}
                {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map(day => (
                  <div key={day} className="text-center font-semibold text-gray-600 py-2 text-sm">
                    {day}
                  </div>
                ))}

                {/* Empty cells for alignment */}
                {Array(startingDayOfWeek).fill(null).map((_, index) => (
                  <div key={`empty-${index}`} className="aspect-square" />
                ))}

                {/* Days */}
                {Array(daysInMonth).fill(null).map((_, index) => {
                  const day = index + 1;
                  const dateStr = formatDate(year, month, day);
                  const housesCount = cleanings[dateStr]?.length || 0;
                  const isToday = dateStr === new Date().toISOString().split('T')[0];
                  const isSelected = dateStr === selectedDate;

                  return (
                    <button
                      key={day}
                      onClick={() => handleDateClick(dateStr)}
                      className={`aspect-square p-2 rounded-lg transition-all relative
                        ${isToday ? 'bg-blue-100 ring-2 ring-blue-500' : ''}
                        ${isSelected ? 'bg-blue-500 text-white' : 'hover:bg-gray-50'}
                        ${housesCount > 0 && !isSelected ? 'bg-green-50' : ''}
                      `}
                    >
                      <div className="text-sm font-medium">{day}</div>
                      {housesCount > 0 && (
                        <div className={`absolute bottom-1 left-1/2 transform -translate-x-1/2 text-xs
                          ${isSelected ? 'text-white' : 'text-green-600'}
                        `}>
                          {housesCount} 🏠
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Legend */}
              <div className="mt-6 flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-blue-100 border-2 border-blue-500 rounded" />
                  <span className="text-gray-600">Сегодня</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-50 rounded" />
                  <span className="text-gray-600">Есть уборки</span>
                </div>
              </div>
            </div>
          </div>

          {/* Selected Date Info */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 sticky top-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Home className="w-6 h-6 text-blue-600" />
                {selectedDate ? `Уборки на ${new Date(selectedDate).toLocaleDateString('ru-RU')}` : 'Выберите дату'}
              </h3>

              {loading ? (
                <div className="text-center py-8 text-gray-400">
                  Загрузка...
                </div>
              ) : selectedDate && housesOnDate.length > 0 ? (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {housesOnDate.map((house, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors"
                    >
                      <div className="font-medium text-gray-900 text-sm mb-1">
                        {house.address}
                      </div>
                      {house.brigade && (
                        <div className="text-xs text-gray-600 mb-1">
                          👷 {house.brigade}
                        </div>
                      )}
                      {house.type && (
                        <div className="text-xs text-gray-500 line-clamp-2">
                          {house.type}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : selectedDate ? (
                <div className="text-center py-8 text-gray-400">
                  На эту дату уборок нет
                </div>
              ) : (
                <div className="text-center py-8 text-gray-400">
                  Выберите дату на календаре
                </div>
              )}

              {selectedDate && housesOnDate.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="text-sm font-semibold text-gray-900">
                    Всего: {housesOnDate.length} домов
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CleaningCalendar;
