import React, { useEffect, useRef, useState } from 'react';
import { Building2, Users, Calendar, MapPin, RefreshCw } from 'lucide-react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

const Works = () => {
  const [houses, setHouses] = useState([]);
  const [pagination, setPagination] = useState({ total: 0, page: 1, limit: 50, pages: 0 });
  const [filters, setFilters] = useState({ brigades: [], management_companies: [], statuses: [] });
  const [loading, setLoading] = useState(false);
  const [activeFilters, setActiveFilters] = useState({ brigade: '', management_company: '', status: '', search: '', cleaning_date: '' });
  const [notification, setNotification] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [houseDetails, setHouseDetails] = useState(null);
  const detailsLoadingRef = useRef(false);

  useEffect(() => { fetchInitial(); }, []);
  useEffect(() => { fetchHouses(); }, [activeFilters, pagination.page, pagination.limit]);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 2500);
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

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center"><Building2 className="w-6 h-6 mr-2 text-blue-600"/>Работы (Дома)</h1>
        <button onClick={fetchHouses} className="btn-primary flex items-center"><RefreshCw className="w-4 h-4 mr-2"/>Обновить</button>
      </div>

      <div className="card-modern mb-6 p-4">
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
          <div key={house.id} className="card-modern">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-lg font-semibold">{house.title || house.address || 'Без названия'}</h3>
                <p className="text-sm text-gray-500">ID: {house.id}</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center mb-3">
              <div className="bg-emerald-500 text-white p-2 rounded-lg">
                <div className="text-lg font-bold">{house.apartments || 0}</div>
                <div className="text-xs">Квартир</div>
              </div>
              <div className="bg-blue-500 text-white p-2 rounded-lg">
                <div className="text-lg font-bold">{house.entrances || 0}</div>
                <div className="text-xs">Подъездов</div>
              </div>
              <div className="bg-orange-500 text-white p-2 rounded-lg">
                <div className="text-lg font-bold">{house.floors || 0}</div>
                <div className="text-xs">Этажей</div>
              </div>
            </div>

            <div className="space-y-1 text-sm mb-3">
              <div className="flex items-center gap-2"><Users className="w-4 h-4 text-green-600"/><span className="font-medium">Бригада:</span><span>{house.brigade || 'Не назначена'}</span></div>
              <div className="flex items-center gap-2"><Building2 className="w-4 h-4 text-blue-600"/><span className="font-medium">УК:</span><span>{house.management_company || 'Не указана'}</span></div>
              {house.periodicity && (
                <div className="flex items-center gap-2"><Calendar className="w-4 h-4 text-purple-600"/><span className="font-medium">Периодичность:</span><span>{house.periodicity}</span></div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => fetchHouseDetails(house.id)} className="bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded-lg text-sm flex items-center justify-center gap-1">
                <MapPin className="w-4 h-4"/> Детали
              </button>
              {house.bitrix_url && (
                <a href={house.bitrix_url} target="_blank" rel="noopener noreferrer" className="bg-gray-800 hover:bg-black text-white px-3 py-2 rounded-lg text-sm text-center">Открыть в Bitrix</a>
              )}
            </div>
          </div>
        ))}
      </div>

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
                  {Object.entries(houseDetails.house.cleaning_dates).map(([k, v]) => (
                    (v?.dates?.length) ? (
                      <div key={k} className="mb-2 border rounded p-3">
                        <div className="text-sm text-gray-600 mb-1">{k}</div>
                        <div className="flex flex-wrap gap-1 mb-1">
                          {v.dates.map((d, i) => (<span key={i} className="bg-gray-100 px-2 py-1 rounded text-xs">{d}</span>))}
                        </div>
                        <div className="text-sm text-gray-800">{v.type}</div>
                      </div>
                    ) : null
                  ))}
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
    </div>
  );
};

export default Works;