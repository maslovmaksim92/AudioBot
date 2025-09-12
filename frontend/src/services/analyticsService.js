// Analytics Service - Клиентская аналитика для Фазы 4
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const analyticsService = {
  // Вычисляем аналитику из данных домов
  calculateAnalytics: (houses) => {
    const analytics = {
      overview: {
        total_houses: houses.length,
        total_apartments: 0,
        total_entrances: 0,
        total_floors: 0,
        scheduled_houses: 0,
        coverage_rate: 0,
        total_cleaning_events: 0
      },
      brigade_stats: {},
      company_stats: {},
      schedule_distribution: {
        scheduled: 0,
        not_scheduled: 0,
        total_cleaning_events: 0
      },
      calendar_events: [],
      kpi: {}
    };

    houses.forEach(house => {
      // Общая статистика
      analytics.overview.total_apartments += house.apartments_count || 0;
      analytics.overview.total_entrances += house.entrances_count || 0;
      analytics.overview.total_floors += house.floors_count || 0;

      // Статистика по бригадам
      const brigade = house.brigade || 'Не назначена';
      if (!analytics.brigade_stats[brigade]) {
        analytics.brigade_stats[brigade] = {
          houses: 0,
          apartments: 0,
          entrances: 0,
          floors: 0,
          scheduled_houses: 0,
          problem_houses: 0,
          coverage_rate: 0
        };
      }

      analytics.brigade_stats[brigade].houses += 1;
      analytics.brigade_stats[brigade].apartments += house.apartments_count || 0;
      analytics.brigade_stats[brigade].entrances += house.entrances_count || 0;
      analytics.brigade_stats[brigade].floors += house.floors_count || 0;

      // Статистика по УК
      const company = house.management_company || 'Не указана';
      if (!analytics.company_stats[company]) {
        analytics.company_stats[company] = {
          houses: 0,
          apartments: 0,
          avg_apartments: 0
        };
      }

      analytics.company_stats[company].houses += 1;
      analytics.company_stats[company].apartments += house.apartments_count || 0;

      // Проверяем графики уборки
      if (house.september_schedule && house.september_schedule.has_schedule) {
        analytics.overview.scheduled_houses += 1;
        analytics.schedule_distribution.scheduled += 1;
        analytics.brigade_stats[brigade].scheduled_houses += 1;

        // Считаем события уборки
        const dates1 = house.september_schedule.cleaning_date_1 || [];
        const dates2 = house.september_schedule.cleaning_date_2 || [];
        const eventCount = dates1.length + dates2.length;
        
        analytics.overview.total_cleaning_events += eventCount;
        analytics.schedule_distribution.total_cleaning_events += eventCount;

        // Создаем события календаря
        dates1.forEach(dateStr => {
          try {
            const date = new Date(dateStr);
            analytics.calendar_events.push({
              id: `${house.deal_id}_${date.getTime()}_1`,
              title: `Уборка: ${house.address}`,
              date: date.toISOString().split('T')[0],
              time: date.toTimeString().split(' ')[0].substring(0, 5),
              type: house.september_schedule.cleaning_type_1,
              address: house.address,
              brigade: brigade,
              deal_id: house.deal_id,
              month: 'september'
            });
          } catch (e) {
            console.warn('Date parsing error:', e);
          }
        });

        dates2.forEach(dateStr => {
          try {
            const date = new Date(dateStr);
            analytics.calendar_events.push({
              id: `${house.deal_id}_${date.getTime()}_2`,
              title: `Уборка: ${house.address}`,
              date: date.toISOString().split('T')[0],
              time: date.toTimeString().split(' ')[0].substring(0, 5),
              type: house.september_schedule.cleaning_type_2,
              address: house.address,
              brigade: brigade,
              deal_id: house.deal_id,
              month: 'september'
            });
          } catch (e) {
            console.warn('Date parsing error:', e);
          }
        });
      } else {
        analytics.schedule_distribution.not_scheduled += 1;
      }

      // Проблемные дома
      if (house.status_color === 'red' || house.status_color === 'yellow') {
        analytics.brigade_stats[brigade].problem_houses += 1;
      }
    });

    // Вычисляем проценты и средние значения
    analytics.overview.coverage_rate = analytics.overview.total_houses > 0 
      ? Math.round((analytics.overview.scheduled_houses / analytics.overview.total_houses) * 100)
      : 0;

    analytics.overview.avg_events_per_house = analytics.overview.total_houses > 0
      ? Math.round((analytics.overview.total_cleaning_events / analytics.overview.total_houses) * 10) / 10
      : 0;

    // Рассчитываем эффективность бригад
    Object.keys(analytics.brigade_stats).forEach(brigade => {
      const stats = analytics.brigade_stats[brigade];
      if (stats.houses > 0) {
        stats.coverage_rate = Math.round((stats.scheduled_houses / stats.houses) * 100);
        stats.avg_apartments = Math.round(stats.apartments / stats.houses);
        stats.problem_rate = Math.round((stats.problem_houses / stats.houses) * 100);
      }
    });

    // Средние значения по УК
    Object.keys(analytics.company_stats).forEach(company => {
      const stats = analytics.company_stats[company];
      if (stats.houses > 0) {
        stats.avg_apartments = Math.round((stats.apartments / stats.houses) * 10) / 10;
      }
    });

    // Сортируем календарные события
    analytics.calendar_events.sort((a, b) => new Date(a.date) - new Date(b.date));

    // KPI расчеты
    const topBrigades = Object.entries(analytics.brigade_stats)
      .sort((a, b) => b[1].coverage_rate - a[1].coverage_rate);

    analytics.kpi = {
      best_brigade: topBrigades[0] ? {
        name: topBrigades[0][0],
        coverage: topBrigades[0][1].coverage_rate,
        houses: topBrigades[0][1].houses
      } : null,
      worst_brigade: topBrigades[topBrigades.length - 1] ? {
        name: topBrigades[topBrigades.length - 1][0],
        coverage: topBrigades[topBrigades.length - 1][1].coverage_rate,
        houses: topBrigades[topBrigades.length - 1][1].houses
      } : null,
      total_brigades: Object.keys(analytics.brigade_stats).length,
      avg_houses_per_brigade: Math.round(analytics.overview.total_houses / Object.keys(analytics.brigade_stats).length),
      companies_count: Object.keys(analytics.company_stats).length
    };

    return analytics;
  },

  // Получаем данные для dashboard аналитики
  getDashboardAnalytics: async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/cleaning/houses-490`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      if (data.status === 'success' && data.houses) {
        return analyticsService.calculateAnalytics(data.houses);
      } else {
        throw new Error('Invalid data format');
      }
    } catch (error) {
      console.error('❌ Analytics service error:', error);
      return {
        error: error.message,
        overview: { total_houses: 0, coverage_rate: 0 }
      };
    }
  },

  // Форматтеры для отображения
  formatters: {
    percentage: (value) => `${value}%`,
    number: (value) => value.toLocaleString('ru-RU'),
    date: (dateStr) => {
      try {
        return new Date(dateStr).toLocaleDateString('ru-RU', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric'
        });
      } catch {
        return dateStr;
      }
    },
    time: (timeStr) => timeStr || '00:00'
  }
};

export default analyticsService;