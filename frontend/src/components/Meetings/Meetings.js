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
          message: `Планерка "${meetingTitle}" начата`
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
    &lt;div className="p-6"&gt;
      &lt;div className="flex justify-between items-center mb-6"&gt;
        &lt;div&gt;
          &lt;h1 className="text-3xl font-bold text-gray-900"&gt;Планерки&lt;/h1&gt;
          &lt;p className="text-gray-600"&gt;Запись и управление совещаниями&lt;/p&gt;
        &lt;/div&gt;
        &lt;Button variant="secondary" onClick={fetchMeetings} loading={loading}&gt;
          🔄 Обновить
        &lt;/Button&gt;
      &lt;/div&gt;

      &lt;div className="grid grid-cols-1 lg:grid-cols-2 gap-6"&gt;
        {/* Recording Panel */}
        &lt;div&gt;
          &lt;Card title="🎤 Новая планерка" className="mb-6"&gt;
            &lt;div className="space-y-4"&gt;
              &lt;div&gt;
                &lt;label className="block text-sm font-medium text-gray-700 mb-1"&gt;
                  Название планерки
                &lt;/label&gt;
                &lt;input
                  type="text"
                  value={meetingTitle}
                  onChange={(e) => setMeetingTitle(e.target.value)}
                  placeholder="Введите название..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isRecording}
                /&gt;
              &lt;/div&gt;

              &lt;div className="flex space-x-2"&gt;
                {!isRecording ? (
                  &lt;Button
                    onClick={startRecording}
                    variant="success"
                    disabled={!meetingTitle.trim()}
                    className="flex-1"
                  &gt;
                    🎤 Начать запись
                  &lt;/Button&gt;
                ) : (
                  &lt;Button
                    onClick={stopRecording}
                    variant="danger"
                    className="flex-1"
                  &gt;
                    ⏹️ Остановить запись
                  &lt;/Button&gt;
                )}
              &lt;/div&gt;

              {isRecording && (
                &lt;div className="p-3 bg-red-50 border border-red-200 rounded-lg"&gt;
                  &lt;div className="flex items-center mb-2"&gt;
                    &lt;div className="w-3 h-3 bg-red-500 rounded-full animate-pulse mr-2"&gt;&lt;/div&gt;
                    &lt;span className="text-sm font-medium text-red-800"&gt;
                      Идет запись: {meetingTitle}
                    &lt;/span&gt;
                  &lt;/div&gt;
                  &lt;p className="text-xs text-red-600"&gt;
                    ID: {currentMeetingId}
                  &lt;/p&gt;
                &lt;/div&gt;
              )}
            &lt;/div&gt;
          &lt;/Card&gt;

          {/* Real-time Transcription */}
          {isRecording && (
            &lt;Card title="📝 Транскрипция в реальном времени"&gt;
              &lt;div className="space-y-4"&gt;
                &lt;div className="h-32 p-3 bg-gray-50 border rounded-lg overflow-y-auto"&gt;
                  &lt;p className="text-sm text-gray-700 whitespace-pre-wrap"&gt;
                    {transcription}
                  &lt;/p&gt;
                  {realTimeText && (
                    &lt;p className="text-sm text-blue-600 italic"&gt;
                      {realTimeText}
                    &lt;/p&gt;
                  )}
                &lt;/div&gt;
                &lt;div className="text-xs text-gray-500"&gt;
                  Всего символов: {transcription.length}
                &lt;/div&gt;
              &lt;/div&gt;
            &lt;/Card&gt;
          )}
        &lt;/div&gt;

        {/* Meetings History */}
        &lt;div&gt;
          &lt;Card title={`📋 История планерок (${meetings.length})`}&gt;
            {loading ? (
              &lt;div className="flex justify-center py-8"&gt;
                &lt;LoadingSpinner size="md" text="Загрузка планерок..." /&gt;
              &lt;/div&gt;
            ) : meetings.length > 0 ? (
              &lt;div className="space-y-3 max-h-96 overflow-y-auto"&gt;
                {meetings.map((meeting, index) => (
                  &lt;div
                    key={meeting.id || index}
                    className="p-3 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                  &gt;
                    &lt;div className="flex justify-between items-start mb-2"&gt;
                      &lt;h4 className="font-medium text-gray-900"&gt;
                        {meeting.title || 'Без названия'}
                      &lt;/h4&gt;
                      &lt;span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        meeting.status === 'active' 
                          ? 'bg-green-100 text-green-800'
                          : meeting.status === 'completed'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}&gt;
                        {meeting.status === 'active' ? 'Активна' : 
                         meeting.status === 'completed' ? 'Завершена' : 'Неизвестно'}
                      &lt;/span&gt;
                    &lt;/div&gt;
                    
                    &lt;p className="text-xs text-gray-500 mb-2"&gt;
                      Создана: {formatDate(meeting.created_at)}
                    &lt;/p&gt;
                    
                    {meeting.transcription && (
                      &lt;p className="text-sm text-gray-700 truncate"&gt;
                        {meeting.transcription.substring(0, 100)}...
                      &lt;/p&gt;
                    )}
                    
                    {meeting.summary && (
                      &lt;div className="mt-2 p-2 bg-blue-50 rounded text-sm"&gt;
                        &lt;strong&gt;Резюме:&lt;/strong&gt; {meeting.summary}
                      &lt;/div&gt;
                    )}
                  &lt;/div&gt;
                ))}
              &lt;/div&gt;
            ) : (
              &lt;div className="text-center py-8 text-gray-500"&gt;
                &lt;p&gt;📝 Пока нет записанных планерок&lt;/p&gt;
                &lt;p className="text-sm mt-1"&gt;Начните первую запись выше&lt;/p&gt;
              &lt;/div&gt;
            )}
          &lt;/Card&gt;
        &lt;/div&gt;
      &lt;/div&gt;

      {/* Info Card */}
      &lt;Card title="💡 Информация" className="mt-6"&gt;
        &lt;div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600"&gt;
          &lt;div&gt;
            &lt;h4 className="font-medium text-gray-900 mb-2"&gt;Возможности:&lt;/h4&gt;
            &lt;ul className="space-y-1"&gt;
              &lt;li&gt;• Автоматическая транскрипция речи&lt;/li&gt;
              &lt;li&gt;• Сохранение в PostgreSQL&lt;/li&gt;
              &lt;li&gt;• AI-обработка и резюме&lt;/li&gt;
              &lt;li&gt;• История всех планерок&lt;/li&gt;
            &lt;/ul&gt;
          &lt;/div&gt;
          &lt;div&gt;
            &lt;h4 className="font-medium text-gray-900 mb-2"&gt;Советы:&lt;/h4&gt;
            &lt;ul className="space-y-1"&gt;
              &lt;li&gt;• Говорите четко и громко&lt;/li&gt;
              &lt;li&gt;• Используйте Chrome для лучшего качества&lt;/li&gt;
              &lt;li&gt;• Проверьte разрешения микрофона&lt;/li&gt;
              &lt;li&gt;• Минимизируйте фоновый шум&lt;/li&gt;
            &lt;/ul&gt;
          &lt;/div&gt;
        &lt;/div&gt;
      &lt;/Card&gt;
    &lt;/div&gt;
  );
};

export default Meetings;