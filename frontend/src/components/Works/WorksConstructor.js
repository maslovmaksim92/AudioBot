import React, { useState, useEffect } from 'react';
import './WorksConstructor.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

const WorksConstructor = () => {
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingHouse, setEditingHouse] = useState(null);
  const [filters, setFilters] = useState({
    brigade: '',
    company: '',
    search: ''
  });

  // Форма дома
  const [houseForm, setHouseForm] = useState({
    address: '',
    apartments_count: '',
    entrances_count: '',
    floors_count: '',
    company_title: '',
    brigade_number: '',
    tariff: '',
    elder_contact: '',
    notes: ''
  });

  useEffect(() => {
    loadHouses();
  }, []);

  const loadHouses = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/houses?limit=500`);
      if (res.ok) {
        const data = await res.json();
        setHouses(data);
      }
    } catch (e) {
      console.error('Error loading houses:', e);
    } finally {
      setLoading(false);
    }
  };

  const syncBitrix24 = async () => {
    if (!window.confirm('Начать синхронизацию с Bitrix24? Это может занять несколько минут.')) {
      return;
    }

    try {
      const res = await fetch(`${BACKEND_URL}/api/houses/sync-bitrix24`, {
        method: 'POST'
      });

      if (res.ok) {
        alert('✅ Синхронизация запущена в фоновом режиме. Обновите список через 2-3 минуты.');
        setTimeout(loadHouses, 180000); // Обновить через 3 минуты
      } else {
        alert('❌ Ошибка запуска синхронизации');
      }
    } catch (e) {
      alert('❌ Ошибка подключения к серверу');
    }
  };

  const handleSaveHouse = async () => {
    try {
      const url = editingHouse 
        ? `${BACKEND_URL}/api/houses/${editingHouse.id}`
        : `${BACKEND_URL}/api/houses`;
      
      const method = editingHouse ? 'PATCH' : 'POST';

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(houseForm)
      });

      if (res.ok) {
        alert(editingHouse ? '✅ Дом обновлен' : '✅ Дом добавлен');
        setShowAddModal(false);
        setEditingHouse(null);
        resetForm();
        loadHouses();
      } else {
        alert('❌ Ошибка сохранения');
      }
    } catch (e) {
      alert('❌ Ошибка подключения к серверу');
    }
  };

  const handleDeleteHouse = async (houseId) => {
    if (!window.confirm('Удалить дом?')) return;

    try {
      const res = await fetch(`${BACKEND_URL}/api/houses/${houseId}`, {
        method: 'DELETE'
      });

      if (res.ok) {
        alert('✅ Дом удален');
        loadHouses();
      } else {
        alert('❌ Ошибка удаления');
      }
    } catch (e) {
      alert('❌ Ошибка подключения к серверу');
    }
  };

  const openAddModal = () => {
    resetForm();
    setEditingHouse(null);
    setShowAddModal(true);
  };

  const openEditModal = (house) => {
    setHouseForm({
      address: house.address || '',
      apartments_count: house.apartments_count || '',
      entrances_count: house.entrances_count || '',
      floors_count: house.floors_count || '',
      company_title: house.company_title || '',
      brigade_number: house.brigade_number || '',
      tariff: house.tariff || '',
      elder_contact: house.elder_contact || '',
      notes: house.notes || ''
    });
    setEditingHouse(house);
    setShowAddModal(true);
  };

  const resetForm = () => {
    setHouseForm({
      address: '',
      apartments_count: '',
      entrances_count: '',
      floors_count: '',
      company_title: '',
      brigade_number: '',
      tariff: '',
      elder_contact: '',
      notes: ''
    });
  };

  const filteredHouses = houses.filter(house => {
    if (filters.brigade && house.brigade_number !== filters.brigade) return false;
    if (filters.company && !house.company_title?.toLowerCase().includes(filters.company.toLowerCase())) return false;
    if (filters.search && !house.address?.toLowerCase().includes(filters.search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="works-constructor">
      <div className="constructor-header">
        <h1>🏠 Управление домами - Конструктор</h1>
        <div className="header-actions">
          <button onClick={syncBitrix24} className="btn btn-sync">
            🔄 Синхронизация Bitrix24
          </button>
          <button onClick={openAddModal} className="btn btn-add">
            ➕ Добавить дом
          </button>
        </div>
      </div>

      {/* Фильтры */}
      <div className="filters">
        <input
          type="text"
          placeholder="🔍 Поиск по адресу..."
          value={filters.search}
          onChange={(e) => setFilters({...filters, search: e.target.value})}
          className="filter-input"
        />
        
        <select
          value={filters.brigade}
          onChange={(e) => setFilters({...filters, brigade: e.target.value})}
          className="filter-select"
        >
          <option value="">Все бригады</option>
          {[1,2,3,4,5,6,7].map(n => (
            <option key={n} value={n.toString()}>Бригада {n}</option>
          ))}
        </select>

        <input
          type="text"
          placeholder="УК..."
          value={filters.company}
          onChange={(e) => setFilters({...filters, company: e.target.value})}
          className="filter-input"
        />
      </div>

      {/* Список домов */}
      {loading ? (
        <div className="loading">⏳ Загрузка...</div>
      ) : (
        <div className="houses-grid">
          {filteredHouses.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🏠</div>
              <p>Нет домов. Синхронизируйте с Bitrix24 или добавьте вручную.</p>
            </div>
          ) : (
            filteredHouses.map(house => (
              <div key={house.id} className="house-card">
                <div className="house-header">
                  <h3>{house.address}</h3>
                  <div className="house-actions">
                    <button onClick={() => openEditModal(house)} className="icon-btn">✏️</button>
                    <button onClick={() => handleDeleteHouse(house.id)} className="icon-btn delete">🗑️</button>
                  </div>
                </div>
                
                <div className="house-info">
                  <div className="info-row">
                    <span className="label">Квартир:</span>
                    <span>{house.apartments_count || '—'}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Подъездов:</span>
                    <span>{house.entrances_count || '—'}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Этажей:</span>
                    <span>{house.floors_count || '—'}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Бригада:</span>
                    <span className="badge">{house.brigade_number || '—'}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">УК:</span>
                    <span className="small">{house.company_title || '—'}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Тариф:</span>
                    <span>{house.tariff || '—'}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Модальное окно добавления/редактирования */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingHouse ? '✏️ Редактировать дом' : '➕ Добавить дом'}</h2>
              <button onClick={() => setShowAddModal(false)} className="close-btn">✕</button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label>Адрес *</label>
                <input
                  type="text"
                  value={houseForm.address}
                  onChange={(e) => setHouseForm({...houseForm, address: e.target.value})}
                  placeholder="ул. Пример, д. 1"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Квартир</label>
                  <input
                    type="number"
                    value={houseForm.apartments_count}
                    onChange={(e) => setHouseForm({...houseForm, apartments_count: e.target.value})}
                  />
                </div>

                <div className="form-group">
                  <label>Подъездов</label>
                  <input
                    type="number"
                    value={houseForm.entrances_count}
                    onChange={(e) => setHouseForm({...houseForm, entrances_count: e.target.value})}
                  />
                </div>

                <div className="form-group">
                  <label>Этажей</label>
                  <input
                    type="number"
                    value={houseForm.floors_count}
                    onChange={(e) => setHouseForm({...houseForm, floors_count: e.target.value})}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>УК</label>
                <input
                  type="text"
                  value={houseForm.company_title}
                  onChange={(e) => setHouseForm({...houseForm, company_title: e.target.value})}
                  placeholder="Название управляющей компании"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Бригада</label>
                  <select
                    value={houseForm.brigade_number}
                    onChange={(e) => setHouseForm({...houseForm, brigade_number: e.target.value})}
                  >
                    <option value="">Не выбрано</option>
                    {[1,2,3,4,5,6,7].map(n => (
                      <option key={n} value={n.toString()}>Бригада {n}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Тариф</label>
                  <input
                    type="text"
                    value={houseForm.tariff}
                    onChange={(e) => setHouseForm({...houseForm, tariff: e.target.value})}
                    placeholder="2 раза в месяц"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Контакт старшего</label>
                <input
                  type="text"
                  value={houseForm.elder_contact}
                  onChange={(e) => setHouseForm({...houseForm, elder_contact: e.target.value})}
                  placeholder="+7 xxx xxx xx xx"
                />
              </div>

              <div className="form-group">
                <label>Заметки</label>
                <textarea
                  value={houseForm.notes}
                  onChange={(e) => setHouseForm({...houseForm, notes: e.target.value})}
                  rows="3"
                  placeholder="Дополнительная информация..."
                />
              </div>
            </div>

            <div className="modal-footer">
              <button onClick={() => setShowAddModal(false)} className="btn btn-cancel">
                Отмена
              </button>
              <button onClick={handleSaveHouse} className="btn btn-save">
                {editingHouse ? 'Сохранить' : 'Добавить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorksConstructor;
