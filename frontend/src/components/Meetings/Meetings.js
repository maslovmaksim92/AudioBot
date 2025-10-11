import React, { useState, useRef, useEffect } from 'react';
import { 
  Mic, 
  Square, 
  Play, 
  Pause, 
  Download, 
  FileText, 
  Users,
  Clock,
  Calendar,
  Sparkles,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

const Meetings = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [meetings, setMeetings] = useState([]);
  const [currentMeeting, setCurrentMeeting] = useState(null);
  const [transcription, setTranscription] = useState('');
  const [summary, setSummary] = useState('');
  const [tasks, setTasks] = useState([]);
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const meeting = {
          id: Date.now(),
          date: new Date().toISOString(),
          duration: recordingTime,
          audioBlob: blob,
          audioUrl: URL.createObjectURL(blob)
        };
        setMeetings([meeting, ...meetings]);
        setCurrentMeeting(meeting);
        // В продакшене здесь будет отправка на сервер для транскрибации
        simulateTranscription(meeting);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Не удалось получить доступ к микрофону. Проверьте разрешения.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const togglePause = () => {
    if (isPaused) {
      mediaRecorderRef.current.resume();
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      mediaRecorderRef.current.pause();
      if (timerRef.current) clearInterval(timerRef.current);
    }
    setIsPaused(!isPaused);
  };

  const simulateTranscription = (meeting) => {
    // Симуляция транскрибации и AI анализа
    setTimeout(() => {
      const mockTranscript = `[00:00:05] Максим: Доброе утро, коллеги! Начинаем планёрку.\n[00:00:12] Наталья: Добрый день! У нас сегодня 15 домов на уборку.\n[00:00:25] Алексей: По Билибина 6 - старший просит обратить внимание на подъезд №2.\n[00:00:40] Максим: Хорошо, отметили. Бригада 3 - возьмите с собой дополнительные материалы.\n[00:01:00] Валентина: По финансам - все акты за вчера подписаны, кроме Кубяка 5.\n[00:01:15] Максим: Нужно дозвониться старшему. AI помощник, напомни в 14:00.\n[00:01:30] Наталья: Новая заявка от УК "Комфорт" - 3 дома на обслуживание.\n[00:01:45] Максим: Отлично! Подготовим КП. Встречаемся завтра в 8:30. Всем продуктивного дня!`;
      
      setTranscription(mockTranscript);
      
      const mockSummary = {
        mainTopics: [
          'График уборки домов на сегодня',
          'Проблема с подъездом №2 в доме Билибина 6',
          'Статус подписания актов',
          'Новая заявка от УК "Комфорт"'
        ],
        decisions: [
          'Бригада 3 берёт дополнительные материалы для Билибина 6',
          'Дозвониться старшему Кубяка 5 для подписания акта',
          'Подготовить КП для УК "Комфорт" на 3 дома'
        ],
        participants: ['Максим (Директор)', 'Наталья (Нач. отдела)', 'Алексей (Менеджер)', 'Валентина (Ген. директор)'],
        duration: formatTime(meeting.duration)
      };
      
      setSummary(mockSummary);
      
      const mockTasks = [
        {
          id: 1,
          title: 'Уборка Билибина 6 - особое внимание подъезд №2',
          assignee: 'Бригада 3',
          priority: 'high',
          deadline: 'Сегодня',
          status: 'pending'
        },
        {
          id: 2,
          title: 'Связаться со старшим Кубяка 5 для подписания акта',
          assignee: 'Алексей',
          priority: 'medium',
          deadline: 'Сегодня 14:00',
          status: 'pending'
        },
        {
          id: 3,
          title: 'Подготовить КП для УК "Комфорт" на 3 дома',
          assignee: 'Наталья',
          priority: 'medium',
          deadline: 'Завтра',
          status: 'pending'
        }
      ];
      
      setTasks(mockTasks);
    }, 2000);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const downloadAudio = (audioUrl, meetingId) => {
    const a = document.createElement('a');
    a.href = audioUrl;
    a.download = `meeting_${meetingId}.webm`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
                <FileText className="w-10 h-10 text-indigo-600" />
                Планёрки
              </h1>
              <p className="text-gray-600">
                Запись, транскрибация и AI-анализ совещаний
              </p>
            </div>
            
            {/* Recording Controls */}
            <div className="flex items-center gap-4">
              {!isRecording ? (
                <button
                  onClick={startRecording}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl hover:from-red-600 hover:to-red-700 transition-all shadow-lg hover:shadow-xl"
                >
                  <Mic className="w-5 h-5" />
                  Начать запись
                </button>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="px-4 py-2 bg-red-100 text-red-700 rounded-lg flex items-center gap-2 font-mono">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                    {formatTime(recordingTime)}
                  </div>
                  
                  <button
                    onClick={togglePause}
                    className="p-3 bg-yellow-500 text-white rounded-xl hover:bg-yellow-600 transition-all shadow-md"
                  >
                    {isPaused ? <Play className="w-5 h-5" /> : <Pause className="w-5 h-5" />}
                  </button>
                  
                  <button
                    onClick={stopRecording}
                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-gray-700 to-gray-800 text-white rounded-xl hover:from-gray-800 hover:to-gray-900 transition-all shadow-lg"
                  >
                    <Square className="w-5 h-5" />
                    Остановить
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Current Meeting Analysis */}
        {currentMeeting && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Transcription */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <FileText className="w-6 h-6 text-blue-600" />
                  Транскрипция
                </h2>
                {transcription && (
                  <Download 
                    className="w-5 h-5 text-gray-400 hover:text-blue-600 cursor-pointer transition-colors" 
                    onClick={() => downloadAudio(currentMeeting.audioUrl, currentMeeting.id)}
                  />
                )}
              </div>
              
              <div className="bg-gray-50 rounded-xl p-4 max-h-96 overflow-y-auto">
                {transcription ? (
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed">
                    {transcription}
                  </pre>
                ) : (
                  <div className="flex items-center justify-center py-12">
                    <div className="text-center">
                      <Sparkles className="w-12 h-12 text-gray-300 mx-auto mb-3 animate-pulse" />
                      <p className="text-gray-500">Ожидание транскрипции...</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* AI Summary */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <Sparkles className="w-6 h-6 text-purple-600" />
                AI Анализ
              </h2>
              
              {summary ? (
                <div className="space-y-4">
                  {/* Participants */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <Users className="w-4 h-4" />
                      Участники ({summary.participants.length})
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {summary.participants.map((p, i) => (
                        <span key={i} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-sm">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Duration */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Длительность
                    </h3>
                    <p className="text-gray-600">{summary.duration}</p>
                  </div>

                  {/* Main Topics */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">
                      Основные темы
                    </h3>
                    <ul className="space-y-2">
                      {summary.mainTopics.map((topic, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span>{topic}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Decisions */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">
                      Решения
                    </h3>
                    <ul className="space-y-2">
                      {summary.decisions.map((decision, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                          <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                          <span>{decision}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <Sparkles className="w-12 h-12 text-gray-300 mx-auto mb-3 animate-pulse" />
                    <p className="text-gray-500">Ожидание анализа...</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tasks from Meeting */}
        {tasks.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <CheckCircle className="w-6 h-6 text-green-600" />
              Задачи из планёрки ({tasks.length})
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {tasks.map(task => (
                <div 
                  key={task.id} 
                  className={`p-4 rounded-xl border-2 transition-all hover:shadow-md ${
                    task.priority === 'high' 
                      ? 'border-red-200 bg-red-50' 
                      : 'border-blue-200 bg-blue-50'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      task.priority === 'high' 
                        ? 'bg-red-200 text-red-700' 
                        : 'bg-blue-200 text-blue-700'
                    }`}>
                      {task.priority === 'high' ? 'Высокий' : 'Средний'}
                    </span>
                  </div>
                  
                  <h3 className="font-semibold text-gray-900 mb-2 text-sm">
                    {task.title}
                  </h3>
                  
                  <div className="space-y-1 text-xs text-gray-600">
                    <div className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      <span>{task.assignee}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      <span>{task.deadline}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Meeting History */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            История планёрок
          </h2>
          
          {meetings.length === 0 ? (
            <div className="text-center py-12">
              <Mic className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Пока нет записанных планёрок</p>
              <p className="text-sm text-gray-400 mt-2">
                Нажмите "Начать запись" чтобы создать первую запись
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {meetings.map(meeting => (
                <div 
                  key={meeting.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
                  onClick={() => setCurrentMeeting(meeting)}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center">
                      <FileText className="w-6 h-6 text-indigo-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        Планёрка {new Date(meeting.date).toLocaleDateString('ru-RU')}
                      </p>
                      <p className="text-sm text-gray-500">
                        {new Date(meeting.date).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })} • {formatTime(meeting.duration)}
                      </p>
                    </div>
                  </div>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      downloadAudio(meeting.audioUrl, meeting.id);
                    }}
                    className="p-2 hover:bg-white rounded-lg transition-colors"
                  >
                    <Download className="w-5 h-5 text-gray-400 hover:text-indigo-600" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Meetings;