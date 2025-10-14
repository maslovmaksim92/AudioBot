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
  
  const recognitionRef = useRef(null);
  const finalTranscriptRef = useRef(''); // Хранилище финального текста
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    // Инициализация Web Speech API
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'ru-RU';
      
      recognition.onresult = (event) => {
        let interim = '';
        
        // Проходим по результатам, обновляя финальный и промежуточный текст
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcriptPiece = event.results[i][0].transcript;
          
          if (event.results[i].isFinal) {
            // Финальный текст добавляем в ref и state
            finalTranscriptRef.current += transcriptPiece + ' ';
            setTranscript(finalTranscriptRef.current);
            console.log('✅ Final:', transcriptPiece);
          } else {
            // Промежуточный текст только для отображения
            interim += transcriptPiece;
            console.log('⏳ Interim:', transcriptPiece);
          }
        }
        
        // Обновляем промежуточный текст для отображения
        setInterimTranscript(interim);
      };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'no-speech') {
          // Игнорируем, это нормально
        } else {
          alert(`Ошибка распознавания речи: ${event.error}`);
        }
      };
      
      recognition.onend = () => {
        if (isRecording) {
          // Перезапускаем если запись еще активна
          recognition.start();
        }
      };
      
      recognitionRef.current = recognition;
    } else {
      alert('⚠️ Ваш браузер не поддерживает распознавание речи. Используйте Chrome или Edge.');
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isRecording]);

  const startRecording = () => {
    if (recognitionRef.current) {
      try {
        // Очищаем предыдущие результаты
        finalTranscriptRef.current = transcript;
        setInterimTranscript('');
        
        recognitionRef.current.start();
        setIsRecording(true);
        setIsSaved(false);
        console.log('🎤 Recording started');
      } catch (error) {
        console.error('Error starting recognition:', error);
        alert(`Ошибка запуска записи: ${error.message}`);
      }
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
      setInterimTranscript(''); // Очищаем промежуточный текст
      console.log('🛑 Recording stopped');
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
          <h2 className="text-xl font-semibold flex items-center mb-4">
            <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
            Извлечённые задачи ({tasks.length})
          </h2>
          <div className="space-y-3">
            {tasks.map((task, index) => (
              <div
                key={index}
                className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{task.title}</h3>
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
