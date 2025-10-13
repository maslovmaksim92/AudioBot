import React, { useState, useEffect } from 'react';
import { X, Calendar, Image, ExternalLink, Send } from 'lucide-react';

const PhotoHistoryModal = ({ isOpen, onClose, house }) => {
  const [cleanings, setCleanings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(null);

  useEffect(() => {
    if (isOpen && house) {
      fetchPhotoHistory();
    }
  }, [isOpen, house]);

  const fetchPhotoHistory = async () => {
    setLoading(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/cleaning/house/${house.id}/photo-history`);
      const data = await response.json();
      
      if (data.cleanings) {
        setCleanings(data.cleanings);
      } else {
        setCleanings([]);
      }
    } catch (error) {
      console.error('[PhotoHistoryModal] Error fetching photo history:', error);
      setCleanings([]);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async (cleaningId) => {
    setResending(cleaningId);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/cleaning/resend-photos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          cleaning_id: cleaningId
        })
      });

      const data = await response.json();

      if (data.success) {
        alert(`✅ ${data.message}`);
      } else {
        alert(`❌ Ошибка: ${data.error}`);
      }
    } catch (error) {
      console.error('[PhotoHistoryModal] Error resending photos:', error);
      alert('❌ Ошибка при отправке фото');
    } finally {
      setResending(null);
    }
  };

  if (!isOpen || !house) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" data-testid="photo-history-modal">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Image className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">История фото уборок</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            data-testid="close-modal-btn"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Address */}
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
          <p className="text-sm text-gray-600">Дом:</p>
          <p className="text-base font-medium text-gray-900">{house.address}</p>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : cleanings.length === 0 ? (
            <div className="text-center py-12">
              <Image className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Нет истории фото для этого дома</p>
              <p className="text-sm text-gray-400 mt-2">
                Когда бригада загрузит фото через Telegram бота, они появятся здесь
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {cleanings.map((cleaning) => (
                <div
                  key={cleaning.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-5 h-5 text-blue-600" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {new Date(cleaning.cleaning_date).toLocaleDateString('ru-RU', {
                            day: '2-digit',
                            month: 'long',
                            year: 'numeric'
                          })}
                        </p>
                        <p className="text-xs text-gray-500">
                          {cleaning.brigade_id ? `Бригада: ${cleaning.brigade_id}` : 'Бригада не указана'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded">
                        {cleaning.photo_count} фото
                      </span>
                    </div>
                  </div>

                  {/* AI Caption */}
                  {cleaning.ai_caption && (
                    <div className="mb-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {cleaning.ai_caption}
                      </p>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 mt-3">
                    {cleaning.telegram_post_url ? (
                      <a
                        href={cleaning.telegram_post_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                        Открыть в Telegram
                      </a>
                    ) : (
                      <div className="flex-1 px-4 py-2 bg-gray-100 text-gray-400 text-sm text-center rounded-lg">
                        Ссылка недоступна
                      </div>
                    )}

                    <button
                      onClick={() => handleResend(cleaning.id)}
                      disabled={resending === cleaning.id}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {resending === cleaning.id ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          Отправка...
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          Отправить снова
                        </>
                      )}
                    </button>
                  </div>

                  {/* Status & Time */}
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Статус: {cleaning.status === 'sent_to_group' ? '✅ Отправлено' : '⏳ В обработке'}</span>
                      {cleaning.sent_to_group_at && (
                        <span>
                          Отправлено: {new Date(cleaning.sent_to_group_at).toLocaleString('ru-RU')}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
};

export default PhotoHistoryModal;
