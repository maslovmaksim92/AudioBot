import React, { useEffect, useRef, useState } from 'react';
import { Building2, Users, Calendar, MapPin, RefreshCw, CalendarDays, List, TrendingUp, Truck, FileCheck, Image } from 'lucide-react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import EditHouseModal from './EditHouseModal';
import CleaningCalendar from '../Calendar/CleaningCalendar';
import BrigadeStats from './BrigadeStats';
import Logistics from '../Logistics/Logistics';
import ActsStats from './ActsStats';
import ActSignModal from './ActSignModal';
import PhotoHistoryModal from './PhotoHistoryModal';

const monthMeta = {
  september_1: { title: 'Сентябрь · 1', color: 'purple' },
  september_2: { title: 'Сентябрь · 2', color: 'purple' },
  october_1: { title: 'Октябрь · 1', color: 'orange' },
  october_2: { title: 'Октябрь · 2', color: 'orange' },
  november_1: { title: 'Ноябрь · 1', color: 'yellow' },
  november_2: { title: 'Ноябрь · 2', color: 'yellow' },
  december_1: { title: 'Декабрь · 1', color: 'blue' },
  december_2: { title: 'Декабрь · 2', color: 'blue' },
};

const Works = () => {
  const [activeTab, setActiveTab] = useState('list'); // 'list', 'calendar', 'kpi', 'logistics', 'acts'
  const [houses, setHouses] = useState([]);
  const [pagination, setPagination] = useState({ total: 0, page: 1, limit: 50, pages: 0 });
  const [filters, setFilters] = useState({ brigades: [], statuses: [] });
  const [loading, setLoading] = useState(false);
  const [activeFilters, setActiveFilters] = useState({ brigade: '', status: '', search: '', cleaning_date: '', date_from: '', date_to: '' });
  const [notification, setNotification] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [houseDetails, setHouseDetails] = useState(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedHouse, setSelectedHouse] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showActSignModal, setShowActSignModal] = useState(false);
  const [selectedHouseForAct, setSelectedHouseForAct] = useState(null);
  const [showPhotoHistoryModal, setShowPhotoHistoryModal] = useState(false);
  const [selectedHouseForPhotos, setSelectedHouseForPhotos] = useState(null);
  const detailsLoadingRef = useRef(false);

  useEffect(() => { fetchInitial(); }, []);
  useEffect(() => { fetchHouses(); }, [activeFilters, pagination.page, pagination.limit]);

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
      setFilters(data || { brigades: [], statuses: [] });
    } catch (e) {
      console.error('filters error', e);
    }
  };

  const fetchHouses = async () => {
    try {
      const q = new URLSearchParams();
      Object.entries(activeFilters).forEach(([k, v]) => {
        if (!v) return;
        // search -> address for backend
        if (k === 'search') q.append('address', v);
        else q.append(k, v);
      });
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
      showNotification('Ошибка загрузки домов из Bitrix24', 'error');
    }
  };

  const handlePageChange = (newPage) => setPagination(prev => ({ ...prev, page: newPage }));
  const handleLimitChange = (newLimit) => setPagination(prev => ({ ...prev, limit: parseInt(newLimit), page: 1 }));

  const fetchHouseDetails = async (houseId) => {
    if (detailsLoadingRef.current) return;
    detailsLoadingRef.current = true;
    try {
      const r = await fetch(`${BACKEND_URL}/api/cleaning/house/${houseId}/details`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setHouseDetails(data);
      setShowDetailsModal(true);
    } catch (e) {
      console.error('details error', e);
      showNotification('Ошибка загрузки деталей дома', 'error');
    } finally {
      detailsLoadingRef.current = false;
    }
  };

  const renderMonthBlock = (key, block) => {
    if (!block?.dates || block.dates.length === 0) return null;
    const meta = monthMeta[key] || { title: key, color: 'gray' };
    const colorMap = {
      purple: { bg: 'bg-purple-50', text: 'text-purple-700', badge: 'bg-purple-500' },
      orange: { bg: 'bg-orange-50', text: 'text-orange-700', badge: 'bg-orange-500' },
      yellow: { bg: 'bg-yellow-50', text: 'text-yellow-700', badge: 'bg-yellow-500' },
      blue: { bg: 'bg-blue-50', text: 'text-blue-700', badge: 'bg-blue-500' },
      gray: { bg: 'bg-gray-50', text: 'text-gray-700', badge: 'bg-gray-400' },
    };
    const c = colorMap[meta.color] || colorMap.gray;
    return (
      <div key={key} className={`mb-3 p-3 rounded-lg border ${c.bg}`}></div>
    );
  };

  // Custom Month Block with content (moved below to keep JSX tidy)
  const MonthBlock = ({ k, block }) => {
    if (!block?.dates || block.dates.length === 0) return null;
    const meta = monthMeta[k] || { title: k, color: 'gray' };
    const colorMap = {
      purple: { bg: 'bg-gradient-to-br from-purple-50 to-purple-100', text: 'text-purple-800', badge: 'bg-purple-500', border: 'border-purple-200' },
      orange: { bg: 'bg-gradient-to-br from-orange-50 to-orange-100', text: 'text-orange-800', badge: 'bg-orange-500', border: 'border-orange-200' },
      yellow: { bg: 'bg-gradient-to-br from-yellow-50 to-yellow-100', text: 'text-yellow-800', badge: 'bg-yellow-500', border: 'border-yellow-200' },
      blue: { bg: 'bg-gradient-to-br from-blue-50 to-blue-100', text: 'text-blue-800', badge: 'bg-blue-500', border: 'border-blue-200' },
      gray: { bg: 'bg-gradient-to-br from-gray-50 to-gray-100', text: 'text-gray-800', badge: 'bg-gray-400', border: 'border-gray-200' },
    };
    const c = colorMap[meta.color] || colorMap.gray;
    return (
      <div className={`mb-4 p-4 rounded-xl border-2 ${c.border} ${c.bg} shadow-sm hover:shadow-md transition-shadow`}>
        <div className={`text-sm font-bold ${c.text} mb-3 flex items-center gap-2`}>
          <span className={`w-2 h-2 rounded-full ${c.badge}`}></span>
          {meta.title}
        </div>
        <div className="flex flex-wrap gap-2 mb-3">
          {block.dates.map((d, i) => {
            const dateStr = (d || '').split('T')[0];
            const [year, month, day] = dateStr.split('-');
            return (
              <div key={i} className="bg-white border-2 border-gray-200 px-3 py-2 rounded-lg shadow-sm hover:shadow-md transition-all">
                <div className="text-lg font-bold text-gray-900">{day}</div>
                <div className="text-xs text-gray-500">{`${month}.${year}`}</div>
              </div>
            );
          })}
        </div>
        <div className="text-sm text-gray-700 leading-relaxed bg-white/50 p-2 rounded-lg">
          {block.type || <span className="text-gray-400 italic">Тип уборки не указан</span>}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center">
          <Building2 className="w-8 h-8 mr-3 text-blue-600"/>
          Работы (Дома)
        </h1>
        <div className="flex gap-2">
          <button 
            onClick={() => {
              const url = `${BACKEND_URL}/api/cleaning/missing-data-report`;
              window.open(url, '_blank');
            }}
            className="btn-secondary flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Скачать отчет CSV
          </button>
          <button onClick={fetchHouses} className="btn-primary flex items-center">
            <RefreshCw className="w-4 h-4 mr-2"/>
            Обновить
          </button>
        </div>
      </div>

      {/* Вкладки */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('list')}
            className={`pb-4 px-2 font-medium transition-colors relative ${
              activeTab === 'list'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <List className="w-5 h-5" />
              Список домов
            </div>
          </button>
          <button
            onClick={() => setActiveTab('calendar')}
            className={`pb-4 px-2 font-medium transition-colors relative ${
              activeTab === 'calendar'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <CalendarDays className="w-5 h-5" />
              Календарь уборок
            </div>
          </button>
          <button
            onClick={() => setActiveTab('brigades')}
            className={`pb-4 px-2 font-medium transition-colors relative ${
              activeTab === 'brigades'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              KPI Бригад
            </div>
          </button>
          <button
            onClick={() => setActiveTab('logistics')}
            className={`pb-4 px-2 font-medium transition-colors relative ${
              activeTab === 'logistics'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <Truck className="w-5 h-5" />
              Логистика
            </div>
          </button>
          <button
            onClick={() => setActiveTab('acts')}
            className={`pb-4 px-2 font-medium transition-colors relative ${
              activeTab === 'acts'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <FileCheck className="w-5 h-5" />
              Акты
            </div>
          </button>
        </nav>
      </div>

      {/* Вкладка "Календарь уборок" */}
      {activeTab === 'calendar' && (
        <div className="-m-6">
          <CleaningCalendar />
        </div>
      )}

      {/* Вкладка "KPI Бригад" */}
      {activeTab === 'brigades' && (
        <div className="-m-6">
          <BrigadeStats />
        </div>
      )}

      {/* Вкладка "Логистика" */}
      {activeTab === 'logistics' && (
        <div className="-m-6">
          <Logistics />
        </div>
      )}

      {/* Вкладка "Акты" */}
      {activeTab === 'acts' && (
        <div className="-m-6 p-6">
          <ActsStats />
        </div>
      )}

      {/* Вкладка "Список домов" */}
      {activeTab === 'list' && (
        <>
      <div className="card-modern mb-4 p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-2">
          <input
            type="text"
            placeholder="Адрес / название дома"
            value={activeFilters.search || ''}
            onChange={(e)=>{ setActiveFilters(prev=>({...prev, search: e.target.value })); setPagination(prev=>({...prev, page:1})); }}
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
          />

          <select
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            value={activeFilters.brigade}
            onChange={(e) => { setActiveFilters(prev => ({ ...prev, brigade: e.target.value })); setPagination(prev => ({...prev, page: 1})); }}
          >
            <option value="">Все бригады</option>
            {filters.brigades?.map((b, i) => {
              const value = typeof b === 'object' ? b.id : b;
              const label = typeof b === 'object' ? b.name : b;
              return (<option key={i} value={value}>{label}</option>);
            })}
          </select>

          <DatePicker
            selected={activeFilters.cleaning_date ? new Date(activeFilters.cleaning_date) : null}
            onChange={(date) => {
              const val = date ? format(date, 'yyyy-MM-dd') : '';
              setActiveFilters(prev => ({ ...prev, cleaning_date: val }));
              setPagination(prev => ({...prev, page: 1}));
            }}
            placeholderText="Дата уборки"
            dateFormat="yyyy-MM-dd"
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            locale={ru}
            isClearable
          />
        </div>

        {/* Быстрые фильтры */}
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <span className="text-sm text-gray-500">Быстро:</span>
          <button className="btn-chip" onClick={()=>{ const v=format(new Date(),'yyyy-MM-dd'); setActiveFilters(p=>({...p, cleaning_date:v})); setPagination(p=>({...p,page:1})); }}>Сегодня</button>
          <button className="btn-chip" onClick={()=>{ const d=new Date(); d.setDate(d.getDate()+1); const v=format(d,'yyyy-MM-dd'); setActiveFilters(p=>({...p, cleaning_date:v})); setPagination(p=>({...p,page:1})); }}>Завтра</button>
          <button className="btn-chip" onClick={()=>{ const from=new Date(); const to=new Date(); to.setDate(to.getDate()+7); setActiveFilters(p=>({...p, cleaning_date:'', date_from:format(from,'yyyy-MM-dd'), date_to:format(to,'yyyy-MM-dd')})); setPagination(p=>({...p,page:1})); }}>Неделя</button>
          <button className="btn-chip" onClick={()=>{ const now=new Date(); const from=new Date(now.getFullYear(), now.getMonth(), 1); const to=new Date(now.getFullYear(), now.getMonth()+1, 0); setActiveFilters(p=>({...p, cleaning_date:'', date_from:format(from,'yyyy-MM-dd'), date_to:format(to,'yyyy-MM-dd')})); setPagination(p=>({...p,page:1})); }}>Месяц</button>
          <button className="btn-chip" onClick={()=>{ setActiveFilters(p=>({ brigade:'', status:'', search:'', cleaning_date:'', date_from:'', date_to:'' })); setPagination(p=>({...p,page:1})); }}>Сброс</button>
        </div>

        <div className="flex items-center gap-3 mb-2">
          <span className="text-sm text-gray-500">Показывать:</span>
          {[10,50,100].map(n => (
            <button key={n} onClick={()=>handleLimitChange(n)} className={`px-2 py-1 text-xs rounded-md ${pagination.limit===n? 'bg-blue-600 text-white':'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}>{n}</button>
          ))}
        </div>
      </div>

      {/* Блок общих рекомендаций */}
      <div className="mb-4 p-4 rounded-lg border bg-amber-50">
        <div className="text-sm font-semibold text-amber-800 mb-2">📋 Рекомендации по заполнению данных</div>
        <ul className="text-xs text-amber-900 space-y-1 list-disc pl-5">
          {/* Квартиры */}
          {houses.filter(h=>!h?.apartments || h.apartments === 0).length>0 && (
            <li>Не указано количество квартир у адресов: {houses.filter(h=>!h?.apartments || h.apartments === 0).slice(0,5).map(h=>h.address || h.title).join(', ')}{houses.filter(h=>!h?.apartments || h.apartments === 0).length>5?' и др.':''}</li>
          )}
          {/* Подъезды */}
          {houses.filter(h=>!h?.entrances || h.entrances === 0).length>0 && (
            <li>Не указано количество подъездов у адресов: {houses.filter(h=>!h?.entrances || h.entrances === 0).slice(0,5).map(h=>h.address || h.title).join(', ')}{houses.filter(h=>!h?.entrances || h.entrances === 0).length>5?' и др.':''}</li>
          )}
          {/* Этажи */}
          {houses.filter(h=>!h?.floors || h.floors === 0).length>0 && (
            <li>Не указано количество этажей у адресов: {houses.filter(h=>!h?.floors || h.floors === 0).slice(0,5).map(h=>h.address || h.title).join(', ')}{houses.filter(h=>!h?.floors || h.floors === 0).length>5?' и др.':''}</li>
          )}
          {/* Управляющая компания */}
          {houses.filter(h=>!h?.management_company || h.management_company === '').length>0 && (
            <li>Не указана управляющая компания у адресов: {houses.filter(h=>!h?.management_company || h.management_company === '').slice(0,5).map(h=>h.address || h.title).join(', ')}{houses.filter(h=>!h?.management_company || h.management_company === '').length>5?' и др.':''}</li>
          )}
          {/* Бригада */}
          {houses.filter(h=>!h?.brigade_name || h.brigade_name === 'Бригада не назначена' || h.brigade_name === '').length>0 && (
            <li>Не назначена бригада у адресов: {houses.filter(h=>!h?.brigade_name || h.brigade_name === 'Бригада не назначена' || h.brigade_name === '').slice(0,5).map(h=>h.address || h.title).join(', ')}{houses.filter(h=>!h?.brigade_name || h.brigade_name === 'Бригада не назначена' || h.brigade_name === '').length>5?' и др.':''}</li>
          )}
          {/* График уборки октябрь */}
          {houses.filter(h=>!(h?.cleaning_dates?.october_1?.dates?.length||h?.cleaning_dates?.october_2?.dates?.length)).length>0 && (
            <li>Не заполнен график уборки (октябрь) у адресов: {houses.filter(h=>!(h?.cleaning_dates?.october_1?.dates?.length||h?.cleaning_dates?.october_2?.dates?.length)).slice(0,5).map(h=>h.address || h.title).join(', ')}{houses.filter(h=>!(h?.cleaning_dates?.october_1?.dates?.length||h?.cleaning_dates?.october_2?.dates?.length)).length>5?' и др.':''}</li>
          )}
          {/* График уборки ноябрь */}
          {houses.filter(h=>!(h?.cleaning_dates?.november_1?.dates?.length||h?.cleaning_dates?.november_2?.dates?.length)).length>0 && (
            <li>Не заполнен график уборки (ноябрь) у адресов: {houses.filter(h=>!(h?.cleaning_dates?.november_1?.dates?.length||h?.cleaning_dates?.november_2?.dates?.length)).slice(0,3).map(h=>h.address || h.title).join(', ')}{houses.filter(h=>!(h?.cleaning_dates?.november_1?.dates?.length||h?.cleaning_dates?.november_2?.dates?.length)).length>3?' и др.':''}</li>
          )}
          {/* Периодичность */}
          {houses.filter(h=>!h?.periodicity || h.periodicity === 'не указана').length>0 && (
            <li>Не указана периодичность уборки у адресов: {houses.filter(h=>!h?.periodicity || h.periodicity === 'не указана').slice(0,3).map(h=>h.address || h.title).join(', ')}{houses.filter(h=>!h?.periodicity || h.periodicity === 'не указана').length>3?' и др.':''}</li>
          )}
          {/* Адрес пустой или некорректный */}
          {houses.filter(h=>!h?.address || h.address.length < 10).length>0 && (
            <li>Некорректный или пустой адрес: {houses.filter(h=>!h?.address || h.address.length < 10).slice(0,3).map(h=>h.title || h.id).join(', ')}{houses.filter(h=>!h?.address || h.address.length < 10).length>3?' и др.':''}</li>
          )}
          {/* Если все заполнено */}
          {houses.length > 0 && 
            houses.filter(h=>!h?.apartments || h.apartments === 0).length === 0 &&
            houses.filter(h=>!h?.entrances || h.entrances === 0).length === 0 &&
            houses.filter(h=>!h?.floors || h.floors === 0).length === 0 &&
            houses.filter(h=>!h?.management_company).length === 0 &&
            houses.filter(h=>!h?.brigade_name || h.brigade_name === 'Бригада не назначена').length === 0 &&
            houses.filter(h=>!(h?.cleaning_dates?.october_1?.dates?.length||h?.cleaning_dates?.october_2?.dates?.length)).length === 0 && (
            <li className="text-green-700 font-semibold">✅ Все данные на текущей странице заполнены корректно!</li>
          )}
        </ul>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {houses.map((house) => (
          <div key={house.id} className="card-modern shadow-hover">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-1">{house.title || house.address || 'Без названия'}</h3>
                <p className="text-sm text-gray-500">ID: {house.id}</p>
              </div>
              {house.bitrix_url && (
                <a
                  href={house.bitrix_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 px-3 py-2 bg-orange-100 hover:bg-orange-200 text-orange-700 rounded-lg text-sm font-medium transition-colors"
                  title="Открыть в Битрикс24"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                  Исправить
                </a>
              )}
            </div>

            {/* Статистика */}
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 text-white p-3 rounded-lg text-center">
                <div className="text-lg font-bold">{house.apartments || 0}</div>
                <div className="text-xs text-emerald-100">Квартир</div>
              </div>
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-3 rounded-lg text-center">
                <div className="text-lg font-bold">{house.entrances || 0}</div>
                <div className="text-xs text-blue-100">Подъездов</div>
              </div>
              <div className="bg-gradient-to-r from-orange-500 to-orange-600 text-white p-3 rounded-lg text-center">
                <div className="text-lg font-bold">{house.floors || 0}</div>
                <div className="text-xs text-orange-100">Этажей</div>
              </div>
            </div>

            {/* Стоимость (ежемесячно) */}
            {typeof house.amount_monthly !== 'undefined' && house.amount_monthly !== null && (
              <div className="mb-3">
                <div className="text-sm text-gray-600">Ежемесячно:</div>
                <div className="text-lg font-semibold">
                  {String(house.amount_monthly.toLocaleString('ru-RU', { style: 'currency', currency: house.currency || 'RUB', maximumFractionDigits: 0 }))}
                </div>
              </div>
            )}

            {/* Инфо */}
            <div className="space-y-3 text-base mb-4">
              <div className="flex items-start gap-2">
                <Building2 className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0"/>
                <div className="flex-1">
                  <span className="font-semibold text-gray-700">УК:</span>
                  <div className="text-gray-900">{house.management_company || 'Не указана'}</div>
                </div>
              </div>
              {house.periodicity && (
                <div className="flex items-start gap-2">
                  <Calendar className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0"/>
                  <div className="flex-1">
                    <span className="font-semibold text-gray-700">Периодичность:</span>
                    <div className="text-gray-900 font-medium">{house.periodicity}</div>
                  </div>
                </div>
              )}
              <div className="flex items-start gap-2">
                <Users className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0"/>
                <div className="flex-1">
                  <span className="font-semibold text-gray-700">Ответственный:</span>
                  <div className="text-gray-900">{house.brigade_name || 'Не назначен'}</div>
                </div>
              </div>
            </div>

            {/* График уборки */}
            {house.cleaning_dates && (house.cleaning_dates.october_1 || house.cleaning_dates.october_2) && (
              <div className="mb-3 p-3 rounded-lg border bg-purple-50">
                <div className="text-sm font-semibold text-purple-800 mb-2">График уборок 2025: Октябрь</div>
                {house.cleaning_dates.october_1 && <MonthBlock k="october_1" block={house.cleaning_dates.october_1} />}
                {house.cleaning_dates.october_2 && <MonthBlock k="october_2" block={house.cleaning_dates.october_2} />}
              </div>
            )}

            <div className="flex flex-col gap-2">
              <div className="flex gap-2">
                <button
                  onClick={() => { setSelectedHouse(house); setShowScheduleModal(true); }}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg text-sm"
                >График</button>

                <button
                  onClick={() => fetchHouseDetails(house.id)}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-sm flex items-center justify-center gap-1"
                >
                  <MapPin className="w-4 h-4"/> Детали
                </button>
              </div>
              
              <button
                onClick={() => {
                  setSelectedHouseForAct(house);
                  setShowActSignModal(true);
                }}
                className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-3 py-2 rounded-lg text-sm flex items-center justify-center gap-2 transition-all"
                data-testid="sign-act-btn"
              >
                <FileCheck className="w-4 h-4" />
                Акт подписан
              </button>

              {house.bitrix_url && (
                <a 
                  href={house.bitrix_url} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="w-full bg-gray-800 hover:bg-black text-white px-3 py-2 rounded-lg text-sm text-center"
                >
                  Bitrix24
                </a>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Schedule Modal */}
      {showScheduleModal && selectedHouse && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">График уборки: {selectedHouse.title || selectedHouse.address}</h2>
                <button onClick={() => setShowScheduleModal(false)} className="p-2 rounded hover:bg-gray-100">✕</button>
              </div>
              <div className="space-y-3">
                {Object.entries(selectedHouse.cleaning_dates || {}).map(([k, v]) => <MonthBlock key={k} k={k} block={v} />)}
              </div>
              <div className="mt-4 text-right">
                <button onClick={() => setShowScheduleModal(false)} className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg">Закрыть</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Details Modal */}
      {showDetailsModal && houseDetails && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Дом: {houseDetails.house.title}
                  {houseDetails.house.brigade_name && (
                    <span className="ml-3 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                      {houseDetails.house.brigade_name}
                    </span>
                  )}
                </h2>
                <button onClick={() => setShowDetailsModal(false)} className="p-2 rounded hover:bg-gray-100">✕</button>
              </div>
              <div className="space-y-2 text-sm">
                <div><span className="font-medium text-gray-600">Адрес:</span> {houseDetails.house.address}</div>
                <div><span className="font-medium text-gray-600">Ответственный:</span> {houseDetails.house.brigade_name || (typeof houseDetails.house.brigade === 'object' ? houseDetails.house.brigade.name : houseDetails.house.brigade) || 'Не назначен'}</div>
                <div><span className="font-medium text-gray-600">Статус:</span> {houseDetails.house.status || 'Не указан'}</div>
                {houseDetails.house.bitrix_url && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <a className="inline-flex items-center gap-2 text-blue-700 hover:text-blue-800 hover:underline" href={houseDetails.house.bitrix_url} target="_blank" rel="noopener noreferrer">
                        <span>Открыть в Bitrix</span>
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h6m0 0v6m0-6L10 16M7 7h.01" /></svg>
                      </a>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {houseDetails.house.elder_contact && (
                        <div className="p-3 rounded-lg border bg-white shadow-sm">
                          <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">Старший дома</div>
                          <div className="text-sm font-medium text-gray-900">{houseDetails.house.elder_contact.name || '—'}</div>
                          {houseDetails.house.elder_contact.phones && houseDetails.house.elder_contact.phones.length>0 && (
                            <div className="mt-1 text-sm text-gray-700">☎ <a className="hover:underline" href={`tel:${houseDetails.house.elder_contact.phones[0]}`}>{houseDetails.house.elder_contact.phones[0]}</a></div>
                          )}
                          {houseDetails.house.elder_contact.emails && houseDetails.house.elder_contact.emails.length>0 && (
                            <div className="mt-1 text-sm text-gray-700">✉ <a className="hover:underline" href={`mailto:${houseDetails.house.elder_contact.emails[0]}`}>{houseDetails.house.elder_contact.emails[0]}</a></div>
                          )}
                        </div>
                      )}
                      {houseDetails.house.company && (
                        <div className="p-3 rounded-lg border bg-white shadow-sm">
                          <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">УК</div>
                          <div className="text-sm font-medium text-gray-900">{houseDetails.house.company.title || '—'}</div>
                          {houseDetails.house.company.phones && houseDetails.house.company.phones.length>0 && (
                            <div className="mt-1 text-sm text-gray-700">☎ <a className="hover:underline" href={`tel:${houseDetails.house.company.phones[0]}`}>{houseDetails.house.company.phones[0]}</a></div>
                          )}
                          {houseDetails.house.company.emails && houseDetails.house.company.emails.length>0 && (
                            <div className="mt-1 text-sm text-gray-700">✉ <a className="hover:underline" href={`mailto:${houseDetails.house.company.emails[0]}`}>{houseDetails.house.company.emails[0]}</a></div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
              {houseDetails.house.cleaning_dates && (
                <div className="mt-4">
                  <div className="font-medium mb-2">График уборки</div>
                  {Object.entries(houseDetails.house.cleaning_dates).map(([k, v]) => <MonthBlock key={k} k={k} block={v} />)}
                  {houseDetails.house.periodicity && (
                    <div className="mt-2 text-sm"><span className="font-medium">Периодичность:</span> {houseDetails.house.periodicity}</div>
                  )}
                </div>
              )}
              <div className="mt-4 flex justify-end gap-3">
                <button onClick={() => { setShowEditModal(true); setShowDetailsModal(false); }} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">Редактировать</button>
                <button onClick={() => setShowDetailsModal(false)} className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg">Закрыть</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {notification && (
        <div className={`fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 text-white ${notification.type === 'success' ? 'bg-green-500' : notification.type === 'error' ? 'bg-red-500' : 'bg-blue-500'}`}>
          {notification.message}
        </div>
      )}

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="mt-6 flex flex-wrap items-center gap-2 justify-center">
          {Array.from({ length: pagination.pages }).map((_, i) => (
            <button key={i} onClick={() => handlePageChange(i+1)} className={`px-3 py-1 rounded border text-sm ${pagination.page === (i+1) ? 'bg-blue-600 text-white border-blue-600' : 'bg-white hover:bg-gray-50'}`}>{i+1}</button>
          ))}
        </div>
      )}

      {/* Edit Modal */}
      <EditHouseModal
        house={houseDetails?.house}
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        onSave={(updatedHouse) => {
          setHouseDetails({ house: updatedHouse });
          setHouses(houses.map(h => h.id === updatedHouse.id ? updatedHouse : h));
          setShowEditModal(false);
          setNotification({ type: 'success', message: 'Данные успешно обновлены!' });
          setTimeout(() => setNotification(null), 3000);
        }}
      />

      {/* Act Sign Modal */}
      <ActSignModal
        house={selectedHouseForAct}
        isOpen={showActSignModal}
        onClose={() => {
          setShowActSignModal(false);
          setSelectedHouseForAct(null);
        }}
        onSuccess={(data) => {
          showNotification(`✅ Акт подписан! Уборок в месяце: ${data.cleaning_count}`, 'success');
        }}
      />
      </>
      )}
    </div>
  );
};

export default Works;