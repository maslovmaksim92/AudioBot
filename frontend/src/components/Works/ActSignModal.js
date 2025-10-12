import React, { useState } from 'react';
import { X, CheckCircle, Calendar } from 'lucide-react';

const ActSignModal = ({ isOpen, onClose, house, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [signedDate, setSignedDate] = useState(new Date().toISOString().split('T')[0]);
  const [signedBy, setSignedBy] = useState('');
  const [notes, setNotes] = useState('');

  if (!isOpen || !house) return null;

  const handleSign = async () => {
    setLoading(true);
    
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      
      // Определяем месяц акта (текущий месяц или из signedDate)
      const actMonth = signedDate.substring(0, 7); // YYYY-MM
      
      const response = await fetch(`${backendUrl}/api/houses/acts/sign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          house_id: house.id || house.bitrix_id,
          house_address: house.address,
          act_month: actMonth,
          signed_date: signedDate,
          signed_by: signedBy || null,
          brigade_id: house.brigade_number || null,
          notes: notes || null
        })
      });

      const data = await response.json();

      if (response.ok) {
        console.log('[ActSignModal] Act signed successfully:', data);
        
        // Уведомление об успехе
        if (window.toast) {
          window.toast.success(`✅ Акт подписан! Уборок в месяце: ${data.cleaning_count}`);
        }
        
        // Вызываем callback
        if (onSuccess) {
          onSuccess(data);
        }
        
        // Закрываем модальное окно
        onClose();
      } else {
        throw new Error(data.detail || 'Ошибка при подписании акта');
      }
      
    } catch (error) {
      console.error('[ActSignModal] Error signing act:', error);
      
      if (window.toast) {
        window.toast.error(`❌ Ошибка: ${error.message}`);
      } else {
        alert(`Ошибка при подписании акта: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" data-testid="act-sign-modal">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <h2 className="text-xl font-semibold text-gray-900">Подписать акт</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            data-testid="close-modal-btn"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {/* Адрес дома */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Адрес дома
            </label>
            <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-900">{house.address}</p>
            </div>
          </div>

          {/* Дата подписания */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Дата подписания акта
            </label>
            <input
              type="date"
              value={signedDate}
              onChange={(e) => setSignedDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="signed-date-input"
            />
            <p className="text-xs text-gray-500 mt-1">
              Месяц акта: {signedDate.substring(0, 7)}
            </p>
          </div>

          {/* Кто подписал */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Кто подписал (опционально)
            </label>
            <input
              type="text"
              value={signedBy}
              onChange={(e) => setSignedBy(e.target.value)}
              placeholder="Например: УК Комфорт, Иванов И.И."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="signed-by-input"
            />
          </div>

          {/* Примечания */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Примечания (опционально)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Дополнительная информация..."
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="notes-input"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            disabled={loading}
            data-testid="cancel-btn"
          >
            Отмена
          </button>
          <button
            onClick={handleSign}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            data-testid="sign-act-btn"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Подписываем...
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                Подписать акт
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ActSignModal;
