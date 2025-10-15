import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Save, Sparkles, CheckCircle, Calendar, Users, FileText } from 'lucide-react';

const Plannerka = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState(''); // Промежуточный текст
  const [title, setTitle] = useState(`Планёрка ${new Date().toLocaleDateString('ru-RU')}`);
  const [summary, setSummary] = useState('');
  const [tasks, setTasks] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [currentMeetingId, setCurrentMeetingId] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const wsRef = useRef(null);
  const isRecordingRef = useRef(false);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

  useEffect(() => {
    // Очистка при размонтировании
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const initWebSocket = () => {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(`${WS_URL}/api/ws/transcribe`);
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        resolve(ws);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'transcription') {
          // Добавляем транскрипцию к тексту
          setTranscript(prev => prev + data.text + ' ');
          setInterimTranscript(''); // Очищаем промежуточный текст
          console.log('✅ Received transcription:', data.text);
        } else if (data.type === 'error') {
          console.error('❌ Transcription error:', data.message);
          alert(`Ошибка транскрипции: ${data.message}`);
        }
      };
      
      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        reject(error);
      };
      
      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
      };
      
      wsRef.current = ws;
    });
  };

  const startRecording = async () => {
    try {
      // Инициализируем WebSocket
      await initWebSocket();
      
      // Получаем доступ к микрофону
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Создаем MediaRecorder с форматом webm
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        console.log('🎤 Recording stopped, processing audio...');
        
        // Создаем blob из всех чанков
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Конвертируем в base64
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          const base64Audio = reader.result.split(',')[1];
          
          // Отправляем на сервер через WebSocket
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'audio',
              audio: base64Audio
            }));
            setInterimTranscript('🎙️ Обрабатываю запись...');
          }
        };
        
        // Очищаем chunks
        audioChunksRef.current = [];
        
        // Останавливаем все треки
        stream.getTracks().forEach(track => track.stop());
      };
      
      // Записываем чанками по 5 секунд для более быстрой обратной связи
      mediaRecorder.start();
      
      // Автоматически отправляем каждые 5 секунд
      const intervalId = setInterval(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording' && isRecordingRef.current) {
          mediaRecorder.stop();
          // Перезапускаем запись
          setTimeout(() => {
            if (isRecordingRef.current) {
              audioChunksRef.current = [];
              mediaRecorder.start();
            }
          }, 100);
        }
      }, 5000);
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorderRef.current.intervalId = intervalId;
      isRecordingRef.current = true;
      setIsRecording(true);
      setIsSaved(false);
      setInterimTranscript('🎤 Слушаю...');
      
      console.log('🎤 Recording started');
    } catch (error) {
      console.error('❌ Error starting recording:', error);
      alert(`Ошибка запуска записи: ${error.message}`);
    }
  };

  const stopRecording = () => {
    try {
      isRecordingRef.current = false;
      setIsRecording(false);
      
      if (mediaRecorderRef.current) {
        // Останавливаем интервал
        if (mediaRecorderRef.current.intervalId) {
          clearInterval(mediaRecorderRef.current.intervalId);
        }
        
        // Останавливаем запись
        if (mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop();
        }
      }
      
      // Закрываем WebSocket
      if (wsRef.current) {
        wsRef.current.close();
      }
      
      console.log('🛑 Recording stopped');
    } catch (error) {
      console.error('❌ Error stopping recording:', error);
    }
  };

  const handleSaveAndAnalyze = async () => {
    if (!transcript || transcript.length < 50) {
      alert('⚠️ Текст слишком короткий. Продолжите запись.');
      return;
    }

    try {
      setIsAnalyzing(true);

      // Сохраняем планёрку
      const saveResponse = await fetch(`${BACKEND_URL}/api/plannerka/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title,
          transcription: transcript,
          participants: []
        })
      });

      if (!saveResponse.ok) {
        throw new Error('Ошибка сохранения планёрки');
      }

      const saveData = await saveResponse.json();
      setCurrentMeetingId(saveData.id);
      console.log('✅ Meeting saved:', saveData.id);

      // Анализируем через GPT-5
      const analyzeResponse = await fetch(`${BACKEND_URL}/api/plannerka/analyze/${saveData.id}`, {
        method: 'POST'
      });

      if (!analyzeResponse.ok) {
        throw new Error('Ошибка анализа планёрки');
      }

      const analyzeData = await analyzeResponse.json();
      console.log('✅ Analysis complete:', analyzeData);

      setSummary(analyzeData.summary);
      setTasks(analyzeData.tasks || []);
      setIsSaved(true);

      alert(`✅ Планёрка сохранена и проанализирована!\nНайдено задач: ${analyzeData.tasks_count}`);

    } catch (error) {
      console.error('Error:', error);
      alert(`❌ Ошибка: ${error.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClear = () => {
    if (confirm('Очистить всё и начать заново?')) {
      setTranscript('');
      setSummary('');
      setTasks([]);
      setIsSaved(false);
      setCurrentMeetingId(null);
    }
  };

  const handleCreateTasksInDB = async () => {
    if (!tasks || tasks.length === 0) {
      alert('⚠️ Нет задач для создания');
      return;
    }

    try {
      setIsAnalyzing(true);
      const createdTasks = [];

      for (const task of tasks) {
        const response = await fetch(`${BACKEND_URL}/api/tasks/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: task.title,
            description: task.description || '',
            status: 'todo',
            priority: task.priority || 'medium',
            assigned_to_id: task.assignee || null,
            due_date: task.deadline || null,
            ai_proposed: true,
            ai_reasoning: `Создано из планёрки: ${title}`,
            meeting_id: currentMeetingId
          })
        });

        if (response.ok) {
          const created = await response.json();
          createdTasks.push(created);
        }
      }

      alert(`✅ Создано задач в БД: ${createdTasks.length}`);
      console.log('Created tasks:', createdTasks);

    } catch (error) {
      console.error('Error creating tasks:', error);
      alert(`❌ Ошибка создания задач: ${error.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCreateTasksInBitrix = async () => {
    if (!tasks || tasks.length === 0) {
      alert('⚠️ Нет задач для создания');
      return;
    }

    try {
      setIsAnalyzing(true);

      const response = await fetch(`${BACKEND_URL}/api/tasks/bitrix/bulk-create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tasks: tasks.map(task => ({
            title: task.title,
            description: task.description || `Создано из планёрки: ${title}`,
            responsible_id: task.assignee || null,
            deadline: task.deadline || null,
            priority: task.priority === 'high' ? '2' : '1'
          }))
        })
      });

      if (!response.ok) {
        throw new Error('Ошибка создания задач в Bitrix24');
      }

      const data = await response.json();
      alert(`✅ Создано задач в Bitrix24: ${data.created_count || tasks.length}`);

    } catch (error) {
      console.error('Error creating tasks in Bitrix24:', error);
      alert(`❌ Ошибка создания задач в Bitrix24: ${error.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center">
          <Calendar className="w-8 h-8 mr-3 text-purple-600" />
          Планёрка с диктофоном
        </h1>
        <p className="text-gray-600 mt-2">Записывайте речь, получайте транскрипцию и AI-анализ</p>
      </div>

      {/* Заголовок планёрки */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Название планёрки
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          placeholder="Введите название..."
        />
      </div>

      {/* Блок записи */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold flex items-center">
            <Mic className="w-5 h-5 mr-2 text-purple-600" />
            Запись и транскрипция
          </h2>
          
          <div className="flex gap-2">
            {!isRecording ? (
              <button
                onClick={startRecording}
                className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
              >
                <Mic className="w-5 h-5" />
                Начать запись
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="flex items-center gap-2 px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors animate-pulse"
              >
                <MicOff className="w-5 h-5" />
                Остановить
              </button>
            )}
          </div>
        </div>

        {/* Индикатор записи */}
        {isRecording && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
            <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse"></div>
            <span className="text-red-700 font-medium">🎤 Идет запись... Говорите в микрофон</span>
          </div>
        )}

        {/* Транскрипция */}
        <div className="relative">
          <textarea
            value={transcript + interimTranscript}
            onChange={(e) => {
              // При ручном редактировании сбрасываем промежуточный текст
              setTranscript(e.target.value);
              setInterimTranscript('');
              finalTranscriptRef.current = e.target.value;
            }}
            className="w-full h-64 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-sm"
            placeholder="Здесь будет отображаться транскрипция речи в реальном времени..."
          />
          <div className="absolute bottom-3 right-3 flex gap-3 text-xs text-gray-500">
            {interimTranscript && (
              <span className="text-blue-600 animate-pulse">
                🎤 Распознаю...
              </span>
            )}
            <span>
              {(transcript + interimTranscript).length} символов
            </span>
          </div>
        </div>

        {/* Кнопки действий */}
        <div className="mt-4 flex gap-3">
          <button
            onClick={handleSaveAndAnalyze}
            disabled={isAnalyzing || !transcript || transcript.length < 50}
            className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAnalyzing ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Анализирую...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Сохранить и проанализировать
              </>
            )}
          </button>

          <button
            onClick={handleClear}
            disabled={isAnalyzing}
            className="px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
          >
            Очистить
          </button>
        </div>
      </div>

      {/* Саммари */}
      {summary && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold flex items-center mb-4">
            <FileText className="w-5 h-5 mr-2 text-blue-600" />
            Краткое саммари
          </h2>
          <div className="prose max-w-none">
            <p className="text-gray-700 whitespace-pre-wrap">{summary}</p>
          </div>
        </div>
      )}

      {/* Задачи */}
      {tasks.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center">
              <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
              Извлечённые задачи ({tasks.length})
            </h2>
            <div className="flex gap-2">
              <button
                onClick={handleCreateTasksInDB}
                disabled={isAnalyzing}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                💾 Сохранить в БД
              </button>
              <button
                onClick={handleCreateTasksInBitrix}
                disabled={isAnalyzing}
                className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                📋 Создать в Bitrix24
              </button>
            </div>
          </div>
          <div className="space-y-3">
            {tasks.map((task, index) => (
              <div
                key={index}
                className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{task.title}</h3>
                    {task.description && (
                      <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                    )}
                    <div className="mt-2 flex flex-wrap gap-3 text-sm">
                      {task.assignee && (
                        <span className="flex items-center gap-1 text-gray-600">
                          <Users className="w-4 h-4" />
                          {task.assignee}
                        </span>
                      )}
                      {task.deadline && (
                        <span className="flex items-center gap-1 text-gray-600">
                          <Calendar className="w-4 h-4" />
                          {task.deadline}
                        </span>
                      )}
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          task.priority === 'high'
                            ? 'bg-red-100 text-red-700'
                            : task.priority === 'medium'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-green-100 text-green-700'
                        }`}
                      >
                        {task.priority === 'high' ? 'Высокий' : task.priority === 'medium' ? 'Средний' : 'Низкий'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Статус сохранения */}
      {isSaved && (
        <div className="fixed bottom-6 right-6 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-bounce">
          <CheckCircle className="w-5 h-5" />
          Планёрка сохранена!
        </div>
      )}
    </div>
  );
};

export default Plannerka;
