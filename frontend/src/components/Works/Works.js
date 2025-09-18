import React, { useEffect, useRef, useState } from 'react';
import { Building2, Users, Calendar, MapPin, RefreshCw } from 'lucide-react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

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
  const [houses, setHouses] = useState([]);
  const [pagination, setPagination] = useState({ total: 0, page: 1, limit: 50, pages: 0 });
  const [filters, setFilters] = useState({ brigades: [], statuses: [] });
  const [loading, setLoading] = useState(false);
  const [activeFilters, setActiveFilters] = useState({ brigade: '', management_company: '', status: '', search: '', cleaning_date: '' });
  const [notification, setNotification] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [houseDetails, setHouseDetails] = useState(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedHouse, setSelectedHouse] = useState(null);
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
      setFilters(data || { brigades: [], management_companies: [], statuses: [] });
    } catch (e) {
      console.error('filters error', e);
    }
  };

  const fetchHouses = async () => {
    try {
      const q = new URLSearchParams();
      Object.entries(activeFilters).forEach(([k, v]) => { if (v) q.append(k, v); });
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
      <div key={key} className={`mb-3 p-3 rounded-lg border ${c.bg}`}>
        <div className={`text-xs font-medium ${c.text} mb-2`}>{meta.title}</div>
        <div className="flex flex-wrap gap-1 mb-2">
          {block.dates.map((d, i) => (
            <span key={i} className="bg-white border px-2 py-1 rounded text-xs">{d}</span>
          ))}
        </div>
        <div className="text-sm text-gray-800 leading-snug">{block.type}</div>
      </div>
    );
  };

  return (
    <div className="p-2 max-w-7xl mx-auto">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold flex items-center"><Building2 className="w-5 h-5 mr-2 text-blue-600"/>Работы (Дома)</h1>
        <button onClick={fetchHouses} className="btn-primary flex items-center"><RefreshCw className="w-4 h-4 mr-2"/>Обновить</button>
      </div>

      <div className="card-modern mb-4 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-2">
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
            {filters.brigades?.map((b, i) => (<option key={i} value={b}>{b}</option>))}
          </select>

          <select
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            value={activeFilters.management_company}
            onChange={(e) => { setActiveFilters(prev => ({ ...prev, management_company: e.target.value })); setPagination(prev => ({...prev, page: 1})); }}
          >
            <option value="">Все УК</option>
            {filters.management_companies?.map((c, i) => (<option key={i} value={c}>{c}</option>))}
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

        <div className="flex items-center gap-3 mb-2">
          <span className="text-sm text-gray-500">Показывать:</span>
          {[50,100,200,500,1000].map(n => (
            <button key={n} onClick={()=>handleLimitChange(n)} className={`px-2 py-1 text-xs rounded-md ${pagination.limit===n? 'bg-blue-600 text-white':'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}>{n}</button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {houses.map((house) => (
          <div key={house.id} className="card-modern shadow-hover">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-lg font-semibold">{house.title || house.address || 'Без названия'}</h3>
                <p className="text-xs text-gray-500">ID: {house.id}</p>
              </div>
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

            {/* Инфо */}
            <div className="space-y-2 text-sm mb-3">
              <div className="flex items-center gap-2"><Building2 className="w-4 h-4 text-blue-600"/><span className="font-medium">УК:</span><span>{house.management_company || 'Не указана'}</span></div>
              {house.periodicity && (<div className="flex items-center gap-2"><Calendar className="w-4 h-4 text-purple-600"/><span className="font-medium">Периодичность:</span><span>{house.periodicity}</span></div>)}
              <div className="flex items-center gap-2"><Users className="w-4 h-4 text-green-600"/><span className="font-medium">Бригада №:</span><span>{house.brigade || 'Бригада не назначена'}</span></div>
            </div>

            {/* График уборки */}
            {house.cleaning_dates && (house.cleaning_dates.september_1 || house.cleaning_dates.september_2) && (
              <div className="mb-3 p-3 rounded-lg border bg-purple-50">
                <div className="text-sm font-semibold text-purple-800 mb-2">График уборок 2025</div>
                {renderMonthBlock('september_1', house.cleaning_dates.september_1)}
                {renderMonthBlock('september_2', house.cleaning_dates.september_2)}
              </div>
            )}

            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => { setSelectedHouse(house); setShowScheduleModal(true); }}
                className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg text-sm"
              >Посмотреть график</button>

              <button
                onClick={() => fetchHouseDetails(house.id)}
                className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-sm flex items-center justify-center gap-1"
              >
                <MapPin className="w-4 h-4"/> Детали
              </button>

              {house.bitrix_url && (
                <a href={house.bitrix_url} target="_blank" rel="noopener noreferrer" className="bg-gray-800 hover:bg-black text-white px-3 py-2 rounded-lg text-sm text-center">Открыть в Bitrix24</a>
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
                {Object.entries(selectedHouse.cleaning_dates || {}).map(([k, v]) => renderMonthBlock(k, v))}
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
                <h2 className="text-xl font-semibold">Дом: {houseDetails.house.title}</h2>
                <button onClick={() => setShowDetailsModal(false)} className="p-2 rounded hover:bg-gray-100">✕</button>
              </div>
              <div className="space-y-2 text-sm">
                <div><span className="font-medium text-gray-600">Адрес:</span> {houseDetails.house.address}</div>
                <div><span className="font-medium text-gray-600">Бригада:</span> {houseDetails.house.brigade}</div>
                <div><span className="font-medium text-gray-600">Статус:</span> {houseDetails.house.status}</div>
                {houseDetails.house.bitrix_url && (
                  <div><a className="text-blue-600 hover:underline" href={houseDetails.house.bitrix_url} target="_blank" rel="noopener noreferrer">Открыть в Bitrix</a></div>
                )}
              </div>
              {houseDetails.house.cleaning_dates && (
                <div className="mt-4">
                  <div className="font-medium mb-2">График уборки</div>
                  {Object.entries(houseDetails.house.cleaning_dates).map(([k, v]) => renderMonthBlock(k, v))}
                  {houseDetails.house.periodicity && (
                    <div className="mt-2 text-sm"><span className="font-medium">Периодичность:</span> {houseDetails.house.periodicity}</div>
                  )}
                </div>
              )}
              <div className="mt-4 text-right">
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
    </div>
  );
};

export default Works;