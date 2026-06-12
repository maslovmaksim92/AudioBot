import React, { useEffect, useState } from 'react';
import { Building2, RefreshCw, CalendarDays, List, TrendingUp, Truck, FileCheck, Search, X, Calculator, CalendarRange, CheckSquare } from 'lucide-react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import CleaningCalendar from '../Calendar/CleaningCalendar';
import BrigadeStats from './BrigadeStats';
import Logistics from '../Logistics/Logistics';
import ActsStats from './ActsStats';
import PlanFact from './PlanFact';

const MONTH_EN_RU = {
  january: 'Январь', february: 'Февраль', march: 'Март', april: 'Апрель',
  may: 'Май', june: 'Июнь', july: 'Июль', august: 'Август',
  september: 'Сентябрь', october: 'Октябрь', november: 'Ноябрь', december: 'Декабрь',
};

// Очистка названия УК: убираем организационную форму (ООО, ОАО, ЗАО, АО, ПАО, ТСЖ, ИП, УК, "РКЦ" и т.п.) и кавычки
const cleanUK = (name) => {
  if (!name) return '';
  let s = String(name).trim();
  // убрать орг-формы в начале (возможно несколько подряд, напр. ООО "УК ...")
  s = s.replace(/^(\s*(ООО|ОАО|ЗАО|ПАО|АО|ТСЖ|ТСН|ЖСК|ИП|МУП|ГУП|УК)\b[\s"«»]*)+/iu, '');
  // снять обрамляющие кавычки
  s = s.replace(/^[«"']+|[«"'»]+$/g, '').trim();
  return s || String(name).trim();
};

// Короткая сводка графика для ячейки таблицы: "Май: 15, 29" (+N мес.)
const scheduleSummary = (house) => {
  const cd = house?.cleaning_dates || {};
  const keys = Object.keys(cd).filter(k => (cd[k]?.dates?.length || 0) > 0);
  if (keys.length === 0) return null;
  keys.sort((a, b) => {
    const pa = (a.match(/_(\d{4})$/) || [])[1] || '';
    const pb = (b.match(/_(\d{4})$/) || [])[1] || '';
    return (pa + a).localeCompare(pb + b);
  });
  const first = keys[0];
  const m = first.toLowerCase().match(/^([a-z]+)_(\d{4})$/);
  const monthName = m && MONTH_EN_RU[m[1]] ? MONTH_EN_RU[m[1]] : first;
  const days = (cd[first].dates || []).map(d => (d || '').split('T')[0].split('-')[2]).filter(Boolean);
  return { label: monthName, days, more: keys.length - 1 };
};

// дни уборки выбранного месяца (listMonth -> month_key)
const monthKeyFromYM = (ym) => {
  const M = {1:'january',2:'february',3:'march',4:'april',5:'may',6:'june',7:'july',8:'august',9:'september',10:'october',11:'november',12:'december'};
  if (!ym) return null;
  const [y, m] = ym.split('-'); return `${M[parseInt(m)]}_${parseInt(y)}`;
};

const Works = () => {
  const [activeTab, setActiveTab] = useState('list');
  const [houses, setHouses] = useState([]);
  const [pagination, setPagination] = useState({ total: 0, page: 1, limit: 50, pages: 0 });
  const [filters, setFilters] = useState({ brigades: [], statuses: [], companies: [] });
  const [loading, setLoading] = useState(false);
  const [listMonth, setListMonth] = useState(() => {
    const n = new Date(); return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, '0')}`;
  });
  const [activeFilters, setActiveFilters] = useState({
    brigade: '', management_company: '', search: '', periodicity: '',
    cleaning_date: '', date_from: '', date_to: '',
  });
  const [notification, setNotification] = useState(null);
  const [calcMonth, setCalcMonth] = useState(() => { const n = new Date(); return `${n.getFullYear()}-${String(n.getMonth()+1).padStart(2,'0')}`; });
  const [calcData, setCalcData] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);
  const [dailyData, setDailyData] = useState(null);
  const [dailyLoading, setDailyLoading] = useState(false);
  const [expandedDay, setExpandedDay] = useState(null);

  useEffect(() => { fetchInitial(); }, []);
  useEffect(() => { fetchHouses(); }, [activeFilters, pagination.page, pagination.limit, listMonth]);
  useEffect(() => { if (activeTab === 'calc') fetchCalc(); }, [activeTab, calcMonth]);
  useEffect(() => { if (activeTab === 'daily') fetchDaily(); }, [activeTab, calcMonth]);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 2200);
  };

  const fetchInitial = async () => {
    setLoading(true);
    try {
      await Promise.all([fetchFilters(), fetchHouses()]);
    } catch (e) {
      console.error(e);
      showNotification('Ошибка загрузки данных', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchFilters = async () => {
    try {
      const r = await fetch(`${BACKEND_URL}/api/cleaning/filters`);
      const data = await r.json();
      setFilters({ brigades: data.brigades || [], statuses: data.statuses || [], companies: data.companies || [] });
    } catch (e) {
      console.error('filters error', e);
    }
  };

  const fetchHouses = async () => {
    setLoading(true);
    try {
      const q = new URLSearchParams();
      Object.entries(activeFilters).forEach(([k, v]) => {
        if (!v) return;
        if (k === 'search') q.append('address', v);
        else if (k === 'periodicity') return; // фильтруется на клиенте
        else q.append(k, v);
      });
      if (listMonth) q.append('month', listMonth);
      q.append('page', String(pagination.page));
      q.append('limit', String(pagination.limit));
      const url = `${BACKEND_URL}/api/cleaning/houses?${q.toString()}`;
      const r = await fetch(url);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setHouses(data.houses || []);
      setPagination({ total: data.total || 0, page: data.page || 1, limit: data.limit || 50, pages: data.pages || 0 });
    } catch (e) {
      console.error('houses error', e);
      setHouses([]);
      showNotification('Ошибка загрузки домов', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchDaily = async () => {
    setDailyLoading(true);
    try {
      const r = await fetch(`${BACKEND_URL}/api/cleaning/daily-calc?month=${calcMonth}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setDailyData(await r.json());
    } catch (e) {
      console.error('daily error', e);
      setDailyData(null);
      showNotification('Ошибка загрузки расчётов по дням', 'error');
    } finally {
      setDailyLoading(false);
    }
  };

  const fetchCalc = async () => {
    setCalcLoading(true);
    try {
      const r = await fetch(`${BACKEND_URL}/api/cleaning/brigade-calc?month=${calcMonth}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setCalcData(await r.json());
    } catch (e) {
      console.error('calc error', e);
      setCalcData(null);
      showNotification('Ошибка загрузки расчётов', 'error');
    } finally {
      setCalcLoading(false);
    }
  };

  const handlePageChange = (newPage) => setPagination(prev => ({ ...prev, page: newPage }));
  const handleLimitChange = (newLimit) => setPagination(prev => ({ ...prev, limit: parseInt(newLimit), page: 1 }));
  const setF = (patch) => { setActiveFilters(prev => ({ ...prev, ...patch })); setPagination(prev => ({ ...prev, page: 1 })); };
  const resetFilters = () => { setActiveFilters({ brigade: '', management_company: '', search: '', periodicity: '', cleaning_date: '', date_from: '', date_to: '' }); setPagination(prev => ({ ...prev, page: 1 })); };

  // клиентский фильтр по периодичности (подстрока, т.к. формулировки разные)
  const visibleHouses = activeFilters.periodicity
    ? houses.filter(h => (h.periodicity || '').toLowerCase().includes(activeFilters.periodicity.toLowerCase()))
    : houses;

  const monthDays = (h) => {
    const key = monthKeyFromYM(listMonth);
    const cd = (h.cleaning_dates || {})[key];
    if (!cd || !cd.dates) return [];
    return cd.dates.map(d => (d || '').split('T')[0].split('-')[2]).filter(Boolean);
  };

  const periodicityOptions = ['2 мытья', '4 мытья', 'подметания', '1 этажа', 'индивидуальный'];
  const activeFilterCount = Object.values(activeFilters).filter(Boolean).length;

  return (
    <div className="max-w-[1600px] mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Building2 className="w-8 h-8 mr-3 text-blue-600" />
          Работы (Дома)
        </h1>
        <button onClick={fetchHouses} className="btn-primary flex items-center">
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Обновить
        </button>
      </div>

      {/* Вкладки */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex gap-4">
          {[
            { id: 'list', label: 'Список домов', Icon: List },
            { id: 'planfact', label: 'Контроль', Icon: CheckSquare },
            { id: 'calendar', label: 'Календарь уборок', Icon: CalendarDays },
            { id: 'brigades', label: 'KPI Бригад', Icon: TrendingUp },
            { id: 'logistics', label: 'Логистика', Icon: Truck },
            { id: 'acts', label: 'Акты', Icon: FileCheck },
            { id: 'calc', label: 'Расчёты', Icon: Calculator },
            { id: 'daily', label: 'Расчёты по дням', Icon: CalendarRange },
          ].map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`pb-4 px-2 font-medium transition-colors relative ${
                activeTab === id ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <div className="flex items-center gap-2"><Icon className="w-5 h-5" />{label}</div>
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'calendar' && (<div className="-m-6"><CleaningCalendar /></div>)}
      {activeTab === 'brigades' && (<div className="-m-6"><BrigadeStats /></div>)}
      {activeTab === 'logistics' && (<div className="-m-6"><Logistics /></div>)}
      {activeTab === 'acts' && (<div className="-m-6 p-6"><ActsStats /></div>)}
      {activeTab === 'planfact' && (<div className="-m-6"><PlanFact /></div>)}

      {/* Вкладка "Расчёты" — побригадно */}
      {activeTab === 'calc' && (
        <div>
          <div className="flex items-center gap-3 mb-4">
            <Calculator className="w-5 h-5 text-blue-600" />
            <span className="text-sm text-gray-600">Месяц расчёта:</span>
            <input
              type="month"
              value={calcMonth}
              onChange={(e) => setCalcMonth(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
            />
            <button onClick={fetchCalc} className="px-3 py-1.5 text-sm rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center gap-1">
              <RefreshCw className={`w-3.5 h-3.5 ${calcLoading ? 'animate-spin' : ''}`} /> Обновить
            </button>
          </div>

          {/* Карточки-итоги */}
          {calcData?.totals && (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-5">
              {[
                { label: 'Бригад', value: calcData.brigades?.length || 0, color: 'from-slate-500 to-slate-600' },
                { label: 'Домов', value: calcData.totals.houses, color: 'from-blue-500 to-blue-600' },
                { label: 'Подъездов', value: calcData.totals.entrances, color: 'from-indigo-500 to-indigo-600' },
                { label: 'Уборок (план)', value: calcData.totals.plan_cleanings, color: 'from-purple-500 to-purple-600' },
                { label: 'Уборок (факт)', value: calcData.totals.fact_cleanings, color: 'from-green-500 to-green-600' },
                { label: 'Выручка/мес, ₽', value: (calcData.totals.revenue || 0).toLocaleString('ru-RU'), color: 'from-amber-500 to-orange-600' },
              ].map((c, i) => (
                <div key={i} className={`bg-gradient-to-br ${c.color} text-white rounded-xl p-3 shadow-sm`}>
                  <div className="text-xl font-bold leading-none">{c.value}</div>
                  <div className="text-xs opacity-90 mt-1">{c.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Таблица по бригадам */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200 text-left text-xs uppercase tracking-wide text-gray-500">
                    <th className="px-4 py-3 font-semibold">Бригада</th>
                    <th className="px-3 py-3 font-semibold text-center">Домов</th>
                    <th className="px-3 py-3 font-semibold text-center">Подъездов</th>
                    <th className="px-3 py-3 font-semibold text-center">Этажей</th>
                    <th className="px-3 py-3 font-semibold text-center">Квартир</th>
                    <th className="px-3 py-3 font-semibold text-center">Ср. подъездов/дом</th>
                    <th className="px-3 py-3 font-semibold text-center">Уборок план</th>
                    <th className="px-3 py-3 font-semibold text-center">Уборок факт</th>
                    <th className="px-4 py-3 font-semibold text-right">Выручка/мес, ₽</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {calcLoading && (<tr><td colSpan={9} className="px-4 py-10 text-center text-gray-400">Загрузка…</td></tr>)}
                  {!calcLoading && (!calcData?.brigades || calcData.brigades.length === 0) && (
                    <tr><td colSpan={9} className="px-4 py-10 text-center text-gray-400">Нет данных за выбранный месяц.</td></tr>
                  )}
                  {!calcLoading && calcData?.brigades?.map((b) => {
                    const planFactPct = b.plan_cleanings > 0 ? Math.round((b.fact_cleanings / b.plan_cleanings) * 100) : null;
                    return (
                      <tr key={b.brigade} className="hover:bg-blue-50/40 transition-colors">
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200">{b.brigade} бригада</span>
                        </td>
                        <td className="px-3 py-3 text-center font-medium text-gray-800">{b.houses}</td>
                        <td className="px-3 py-3 text-center font-medium text-gray-800">{b.entrances}</td>
                        <td className="px-3 py-3 text-center text-gray-700">{b.floors}</td>
                        <td className="px-3 py-3 text-center text-gray-700">{b.apartments}</td>
                        <td className="px-3 py-3 text-center text-gray-600">{b.avg_entrances_per_house}</td>
                        <td className="px-3 py-3 text-center text-purple-700 font-medium">{b.plan_cleanings}</td>
                        <td className="px-3 py-3 text-center">
                          <span className="text-green-700 font-medium">{b.fact_cleanings}</span>
                          {planFactPct !== null && (
                            <span className={`ml-1 text-xs ${planFactPct >= 100 ? 'text-green-500' : planFactPct >= 50 ? 'text-amber-500' : 'text-red-400'}`}>({planFactPct}%)</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right font-semibold text-gray-900">{(b.revenue || 0).toLocaleString('ru-RU')}</td>
                      </tr>
                    );
                  })}
                </tbody>
                {!calcLoading && calcData?.totals && calcData.brigades?.length > 0 && (
                  <tfoot>
                    <tr className="bg-gray-50 border-t-2 border-gray-200 font-semibold text-gray-900">
                      <td className="px-4 py-3">ИТОГО</td>
                      <td className="px-3 py-3 text-center">{calcData.totals.houses}</td>
                      <td className="px-3 py-3 text-center">{calcData.totals.entrances}</td>
                      <td className="px-3 py-3 text-center">{calcData.totals.floors}</td>
                      <td className="px-3 py-3 text-center">{calcData.totals.apartments}</td>
                      <td className="px-3 py-3 text-center">—</td>
                      <td className="px-3 py-3 text-center text-purple-700">{calcData.totals.plan_cleanings}</td>
                      <td className="px-3 py-3 text-center text-green-700">{calcData.totals.fact_cleanings}</td>
                      <td className="px-4 py-3 text-right">{(calcData.totals.revenue || 0).toLocaleString('ru-RU')} ₽</td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </div>

          <div className="mt-3 text-xs text-gray-400">
            Выручка = месячная стоимость дома (сумма договора из Bitrix). Уборки план — из графика, факт — из фото-отчётов.
          </div>
        </div>
      )}

      {/* Вкладка "Расчёты по дням" */}
      {activeTab === 'daily' && (
        <div>
          <div className="flex items-center gap-3 mb-4">
            <CalendarRange className="w-5 h-5 text-blue-600" />
            <span className="text-sm text-gray-600">Месяц:</span>
            <input
              type="month"
              value={calcMonth}
              onChange={(e) => setCalcMonth(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
            />
            <button onClick={fetchDaily} className="px-3 py-1.5 text-sm rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center gap-1">
              <RefreshCw className={`w-3.5 h-3.5 ${dailyLoading ? 'animate-spin' : ''}`} /> Обновить
            </button>
          </div>

          {/* Итоги за месяц */}
          {dailyData?.totals && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-5">
              {[
                { label: 'Дней с уборками', value: dailyData.totals.days, color: 'from-slate-500 to-slate-600' },
                { label: 'Всего уборок', value: dailyData.totals.cleanings, color: 'from-blue-500 to-blue-600' },
                { label: 'Подъездов (сумма)', value: dailyData.totals.entrances, color: 'from-indigo-500 to-indigo-600' },
                { label: 'Этажей (сумма)', value: dailyData.totals.floors, color: 'from-purple-500 to-purple-600' },
                { label: 'Деньги, ₽', value: (dailyData.totals.money || 0).toLocaleString('ru-RU'), color: 'from-amber-500 to-orange-600' },
              ].map((c, i) => (
                <div key={i} className={`bg-gradient-to-br ${c.color} text-white rounded-xl p-3 shadow-sm`}>
                  <div className="text-xl font-bold leading-none">{c.value}</div>
                  <div className="text-xs opacity-90 mt-1">{c.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Таблица по дням */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200 text-left text-xs uppercase tracking-wide text-gray-500">
                    <th className="px-4 py-3 font-semibold">Дата</th>
                    <th className="px-3 py-3 font-semibold text-center">День</th>
                    <th className="px-3 py-3 font-semibold text-center">Уборок</th>
                    <th className="px-3 py-3 font-semibold text-center">Подъездов</th>
                    <th className="px-3 py-3 font-semibold text-center">Этажей</th>
                    <th className="px-4 py-3 font-semibold text-right">Деньги, ₽</th>
                    <th className="px-3 py-3 font-semibold text-center">Бригады</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {dailyLoading && (<tr><td colSpan={7} className="px-4 py-10 text-center text-gray-400">Загрузка…</td></tr>)}
                  {!dailyLoading && (!dailyData?.days || dailyData.days.length === 0) && (
                    <tr><td colSpan={7} className="px-4 py-10 text-center text-gray-400">Нет уборок в этом месяце.</td></tr>
                  )}
                  {!dailyLoading && dailyData?.days?.map((d) => {
                    const isWeekend = d.weekday === 'Сб' || d.weekday === 'Вс';
                    const open = expandedDay === d.date;
                    const [yy, mm, dd] = d.date.split('-');
                    return (
                      <React.Fragment key={d.date}>
                        <tr
                          className={`hover:bg-blue-50/40 transition-colors cursor-pointer ${isWeekend ? 'bg-amber-50/40' : ''}`}
                          onClick={() => setExpandedDay(open ? null : d.date)}
                        >
                          <td className="px-4 py-3 font-medium text-gray-900">{dd}.{mm}.{yy}</td>
                          <td className={`px-3 py-3 text-center text-xs font-medium ${isWeekend ? 'text-amber-600' : 'text-gray-500'}`}>{d.weekday}</td>
                          <td className="px-3 py-3 text-center font-semibold text-blue-700">{d.cleanings}</td>
                          <td className="px-3 py-3 text-center text-gray-800">{d.entrances}</td>
                          <td className="px-3 py-3 text-center text-gray-700">{d.floors}</td>
                          <td className="px-4 py-3 text-right font-semibold text-gray-900">{(d.money || 0).toLocaleString('ru-RU')}</td>
                          <td className="px-3 py-3 text-center">
                            <span className="inline-flex items-center gap-1 text-xs text-gray-500">
                              {d.brigades?.length || 0} {open ? '▲' : '▼'}
                            </span>
                          </td>
                        </tr>
                        {open && d.brigades?.map((b) => (
                          <tr key={d.date + '_' + b.brigade} className="bg-gray-50/70 text-xs">
                            <td className="px-4 py-2 pl-8 text-gray-400">↳ {b.brigade === '—' ? 'без бригады' : b.brigade + ' бригада'}</td>
                            <td></td>
                            <td className="px-3 py-2 text-center text-blue-600">{b.cleanings}</td>
                            <td className="px-3 py-2 text-center text-gray-600">{b.entrances}</td>
                            <td className="px-3 py-2 text-center text-gray-600">{b.floors}</td>
                            <td className="px-4 py-2 text-right text-gray-700">{(b.money || 0).toLocaleString('ru-RU')}</td>
                            <td></td>
                          </tr>
                        ))}
                      </React.Fragment>
                    );
                  })}
                </tbody>
                {!dailyLoading && dailyData?.totals && dailyData.days?.length > 0 && (
                  <tfoot>
                    <tr className="bg-gray-50 border-t-2 border-gray-200 font-semibold text-gray-900">
                      <td className="px-4 py-3" colSpan={2}>ИТОГО за месяц</td>
                      <td className="px-3 py-3 text-center text-blue-700">{dailyData.totals.cleanings}</td>
                      <td className="px-3 py-3 text-center">{dailyData.totals.entrances}</td>
                      <td className="px-3 py-3 text-center">{dailyData.totals.floors}</td>
                      <td className="px-4 py-3 text-right">{(dailyData.totals.money || 0).toLocaleString('ru-RU')} ₽</td>
                      <td></td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </div>

          <div className="mt-3 text-xs text-gray-400">
            Деньги за день = Σ по уборкам (месячная стоимость дома ÷ число уборок дома в месяце). Нажмите на строку дня — разбивка по бригадам.
          </div>
        </div>
      )}

      {/* Вкладка "Список домов": слева фильтры, справа таблица */}
      {activeTab === 'list' && (
        <div className="flex flex-col lg:flex-row gap-6 items-start">

          {/* ЛЕВАЯ ПАНЕЛЬ ФИЛЬТРОВ */}
          <aside className="w-full lg:w-72 flex-shrink-0 lg:sticky lg:top-4">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-800 flex items-center gap-2">
                  <Search className="w-4 h-4 text-blue-600" /> Фильтры
                </h3>
                {activeFilterCount > 0 && (
                  <button onClick={resetFilters} className="text-xs text-gray-500 hover:text-red-600 flex items-center gap-1">
                    <X className="w-3 h-3" /> Сброс
                  </button>
                )}
              </div>

              {/* Месяц */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Месяц графика</label>
                <input
                  type="month"
                  value={listMonth}
                  onChange={(e) => setListMonth(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Поиск по адресу */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Поиск по адресу</label>
                <div className="relative">
                  <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Улица, дом…"
                    value={activeFilters.search}
                    onChange={(e) => setF({ search: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* УК */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Управляющая компания</label>
                <select
                  value={activeFilters.management_company}
                  onChange={(e) => setF({ management_company: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Все УК</option>
                  {filters.companies?.map((c, i) => {
                    const val = typeof c === 'object' ? c.id : c;
                    const lbl = typeof c === 'object' ? c.name : c;
                    return <option key={i} value={val}>{cleanUK(lbl)}</option>;
                  })}
                </select>
              </div>

              {/* Бригада */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Бригада</label>
                <select
                  value={activeFilters.brigade}
                  onChange={(e) => setF({ brigade: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Все бригады</option>
                  {filters.brigades?.map((b, i) => {
                    const val = typeof b === 'object' ? b.id : b;
                    const lbl = typeof b === 'object' ? b.name : b;
                    return <option key={i} value={val}>{lbl}</option>;
                  })}
                </select>
              </div>

              {/* Периодичность */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Периодичность</label>
                <select
                  value={activeFilters.periodicity}
                  onChange={(e) => setF({ periodicity: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Любая</option>
                  {periodicityOptions.map((p, i) => <option key={i} value={p}>{p}</option>)}
                </select>
              </div>

              {/* Дата уборки */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Дата уборки</label>
                <DatePicker
                  selected={activeFilters.cleaning_date ? new Date(activeFilters.cleaning_date) : null}
                  onChange={(date) => setF({ cleaning_date: date ? format(date, 'yyyy-MM-dd') : '' })}
                  placeholderText="Выберите дату"
                  dateFormat="dd.MM.yyyy"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  locale={ru}
                  isClearable
                />
              </div>

              {/* Быстрые фильтры по дате */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Быстро</label>
                <div className="flex flex-wrap gap-2">
                  <button className="px-2 py-1 text-xs rounded-md bg-gray-100 hover:bg-blue-100 text-gray-700" onClick={() => setF({ cleaning_date: format(new Date(), 'yyyy-MM-dd'), date_from: '', date_to: '' })}>Сегодня</button>
                  <button className="px-2 py-1 text-xs rounded-md bg-gray-100 hover:bg-blue-100 text-gray-700" onClick={() => { const d = new Date(); d.setDate(d.getDate() + 1); setF({ cleaning_date: format(d, 'yyyy-MM-dd'), date_from: '', date_to: '' }); }}>Завтра</button>
                  <button className="px-2 py-1 text-xs rounded-md bg-gray-100 hover:bg-blue-100 text-gray-700" onClick={() => { const from = new Date(); const to = new Date(); to.setDate(to.getDate() + 7); setF({ cleaning_date: '', date_from: format(from, 'yyyy-MM-dd'), date_to: format(to, 'yyyy-MM-dd') }); }}>Неделя</button>
                </div>
              </div>

              {/* Кол-во на странице */}
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Показывать по</label>
                <div className="flex gap-2">
                  {[10, 50, 100].map(n => (
                    <button key={n} onClick={() => handleLimitChange(n)} className={`flex-1 px-2 py-1 text-xs rounded-md ${pagination.limit === n ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}>{n}</button>
                  ))}
                </div>
              </div>

              {/* CSV-отчёт */}
              <div className="pt-2 border-t border-gray-100">
                <button
                  onClick={() => window.open(`${BACKEND_URL}/api/cleaning/missing-data-report`, '_blank')}
                  className="w-full px-3 py-2 text-xs rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 flex items-center justify-center gap-2"
                >
                  ⬇ Скачать отчёт CSV
                </button>
              </div>
            </div>
          </aside>

          {/* ПРАВАЯ ЧАСТЬ — ТАБЛИЦА */}
          <div className="flex-1 min-w-0 w-full">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-gray-600">
                Найдено домов: <span className="font-semibold text-gray-900">{activeFilters.periodicity ? visibleHouses.length : pagination.total}</span>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200 text-left text-xs uppercase tracking-wide text-gray-500">
                      <th className="px-4 py-3 font-semibold">Адрес</th>
                      <th className="px-4 py-3 font-semibold">УК</th>
                      <th className="px-4 py-3 font-semibold text-center">Бригада</th>
                      <th className="px-3 py-3 font-semibold text-center">Кв.</th>
                      <th className="px-3 py-3 font-semibold text-center">Под.</th>
                      <th className="px-3 py-3 font-semibold text-center">Эт.</th>
                      <th className="px-4 py-3 font-semibold">Периодичность</th>
                      <th className="px-4 py-3 font-semibold">График за месяц</th>
                      <th className="px-3 py-3 font-semibold text-center">Акт</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {loading && (
                      <tr><td colSpan={9} className="px-4 py-10 text-center text-gray-400">Загрузка…</td></tr>
                    )}
                    {!loading && visibleHouses.length === 0 && (
                      <tr><td colSpan={9} className="px-4 py-10 text-center text-gray-400">Дома не найдены. Измените фильтры.</td></tr>
                    )}
                    {!loading && visibleHouses.map((h, idx) => {
                      const sched = scheduleSummary(h);
                      const noBrigade = !h.brigade_name || h.brigade_name === 'Бригада не назначена';
                      return (
                        <tr key={h.id} className={`hover:bg-blue-50/40 transition-colors ${idx % 2 ? 'bg-gray-50/40' : ''}`}>
                          <td className="px-4 py-3">
                            <div className="font-medium text-gray-900 leading-tight">{h.address || h.title || '—'}</div>
                            <div className="text-xs text-gray-400">ID: {h.id}</div>
                          </td>
                          <td className="px-4 py-3 text-gray-700">{cleanUK(h.management_company) || <span className="text-gray-300">—</span>}</td>
                          <td className="px-4 py-3 text-center">
                            {noBrigade
                              ? <span className="text-xs text-gray-300">—</span>
                              : <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">{h.brigade_name}</span>}
                          </td>
                          <td className="px-3 py-3 text-center font-semibold text-gray-800">{h.apartments || <span className="text-gray-300 font-normal">—</span>}</td>
                          <td className="px-3 py-3 text-center font-semibold text-gray-800">{h.entrances || <span className="text-gray-300 font-normal">—</span>}</td>
                          <td className="px-3 py-3 text-center font-semibold text-gray-800">{h.floors || <span className="text-gray-300 font-normal">—</span>}</td>
                          <td className="px-4 py-3">
                            {h.periodicity && h.periodicity !== 'не указана'
                              ? <span className="text-gray-700">{h.periodicity}</span>
                              : <span className="text-xs text-amber-500">не указана</span>}
                          </td>
                          <td className="px-4 py-3">
                            {monthDays(h).length > 0 ? (
                              <div className="flex items-center gap-1 flex-wrap">
                                {monthDays(h).map((d, i) => (
                                  <span key={i} className="inline-flex items-center justify-center min-w-[24px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 text-xs font-semibold border border-purple-100">{d}</span>
                                ))}
                              </div>
                            ) : <span className="text-xs text-gray-300">нет в этом месяце</span>}
                          </td>
                          <td className="px-3 py-3 text-center">
                            {h.act_signed
                              ? <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200" title={`Фото: ${h.act_photo_count || 0}`}>✓ подписан</span>
                              : <span className="text-xs text-gray-300">—</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Пагинация */}
            {!activeFilters.periodicity && pagination.pages > 1 && (
              <div className="mt-4 flex flex-wrap items-center gap-1.5 justify-center">
                <button disabled={pagination.page <= 1} onClick={() => handlePageChange(pagination.page - 1)} className="px-3 py-1 rounded border text-sm bg-white hover:bg-gray-50 disabled:opacity-40">←</button>
                {Array.from({ length: pagination.pages }).slice(
                  Math.max(0, pagination.page - 3),
                  Math.max(0, pagination.page - 3) + 6
                ).map((_, i) => {
                  const pageNum = Math.max(0, pagination.page - 3) + i + 1;
                  if (pageNum > pagination.pages) return null;
                  return (
                    <button key={pageNum} onClick={() => handlePageChange(pageNum)} className={`px-3 py-1 rounded border text-sm ${pagination.page === pageNum ? 'bg-blue-600 text-white border-blue-600' : 'bg-white hover:bg-gray-50'}`}>{pageNum}</button>
                  );
                })}
                <button disabled={pagination.page >= pagination.pages} onClick={() => handlePageChange(pagination.page + 1)} className="px-3 py-1 rounded border text-sm bg-white hover:bg-gray-50 disabled:opacity-40">→</button>
              </div>
            )}
          </div>
        </div>
      )}

      {notification && (
        <div className={`fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 text-white ${notification.type === 'success' ? 'bg-green-500' : notification.type === 'error' ? 'bg-red-500' : 'bg-blue-500'}`}>
          {notification.message}
        </div>
      )}
    </div>
  );
};

export default Works;
