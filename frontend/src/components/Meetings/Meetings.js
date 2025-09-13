import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { apiService } from '../../services/apiService';
import { Card, Button, LoadingSpinner } from '../UI';

const Meetings = () => {
  const { actions } = useApp();
  const [isRecording, setIsRecording] = useState(false);
  const [meetings, setMeetings] = useState([]);
  const [currentMeetingId, setCurrentMeetingId] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [realTimeText, setRealTimeText] = useState('');
  const [meetingTitle, setMeetingTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    console.log('🎤 Meetings component mounted');
    fetchMeetings();
    initSpeechRecognition();
  }, []);

  const initSpeechRecognition = () => {
    if ('webkitSpeechRecognition' in window) {
      const recognition = new window.webkitSpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'ru-RU';
      
      recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
            console.log('📝 Final transcript:', transcript);
          } else {
            interimTranscript = transcript;
          }
        }
        
        if (finalTranscript) {
          setTranscription(prev => prev + finalTranscript);
        }
        setRealTimeText(interimTranscript);
      };
      
      recognition.onstart = () => {
        console.log('🎤 Speech recognition started');
      };
      
      recognition.onend = () => {
        console.log('⏹️ Speech recognition ended');
        if (isRecording) {
          // Автоматически перезапускаем если еще записываем
          setTimeout(() => {
            if (isRecording && recognitionRef.current) {
              recognitionRef.current.start();
            }
          }, 100);
        }
      };
      
      recognition.onerror = (event) => {
        console.error('❌ Speech recognition error:', event.error);
        setRealTimeText(`Ошибка распознавания: ${event.error}`);
        actions.addNotification({
          type: 'error',
          message: `Ошибка распознавания речи: ${event.error}`
        });
      };
      
      recognitionRef.current = recognition;
      console.log('✅ Speech recognition initialized');
    } else {
      console.error('❌ Speech recognition not supported');
      setRealTimeText('Распознавание речи не поддерживается в этом браузере');
    }
  };

  const fetchMeetings = async () => {
    setLoading(true);
    try {
      console.log('📋 Fetching meetings...');
      const response = await apiService.getMeetings();
      if (response.status === 'success') {
        setMeetings(response.meetings);
        console.log('✅ Meetings loaded:', response.meetings.length);
      }
    } catch (error) {
      console.error('❌ Error fetching meetings:', error);
      actions.addNotification({
        type: 'error',
        message: 'Ошибка загрузки планерок'
      });
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    if (!meetingTitle.trim()) {
      actions.addNotification({
        type: 'warning',
        message: 'Введите название планерки'
      });
      return;
    }

    // Проверяем разрешения микрофона
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (error) {
      console.error('❌ Microphone permission denied:', error);
      actions.addNotification({
        type: 'error',
        message: 'Разрешите доступ к микрофону для записи планерки. Проверьте настройки браузера.'
      });
      return;
    }

    try {
      console.log('🎤 Starting meeting recording...');
      const response = await apiService.startMeeting(meetingTitle);
      
      if (response.status === 'success') {
        setCurrentMeetingId(response.meeting_id);
        setIsRecording(true);
        setTranscription('');
        setRealTimeText('');
        
        // Запускаем распознавание речи
        if (recognitionRef.current) {
          recognitionRef.current.start();
        }
        
        actions.addNotification({
          type: 'success',
          message: `Планерка "${meetingTitle}" начата. Говорите четко!`
        });
        
        console.log('✅ Meeting started:', response.meeting_id);
      }
    } catch (error) {
      console.error('❌ Error starting meeting:', error);
      actions.addNotification({
        type: 'error',
        message: 'Ошибка начала записи планерки'
      });
    }
  };

  const stopRecording = async () => {
    if (!currentMeetingId) return;

    try {
      console.log('⏹️ Stopping meeting recording...');
      
      // Останавливаем распознавание речи
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      
      const response = await apiService.stopMeeting(currentMeetingId);
      
      if (response.status === 'success') {
        setIsRecording(false);
        setCurrentMeetingId(null);
        setMeetingTitle('');
        setRealTimeText('');
        
        // Обновляем список планерок
        await fetchMeetings();
        
        actions.addNotification({
          type: 'success',
          message: 'Планерка завершена и сохранена'
        });
        
        console.log('✅ Meeting stopped and saved');
      }
    } catch (error) {
      console.error('❌ Error stopping meeting:', error);
      actions.addNotification({
        type: 'error',
        message: 'Ошибка остановки записи планерки'
      });
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Дата не указана';
    try {
      return new Date(dateString).toLocaleString('ru-RU');
    } catch {
      return 'Неверная дата';
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Планерки</h1>
          <p className="text-gray-600">Запись и управление совещаниями</p>
        </div>
        <Button variant="secondary" onClick={fetchMeetings} loading={loading}>
          🔄 Обновить
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recording Panel */}
        <div>
          <Card title="🎤 Новая планерка" className="mb-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Название планерки
                </label>
                <input
                  type="text"
                  value={meetingTitle}
                  onChange={(e) => setMeetingTitle(e.target.value)}
                  placeholder="Введите название..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isRecording}
                />
              </div>

              <div className="flex space-x-2">
                {!isRecording ? (
                  <div className="flex-1">
                    <Button
                      onClick={startRecording}
                      variant="success"
                      disabled={!meetingTitle.trim()}
                      className="w-full"
                    >
                      🎤 Начать запись
                    </Button>
                    {!meetingTitle.trim() && (
                      <p className="text-xs text-orange-600 mt-1 text-center">
                        💡 Введите название планерки, чтобы активировать кнопку
                      </p>
                    )}
                  </div>
                ) : (
                  <Button
                    onClick={stopRecording}
                    variant="danger"
                    className="flex-1"
                  >
                    ⏹️ Остановить запись
                  </Button>
                )}
              </div>

              {isRecording && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center mb-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse mr-2"></div>
                    <span className="text-sm font-medium text-red-800">
                      Идет запись: {meetingTitle}
                    </span>
                  </div>
                  <p className="text-xs text-red-600">
                    ID: {currentMeetingId}
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Real-time Transcription */}
          {isRecording && (
            <Card title="📝 Транскрипция в реальном времени">
              <div className="space-y-4">
                <div className="h-32 p-3 bg-gray-50 border rounded-lg overflow-y-auto">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {transcription}
                  </p>
                  {realTimeText && (
                    <p className="text-sm text-blue-600 italic">
                      {realTimeText}
                    </p>
                  )}
                </div>
                <div className="text-xs text-gray-500">
                  Всего символов: {transcription.length}
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Meetings History */}
        <div>
          <Card title={`📋 История планерок (${meetings.length})`}>
            {loading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="md" text="Загрузка планерок..." />
              </div>
            ) : meetings.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {meetings.map((meeting, index) => (
                  <div
                    key={meeting.id || index}
                    className="p-3 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-gray-900">
                        {meeting.title || 'Без названия'}
                      </h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        meeting.status === 'active' 
                          ? 'bg-green-100 text-green-800'
                          : meeting.status === 'completed'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {meeting.status === 'active' ? 'Активна' : 
                         meeting.status === 'completed' ? 'Завершена' : 'Неизвестно'}
                      </span>
                    </div>
                    
                    <p className="text-xs text-gray-500 mb-2">
                      Создана: {formatDate(meeting.created_at)}
                    </p>
                    
                    {meeting.transcription && (
                      <p className="text-sm text-gray-700 truncate">
                        {meeting.transcription.substring(0, 100)}...
                      </p>
                    )}
                    
                    {meeting.summary && (
                      <div className="mt-2 p-2 bg-blue-50 rounded text-sm">
                        <strong>Резюме:</strong> {meeting.summary}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>📝 Пока нет записанных планерок</p>
                <p className="text-sm mt-1">Начните первую запись выше</p>
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Info Card */}
      <Card title="💡 Информация" className="mt-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Возможности:</h4>
            <ul className="space-y-1">
              <li>• Автоматическая транскрипция речи</li>
              <li>• Сохранение в PostgreSQL</li>
              <li>• AI-обработка и резюме</li>
              <li>• История всех планерок</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Советы:</h4>
            <ul className="space-y-1">
              <li>• Говорите четко и громко</li>
              <li>• Используйте Chrome для лучшего качества</li>
              <li>• Проверьte разрешения микрофона</li>
              <li>• Минимизируйте фоновый шум</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Meetings;