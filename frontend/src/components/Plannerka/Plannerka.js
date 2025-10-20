import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Save, Sparkles, CheckCircle, Calendar, Users, FileText } from 'lucide-react';

const Plannerka = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [title, setTitle] = useState(`Планёрка ${new Date().toLocaleDateString('ru-RU')}`);
  const [summary, setSummary] = useState('');
  const [tasks, setTasks] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [currentMeetingId, setCurrentMeetingId] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected'); // disconnected, connecting, connected
  
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const processorRef = useRef(null);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  const startRecording = async () => {
    try {
      setConnectionStatus('connecting');
      
      // Получаем доступ к микрофону
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 24000,
          echoCancellation: true,
          noiseSuppression: true
        } 
      });
      mediaStreamRef.current = stream;

      // Создаем AudioContext
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 24000
      });
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      
      // Создаем ScriptProcessor для получения аудио данных
      const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      
      source.connect(processor);
      processor.connect(audioContextRef.current.destination);

      // Подключаемся к OpenAI Realtime API напрямую
      const ws = new WebSocket('wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01');
      wsRef.current = ws;

      ws.onopen = async () => {
        console.log('✅ Connected to OpenAI Realtime API');
        setConnectionStatus('connected');
        setIsRecording(true);

        // Отправляем токен авторизации
        const response = await fetch(`${BACKEND_URL}/api/openai/realtime-token`);
        const { token } = await response.json();

        // Настраиваем сессию
        ws.send(JSON.stringify({
          type: 'session.update',
          session: {
            modalities: ['text', 'audio'],
            instructions: 'Ты помощник для транскрипции совещаний на русском языке. Транскрибируй всё что слышишь точно и подробно.',
            voice: 'alloy',
            input_audio_format: 'pcm16',
            output_audio_format: 'pcm16',
            input_audio_transcription: {
              model: 'whisper-1'
            },
            turn_detection: {
              type: 'server_vad',
              threshold: 0.5,
              prefix_padding_ms: 300,
              silence_duration_ms: 500
            }
          }
        }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Обрабатываем транскрипцию
          if (data.type === 'conversation.item.input_audio_transcription.completed') {
            const transcribedText = data.transcript;
            setTranscript(prev => prev + transcribedText + ' ');
            console.log('✅ Transcription:', transcribedText);
          }
          
          // Обрабатываем другие события
          if (data.type === 'error') {
            console.error('❌ Realtime API error:', data.error);
          }
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setConnectionStatus('disconnected');
      };

      ws.onclose = () => {
        console.log('🔌 Disconnected from Realtime API');
        setConnectionStatus('disconnected');
      };

      // Обработка аудио и отправка в Realtime API
      processor.onaudioprocess = (e) => {
        if (ws.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          
          // Конвертируем Float32Array в Int16Array (PCM16)
          const pcm16 = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          }
          
          // Конвертируем в base64
          const base64Audio = btoa(String.fromCharCode.apply(null, new Uint8Array(pcm16.buffer)));
          
          // Отправляем аудио
          ws.send(JSON.stringify({
            type: 'input_audio_buffer.append',
            audio: base64Audio
          }));
        }
      };

    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Ошибка при запуске записи: ' + error.message);
      setConnectionStatus('disconnected');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    console.log('🛑 Stopping recording...');
    
    // Останавливаем WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // Останавливаем аудио процессор
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    
    // Останавливаем AudioContext
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // Останавливаем медиа поток
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    setIsRecording(false);
    setConnectionStatus('disconnected');
  };
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
