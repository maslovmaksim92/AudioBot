import React, { useState, useEffect } from 'react';
import { Users, TrendingUp, Calendar as CalendarIcon, Home, Layers, ArrowUp, PieChart as PieChartIcon } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

const BrigadeStats = () => {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [brigadeData, setBrigadeData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBrigade, setSelectedBrigade] = useState(null);
  const [dailyStats, setDailyStats] = useState({});
  const [brigadeDistribution, setBrigadeDistribution] = useState([]);

  const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

  useEffect(() => {
    console.log('[BrigadeStats] Month changed, reloading stats...');
    loadBrigadeStats();
  }, [currentMonth]);

  const loadBrigadeStats = async () => {
    try {
      setLoading(true);
      setError(null);
      setBrigadeData([]);
      setDailyStats({});
      setBrigadeDistribution([]);
      console.log('[BrigadeStats] Loading stats for month:', currentMonth.toISOString());
      
      // Загружаем распределение домов по бригадам
      const distributionResponse = await fetch(`${BACKEND_URL}/api/dashboard/houses-by-brigade`);
      const distributionData = await distributionResponse.json();
      setBrigadeDistribution(distributionData.data || []);
      
      const response = await fetch(`${BACKEND_URL}/api/cleaning/houses?limit=1000`);
      const data = await response.json();
      
      console.log('[BrigadeStats] Loaded', data.houses?.length || 0, 'houses');
      
      // Определяем выбранный МЕСЯЦ для фильтрации
      const selectedYear = currentMonth.getFullYear();
      const selectedMonth = currentMonth.getMonth();
      const monthPrefix = `${selectedYear}-${String(selectedMonth + 1).padStart(2, '0')}`; // YYYY-MM
      
      console.log('[BrigadeStats] Filtering for MONTH:', monthPrefix);
      
      // Подсчет статистики по бригадам
      const stats = {};
      const dailyWork = {};
      
      (data.houses || []).forEach((house, idx) => {
        if (idx < 3) {
          console.log('[BrigadeStats] Sample house:', {
            brigade: house.brigade_name,
            address: house.address?.substring(0, 30),
            cleaning_dates: house.cleaning_dates
          });
        }
        const brigade = house.brigade_number || house.brigade_name || 'Не назначена';
        
        if (!stats[brigade]) {
          stats[brigade] = {
            brigade: brigade,
            totalHouses: 0,
            totalApartments: 0,
            totalEntrances: 0,
            totalFloors: 0,
            cleanings: {},
            sweepings: {}
          };
        }
        
        stats[brigade].totalHouses++;
        stats[brigade].totalApartments += house.apartments || 0;
        stats[brigade].totalEntrances += house.entrances || 0;
        stats[brigade].totalFloors += (house.entrances || 0) * (house.floors || 0);
        
        // Подсчет уборок по датам
        // Проверяем оба возможных формата: cleaning_dates и all_cleaning_dates
        const cleaningDatesObj = house.cleaning_dates || house.all_cleaning_dates;
        
        if (cleaningDatesObj && typeof cleaningDatesObj === 'object') {
          Object.values(cleaningDatesObj).forEach(period => {
            // period может быть объектом {dates: [...], type: '...'} 
            // или массивом дат
            let dates = [];
            let type = '';
            
            if (Array.isArray(period)) {
              dates = period;
            } else if (period && typeof period === 'object') {
              dates = period.dates || [];
              type = period.type || '';
            }
            
            if (dates && dates.length > 0) {
              dates.forEach(dateItem => {
                // dateItem может быть строкой или объектом {date: '...'}
                const dateStr = typeof dateItem === 'string' ? dateItem : dateItem?.date;
                
                if (!dateStr) return;
                
                const date = dateStr.split('T')[0]; // Формат YYYY-MM-DD
                
                // Фильтрация: ТОЛЬКО выбранная дата
                if (date !== selectedDate) {
                  return; // Пропускаем все даты кроме выбранной
                }
                
                const typeText = (type || '').toLowerCase();
                const isFullCleaning = typeText.includes('всех этаж');
                const isSweeping = typeText.includes('подмет');
                
                if (!dailyWork[date]) {
                  dailyWork[date] = {};
                }
                if (!dailyWork[date][brigade]) {
                  dailyWork[date][brigade] = {
                    entrances: 0,
                    floors: 0,
                    houses: 0,
                    sweepings: 0
                  };
                }
                
                dailyWork[date][brigade].houses++;
                
                if (isFullCleaning) {
                  dailyWork[date][brigade].entrances += house.entrances || 0;
                  dailyWork[date][brigade].floors += (house.entrances || 0) * (house.floors || 0);
                  
                  if (!stats[brigade].cleanings[date]) {
                    stats[brigade].cleanings[date] = { entrances: 0, floors: 0, houses: 0 };
                  }
                  stats[brigade].cleanings[date].entrances += house.entrances || 0;
                  stats[brigade].cleanings[date].floors += (house.entrances || 0) * (house.floors || 0);
                  stats[brigade].cleanings[date].houses++;
                }
                
                if (isSweeping) {
                  dailyWork[date][brigade].sweepings++;
                  
                  if (!stats[brigade].sweepings[date]) {
                    stats[brigade].sweepings[date] = 0;
                  }
                  stats[brigade].sweepings[date]++;
                }
              });
            }
          });
        } else if (idx < 3) {
          console.log('[BrigadeStats] No cleaning dates for house:', house.address?.substring(0, 30));
        }
      });
      
      const brigadeArray = Object.values(stats);
      console.log('[BrigadeStats] Calculated stats for', brigadeArray.length, 'brigades');
      console.log('[BrigadeStats] Daily work entries:', Object.keys(dailyWork).length);
      
      setBrigadeData(brigadeArray);
      setDailyStats(dailyWork);
    } catch (error) {
      console.error('[BrigadeStats] Error loading brigade stats:', error);
      console.error(error.stack);
      setError(error.message || 'Ошибка загрузки данных');
    } finally {
      console.log('[BrigadeStats] Loading complete, setting loading=false');
      setLoading(false);
    }
  };

  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    return new Date(year, month + 1, 0).getDate();
  };

  const formatDate = (year, month, day) => {
    const m = String(month + 1).padStart(2, '0');
    const d = String(day).padStart(2, '0');
    return `${year}-${m}-${d}`;
  };

  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();
  const day = currentMonth.getDate();
  const formattedDate = `${day} ${months[month]} ${year}`;
  const daysInMonth = getDaysInMonth(currentMonth);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
              <Users className="w-10 h-10 text-blue-600" />
              KPI Бригад
            </h1>
            <p className="text-gray-600">Статистика работы бригад на <span className="font-semibold text-blue-600">{formattedDate}</span></p>
          </div>
          
          {/* Селектор месяца с календарем */}
          <div className="flex items-center gap-3 bg-white rounded-lg shadow-md p-2 border border-gray-200">
            <button
              onClick={() => {
                const newDate = new Date(currentMonth);
                newDate.setMonth(newDate.getMonth() - 1);
                setCurrentMonth(newDate);
              }}
              className="p-2 hover:bg-gray-100 rounded-md transition-colors"
              title="Предыдущий месяц"
            >
              <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            
            {/* Календарь для выбора любой даты */}
            <input
              type="date"
              value={currentMonth.toISOString().split('T')[0]}
              onChange={(e) => {
                if (e.target.value) {
                  setCurrentMonth(new Date(e.target.value));
                }
              }}
              className="px-3 py-2 text-sm font-semibold text-gray-900 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              title="Выберите дату"
            />
            
            <button
              onClick={() => {
                const newDate = new Date(currentMonth);
                newDate.setMonth(newDate.getMonth() + 1);
                setCurrentMonth(newDate);
              }}
              className="p-2 hover:bg-gray-100 rounded-md transition-colors"
              title="Следующий месяц"
            >
              <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
            
            <button
              onClick={() => setCurrentMonth(new Date())}
              className="ml-2 px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors"
              title="Текущий месяц"
            >
              Сегодня
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка статистики...</p>
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <div className="text-red-600 text-xl mb-4">❌ Ошибка</div>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={loadBrigadeStats}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Повторить попытку
          </button>
        </div>
      ) : (
        <>
          {/* Распределение домов по бригадам */}
          {brigadeDistribution.length > 0 && (
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200 mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <PieChartIcon className="w-7 h-7 text-blue-600" />
                Распределение домов по бригадам
              </h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Круговая диаграмма */}
                <div className="flex items-center justify-center">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={brigadeDistribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ label, value, percent }) => `${label}: ${value} (${(percent * 100).toFixed(1)}%)`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {brigadeDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value, name, props) => [
                          `${value} домов (${((props.payload.value / brigadeDistribution.reduce((sum, b) => sum + b.value, 0)) * 100).toFixed(1)}%)`,
                          props.payload.label
                        ]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Таблица с данными */}
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-4 pb-3 border-b-2 border-gray-300 font-semibold text-gray-700">
                    <div>Бригада</div>
                    <div className="text-right">Домов</div>
                    <div className="text-right">Процент</div>
                  </div>
                  {brigadeDistribution
                    .sort((a, b) => b.value - a.value)
                    .map((brigade, idx) => {
                      const totalHouses = brigadeDistribution.reduce((sum, b) => sum + b.value, 0);
                      const percentage = ((brigade.value / totalHouses) * 100).toFixed(1);
                      
                      return (
                        <div 
                          key={idx} 
                          className="grid grid-cols-3 gap-4 p-3 rounded-lg hover:bg-gray-50 transition-all"
                        >
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-4 h-4 rounded"
                              style={{ backgroundColor: brigade.color }}
                            />
                            <span className="font-medium text-gray-900">{brigade.label}</span>
                          </div>
                          <div className="text-right font-semibold text-gray-900">
                            {brigade.value}
                          </div>
                          <div className="text-right">
                            <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
                              {percentage}%
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  
                  {/* Итого */}
                  <div className="grid grid-cols-3 gap-4 pt-3 border-t-2 border-gray-300 font-bold text-gray-900">
                    <div>Итого:</div>
                    <div className="text-right">
                      {brigadeDistribution.reduce((sum, b) => sum + b.value, 0)}
                    </div>
                    <div className="text-right">100%</div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Общая статистика по бригадам */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
            {brigadeData
              .filter(b => b.brigade !== 'Не назначена')
              .sort((a, b) => {
                const numA = parseInt(a.brigade) || 999;
                const numB = parseInt(b.brigade) || 999;
                return numA - numB;
              })
              .map((brigade, idx) => {
                const totalCleanings = Object.keys(brigade.cleanings).length;
                const totalSweepings = Object.keys(brigade.sweepings).length;
                const avgEntrancesPerDay = totalCleanings > 0 
                  ? Math.round(Object.values(brigade.cleanings).reduce((sum, day) => sum + day.entrances, 0) / totalCleanings)
                  : 0;
                
                return (
                  <div
                    key={idx}
                    className={`bg-white rounded-2xl shadow-lg p-6 border-2 cursor-pointer transition-all hover:shadow-xl ${
                      selectedBrigade === brigade.brigade ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'
                    }`}
                    onClick={() => setSelectedBrigade(selectedBrigade === brigade.brigade ? null : brigade.brigade)}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-2xl font-bold text-gray-900">{brigade.brigade} бригада</h3>
                      <TrendingUp className="w-6 h-6 text-green-600" />
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Домов:</span>
                        <span className="text-lg font-semibold">{brigade.totalHouses}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Подъездов:</span>
                        <span className="text-lg font-semibold text-blue-600">{brigade.totalEntrances}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Этажей:</span>
                        <span className="text-lg font-semibold text-purple-600">{brigade.totalFloors}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Уборок:</span>
                        <span className="text-lg font-semibold text-green-600">{totalCleanings}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Подметаний:</span>
                        <span className="text-lg font-semibold text-orange-600">{totalSweepings}</span>
                      </div>
                      <div className="pt-2 border-t border-gray-200">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500">Средн. подъездов/день:</span>
                          <span className="text-sm font-bold text-gray-900">{avgEntrancesPerDay}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>

          {/* Календарь работ выбранной бригады */}
          {selectedBrigade && (
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <CalendarIcon className="w-6 h-6 text-blue-600" />
                График работы: {selectedBrigade} бригада - {months[month]} {year}
              </h2>
              
              <div className="grid grid-cols-7 gap-2">
                {/* День недели */}
                {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map(day => (
                  <div key={day} className="text-center font-semibold text-gray-600 text-sm py-2">
                    {day}
                  </div>
                ))}
                
                {/* Пустые ячейки для выравнивания */}
                {Array(new Date(year, month, 1).getDay() === 0 ? 6 : new Date(year, month, 1).getDay() - 1)
                  .fill(null)
                  .map((_, i) => (
                    <div key={`empty-${i}`} />
                  ))}
                
                {/* Дни месяца */}
                {Array(daysInMonth).fill(null).map((_, i) => {
                  const day = i + 1;
                  const dateStr = formatDate(year, month, day);
                  const work = dailyStats[dateStr]?.[selectedBrigade];
                  const hasWork = work && (work.entrances > 0 || work.sweepings > 0);
                  
                  return (
                    <div
                      key={day}
                      className={`aspect-square p-2 rounded-lg border-2 transition-all ${
                        hasWork
                          ? 'bg-gradient-to-br from-green-50 to-green-100 border-green-300 hover:shadow-md'
                          : 'bg-gray-50 border-gray-200'
                      }`}
                    >
                      <div className="text-sm font-bold text-gray-900 mb-1">{day}</div>
                      {hasWork && (
                        <div className="text-xs space-y-0.5">
                          {work.entrances > 0 && (
                            <div className="text-blue-700 font-medium">
                              🏢 {work.entrances} подъездов
                            </div>
                          )}
                          {work.sweepings > 0 && (
                            <div className="text-orange-700 font-medium">
                              🧹 {work.sweepings} подм.
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              
              {/* Легенда */}
              <div className="mt-6 flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-300 rounded" />
                  <span className="text-gray-600">Есть работы</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-50 border-2 border-gray-200 rounded" />
                  <span className="text-gray-600">Нет работ</span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default BrigadeStats;
