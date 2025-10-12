import React, { useState, useEffect } from 'react';
import { X, Save, Plus, Trash2 } from 'lucide-react';

const EditHouseModal = ({ house, isOpen, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    apartments: 0,
    floors: 0,
    entrances: 0,
    brigade_id: '',
    elder_name: '',
    elder_phone: '',
    elder_comment: '',
    october_1_dates: [],
    october_1_type: '',
    october_2_dates: [],
    october_2_type: '',
    november_1_dates: [],
    november_1_type: '',
    november_2_dates: [],
    november_2_type: '',
    december_1_dates: [],
    december_1_type: '',
    december_2_dates: [],
    december_2_type: '',
  });

  const [brigades, setBrigades] = useState([]);
  const [cleaningTypes, setCleaningTypes] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && house) {
      fetchBrigades();
      fetchCleaningTypes();
    }
  }, [isOpen, house]);

  // Отдельный эффект для инициализации формы после загрузки типов
  useEffect(() => {
    if (isOpen && house && cleaningTypes.length > 0) {
      initializeFormData();
    }
  }, [isOpen, house, cleaningTypes]);

  const fetchBrigades = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/cleaning/brigades`);
      const data = await response.json();
      setBrigades(data.brigades || []);
    } catch (error) {
      console.error('Error fetching brigades:', error);
    }
  };

  const fetchCleaningTypes = async () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/cleaning/cleaning-types`);
      const data = await response.json();
      setCleaningTypes(data.types || []);
    } catch (error) {
      console.error('Error fetching cleaning types:', error);
    }
  };

  const findTypeIdByName = (typeName) => {
    if (!typeName || cleaningTypes.length === 0) return '';
    const type = cleaningTypes.find(t => t.name === typeName);
    return type ? type.id : '';
  };

  const initializeFormData = () => {
    if (!house) return;
    
    const cd = house.cleaning_dates || {};
    
    setFormData({
      apartments: house.apartments || 0,
      floors: house.floors || 0,
      entrances: house.entrances || 0,
      brigade_id: house.assigned?.id || '',
      elder_name: house.elder_contact?.name || '',
      elder_phone: house.elder_contact?.phones?.[0] || '',
      elder_comment: '',
      october_1_dates: cd.october_1?.dates || [],
      october_1_type: findTypeIdByName(cd.october_1?.type) || '',
      october_2_dates: cd.october_2?.dates || [],
      october_2_type: findTypeIdByName(cd.october_2?.type) || '',
      november_1_dates: cd.november_1?.dates || [],
      november_1_type: findTypeIdByName(cd.november_1?.type) || '',
      november_2_dates: cd.november_2?.dates || [],
      november_2_type: findTypeIdByName(cd.november_2?.type) || '',
      december_1_dates: cd.december_1?.dates || [],
      december_1_type: findTypeIdByName(cd.december_1?.type) || '',
      december_2_dates: cd.december_2?.dates || [],
      december_2_type: findTypeIdByName(cd.december_2?.type) || '',
    });
  };

  const addDate = (field) => {
    setFormData({ ...formData, [field]: [...formData[field], ''] });
  };

  const removeDate = (field, index) => {
    const newDates = formData[field].filter((_, i) => i !== index);
    setFormData({ ...formData, [field]: newDates });
  };

  const updateDate = (field, index, value) => {
    const newDates = [...formData[field]];
    newDates[index] = value;
    setFormData({ ...formData, [field]: newDates });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/cleaning/house/${house.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const result = await response.json();
      if (result.success) {
        onSave(result.house);
        onClose();
      } else {
        alert('Ошибка при сохранении: ' + (result.error || 'Неизвестная ошибка'));
      }
    } catch (error) {
      console.error('Error saving house:', error);
      alert('Ошибка при сохранении данных');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold">Редактировать дом</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Основные параметры */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Квартиры</label>
              <input
                type="number"
                value={formData.apartments}
                onChange={(e) => setFormData({ ...formData, apartments: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Этажи</label>
              <input
                type="number"
                value={formData.floors}
                onChange={(e) => setFormData({ ...formData, floors: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Подъезды</label>
              <input
                type="number"
                value={formData.entrances}
                onChange={(e) => setFormData({ ...formData, entrances: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Бригада */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ответственный (бригада)</label>
            <select
              value={formData.brigade_id}
              onChange={(e) => setFormData({ ...formData, brigade_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Не назначена</option>
              {brigades.map((brigade) => (
                <option key={brigade.id} value={brigade.id}>{brigade.name}</option>
              ))}
            </select>
          </div>

          {/* Старший дома */}
          <div className="border rounded-lg p-4 bg-blue-50">
            <h3 className="font-semibold mb-3">Старший дома</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ФИО</label>
                <input
                  type="text"
                  value={formData.elder_name}
                  onChange={(e) => setFormData({ ...formData, elder_name: e.target.value })}
                  placeholder="Введите ФИО старшего"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Номер телефона</label>
                <input
                  type="tel"
                  value={formData.elder_phone}
                  onChange={(e) => setFormData({ ...formData, elder_phone: e.target.value })}
                  placeholder="+7 (XXX) XXX-XX-XX"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Комментарий</label>
                <textarea
                  value={formData.elder_comment}
                  onChange={(e) => setFormData({ ...formData, elder_comment: e.target.value })}
                  placeholder="Дополнительная информация"
                  rows="2"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* График уборки - Октябрь */}
          <div className="border rounded-lg p-4 bg-gray-50">
            <h3 className="font-semibold mb-3 text-lg">График уборки - Октябрь 2025</h3>
            
            <div className="space-y-4">
              {/* Октябрь 1 */}
              <div className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-medium mb-2">Период 1</h4>
                <div className="space-y-2 mb-3">
                  <label className="block text-sm font-medium text-gray-700">Даты:</label>
                  {formData.october_1_dates.map((date, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="date"
                        value={date}
                        onChange={(e) => updateDate('october_1_dates', index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                      />
                      <button type="button" onClick={() => removeDate('october_1_dates', index)} className="px-3 py-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <button type="button" onClick={() => addDate('october_1_dates')} className="px-3 py-2 bg-blue-100 text-blue-600 rounded-md hover:bg-blue-200 text-sm flex items-center gap-1">
                    <Plus className="w-4 h-4" /> Добавить дату
                  </button>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Тип уборки:</label>
                  <select
                    value={formData.october_1_type}
                    onChange={(e) => setFormData({ ...formData, october_1_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Выберите тип</option>
                    {cleaningTypes.map((type) => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Октябрь 2 */}
              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="font-medium mb-2">Период 2</h4>
                <div className="space-y-2 mb-3">
                  <label className="block text-sm font-medium text-gray-700">Даты:</label>
                  {formData.october_2_dates.map((date, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="date"
                        value={date}
                        onChange={(e) => updateDate('october_2_dates', index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                      />
                      <button type="button" onClick={() => removeDate('october_2_dates', index)} className="px-3 py-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <button type="button" onClick={() => addDate('october_2_dates')} className="px-3 py-2 bg-blue-100 text-blue-600 rounded-md hover:bg-blue-200 text-sm flex items-center gap-1">
                    <Plus className="w-4 h-4" /> Добавить дату
                  </button>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Тип уборки:</label>
                  <select
                    value={formData.october_2_type}
                    onChange={(e) => setFormData({ ...formData, october_2_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Выберите тип</option>
                    {cleaningTypes.map((type) => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* График уборки - Ноябрь */}
          <div className="border rounded-lg p-4 bg-gray-50">
            <h3 className="font-semibold mb-3 text-lg">График уборки - Ноябрь 2025</h3>
            
            <div className="space-y-4">
              {/* Ноябрь 1 */}
              <div className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-medium mb-2">Период 1</h4>
                <div className="space-y-2 mb-3">
                  <label className="block text-sm font-medium text-gray-700">Даты:</label>
                  {formData.november_1_dates.map((date, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="date"
                        value={date}
                        onChange={(e) => updateDate('november_1_dates', index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                      />
                      <button type="button" onClick={() => removeDate('november_1_dates', index)} className="px-3 py-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <button type="button" onClick={() => addDate('november_1_dates')} className="px-3 py-2 bg-blue-100 text-blue-600 rounded-md hover:bg-blue-200 text-sm flex items-center gap-1">
                    <Plus className="w-4 h-4" /> Добавить дату
                  </button>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Тип уборки:</label>
                  <select
                    value={formData.november_1_type}
                    onChange={(e) => setFormData({ ...formData, november_1_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Выберите тип</option>
                    {cleaningTypes.map((type) => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Ноябрь 2 */}
              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="font-medium mb-2">Период 2</h4>
                <div className="space-y-2 mb-3">
                  <label className="block text-sm font-medium text-gray-700">Даты:</label>
                  {formData.november_2_dates.map((date, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="date"
                        value={date}
                        onChange={(e) => updateDate('november_2_dates', index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                      />
                      <button type="button" onClick={() => removeDate('november_2_dates', index)} className="px-3 py-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <button type="button" onClick={() => addDate('november_2_dates')} className="px-3 py-2 bg-blue-100 text-blue-600 rounded-md hover:bg-blue-200 text-sm flex items-center gap-1">
                    <Plus className="w-4 h-4" /> Добавить дату
                  </button>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Тип уборки:</label>
                  <select
                    value={formData.november_2_type}
                    onChange={(e) => setFormData({ ...formData, november_2_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Выберите тип</option>
                    {cleaningTypes.map((type) => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* График уборки - Декабрь */}
          <div className="border rounded-lg p-4 bg-gray-50">
            <h3 className="font-semibold mb-3 text-lg">График уборки - Декабрь 2025</h3>
            
            <div className="space-y-4">
              {/* Декабрь 1 */}
              <div className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-medium mb-2">Период 1</h4>
                <div className="space-y-2 mb-3">
                  <label className="block text-sm font-medium text-gray-700">Даты:</label>
                  {formData.december_1_dates.map((date, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="date"
                        value={date}
                        onChange={(e) => updateDate('december_1_dates', index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                      />
                      <button type="button" onClick={() => removeDate('december_1_dates', index)} className="px-3 py-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <button type="button" onClick={() => addDate('december_1_dates')} className="px-3 py-2 bg-blue-100 text-blue-600 rounded-md hover:bg-blue-200 text-sm flex items-center gap-1">
                    <Plus className="w-4 h-4" /> Добавить дату
                  </button>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Тип уборки:</label>
                  <select
                    value={formData.december_1_type}
                    onChange={(e) => setFormData({ ...formData, december_1_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Выберите тип</option>
                    {cleaningTypes.map((type) => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Декабрь 2 */}
              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="font-medium mb-2">Период 2</h4>
                <div className="space-y-2 mb-3">
                  <label className="block text-sm font-medium text-gray-700">Даты:</label>
                  {formData.december_2_dates.map((date, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="date"
                        value={date}
                        onChange={(e) => updateDate('december_2_dates', index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                      />
                      <button type="button" onClick={() => removeDate('december_2_dates', index)} className="px-3 py-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <button type="button" onClick={() => addDate('december_2_dates')} className="px-3 py-2 bg-blue-100 text-blue-600 rounded-md hover:bg-blue-200 text-sm flex items-center gap-1">
                    <Plus className="w-4 h-4" /> Добавить дату
                  </button>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Тип уборки:</label>
                  <select
                    value={formData.december_2_type}
                    onChange={(e) => setFormData({ ...formData, december_2_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Выберите тип</option>
                    {cleaningTypes.map((type) => (
                      <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Кнопки */}
          <div className="flex justify-end gap-3 pt-4 border-t sticky bottom-0 bg-white">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              disabled={loading}
            >
              Отмена
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              disabled={loading}
            >
              <Save className="w-4 h-4" />
              {loading ? 'Сохранение...' : 'Сохранить'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditHouseModal;