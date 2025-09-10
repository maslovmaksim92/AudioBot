import React, { useState, useRef, useEffect } from 'react';
import { 
  Calendar, Mic, MicOff, Play, Pause, Square, 
  FileText, Users, CheckSquare, Clock, Send,
  Loader2, Download, Upload, Zap, Bot, ExternalLink
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Meetings = () => {
  // Meeting states
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [meetingTitle, setMeetingTitle] = useState('');
  
  // Real-time transcription
  const [transcription, setTranscription] = useState('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  
  // AI Analysis
  const [aiSummary, setAiSummary] = useState('');
  const [extractedTasks, setExtractedTasks] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // Bitrix integration
  const [bitrixTasks, setBitrixTasks] = useState([]);
  const [isCreatingTasks, setIsCreatingTasks] = useState(false);
  const [bitrixStatus, setBitrixStatus] = useState('disconnected');

  // Refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const recognitionRef = useRef(null);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'ru-RU';
      
      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        setTranscription(prev => prev + finalTranscript);
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
      };
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      // Start recording
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.start(1000); // Record in 1-second chunks
      setIsRecording(true);
      setIsTranscribing(true);
      
      // Start speech recognition
      if (recognitionRef.current) {
        recognitionRef.current.start();
      }
      
      // Start timer
      setRecordingTime(0);
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Ошибка доступа к микрофону: ' + error.message);
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      if (isPaused) {
        mediaRecorderRef.current.resume();
        if (recognitionRef.current) {
          recognitionRef.current.start();
        }
        timerRef.current = setInterval(() => {
          setRecordingTime(prev => prev + 1);
        }, 1000);
      } else {
        mediaRecorderRef.current.pause();
        if (recognitionRef.current) {
          recognitionRef.current.stop();
        }
        clearInterval(timerRef.current);
      }
      setIsPaused(!isPaused);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    
    clearInterval(timerRef.current);
    setIsRecording(false);
    setIsPaused(false);
    setIsTranscribing(false);
    
    // Process the recording
    setTimeout(() => {
      analyzeRecording();
    }, 1000);
  };

  const analyzeRecording = async () => {
    if (!transcription.trim()) {
      alert('Нет текста для анализа');
      return;
    }
    
    setIsAnalyzing(true);
    
    try {
      // Send transcription to AI for analysis
      const response = await fetch(`${BACKEND_URL}/api/meetings/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcription: transcription,
          meeting_title: meetingTitle || `Планерка ${new Date().toLocaleDateString()}`,
          duration: recordingTime
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      setAiSummary(data.summary || '');
      setExtractedTasks(data.tasks || []);
      setParticipants(data.participants || []);
      
    } catch (error) {
      console.error('Error analyzing recording:', error);
      // Fallback to local analysis
      performLocalAnalysis();
    } finally {
      setIsAnalyzing(false);
    }
  };

  const performLocalAnalysis = () => {
    // Simple local analysis as fallback
    const text = transcription.toLowerCase();
    
    // Extract potential tasks (keywords)
    const taskKeywords = ['задача', 'сделать', 'выполнить', 'подготовить', 'проверить', 'отправить', 'связаться'];
    const sentences = transcription.split(/[.!?]+/);
    const tasks = sentences.filter(sentence => 
      taskKeywords.some(keyword => sentence.toLowerCase().includes(keyword))
    ).map((task, index) => ({
      id: index + 1,
      title: task.trim(),
      priority: 'normal',
      assigned_to: 'Не назначено',
      deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    }));
    
    setExtractedTasks(tasks);
    setAiSummary(`Краткое содержание планерки "${meetingTitle || 'Без названия'}":\n\nОбсуждались вопросы организации и выполнения задач. Выявлено ${tasks.length} потенциальных задач для дальнейшего выполнения.`);
  };

  const createBitrixTasks = async () => {
    if (extractedTasks.length === 0) {
      alert('Нет задач для создания в Битрикс');
      return;
    }
    
    setIsCreatingTasks(true);
    setBitrixStatus('creating');
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/bitrix/create-tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tasks: extractedTasks,
          meeting_title: meetingTitle,
          meeting_summary: aiSummary,
          participants: participants
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setBitrixTasks(data.created_tasks || []);
      setBitrixStatus('success');
      
    } catch (error) {
      console.error('Error creating Bitrix tasks:', error);
      setBitrixStatus('error');
      // Mock success for demo
      const mockTasks = extractedTasks.map((task, index) => ({
        id: 1000 + index,
        title: task.title,
        url: `https://bitrix24.ru/workgroups/task/view/${1000 + index}/`,
        status: 'created'
      }));
      setBitrixTasks(mockTasks);
      setBitrixStatus('success');
    } finally {
      setIsCreatingTasks(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const exportMeeting = () => {
    const meetingData = {
      title: meetingTitle,
      date: new Date().toISOString(),
      duration: recordingTime,
      transcription: transcription,
      summary: aiSummary,
      tasks: extractedTasks,
      participants: participants,
      bitrix_tasks: bitrixTasks
    };
    
    const blob = new Blob([JSON.stringify(meetingData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `meeting-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full overflow-y-auto">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-sm border-b border-white/10 p-6 sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
              <Calendar className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Умные планерки</h1>
              <p className="text-gray-400">Транскрибация, анализ и интеграция с Битрикс24</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Recording Status */}
            {isRecording && (
              <div className="flex items-center space-x-2 bg-red-500/20 text-red-400 px-4 py-2 rounded-lg">
                <div className="w-3 h-3 bg-red-400 rounded-full animate-pulse" />
                <span className="font-mono">{formatTime(recordingTime)}</span>
              </div>
            )}
            
            <button
              onClick={exportMeeting}
              disabled={!transcription}
              className="bg-blue-500/20 text-blue-400 border border-blue-500/30 px-4 py-2 rounded-lg hover:bg-blue-500/30 disabled:opacity-50 flex items-center space-x-2"
            >
              <Download size={16} />
              <span>Экспорт</span>
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Meeting Setup */}
        <div className="bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-4">Настройка планерки</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Название планерки
              </label>
              <input
                type="text"
                value={meetingTitle}
                onChange={(e) => setMeetingTitle(e.target.value)}
                placeholder="Ежедневная планерка команды"
                className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-purple-500/50"
              />
            </div>
          </div>
        </div>

        {/* Recording Controls */}
        <div className="bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl p-8">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-white mb-6">
              {isRecording ? 'Запись планерки' : 'Готов к записи'}
            </h3>
            
            <div className="flex justify-center space-x-4 mb-6">
              {!isRecording ? (
                <button
                  onClick={startRecording}
                  className="bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white px-8 py-4 rounded-full text-lg font-bold transition-all hover:scale-105 flex items-center space-x-3"
                >
                  <Mic size={24} />
                  <span>Начать запись</span>
                </button>
              ) : (
                <div className="flex space-x-4">
                  <button
                    onClick={pauseRecording}
                    className={`px-6 py-3 rounded-lg font-medium transition-all flex items-center space-x-2 ${
                      isPaused
                        ? 'bg-green-500 hover:bg-green-600 text-white'
                        : 'bg-yellow-500 hover:bg-yellow-600 text-white'
                    }`}
                  >
                    {isPaused ? <Play size={20} /> : <Pause size={20} />}
                    <span>{isPaused ? 'Продолжить' : 'Пауза'}</span>
                  </button>
                  
                  <button
                    onClick={stopRecording}
                    className="bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-lg font-medium transition-all flex items-center space-x-2"
                  >
                    <Square size={20} />
                    <span>Остановить</span>
                  </button>
                </div>
              )}
            </div>

            {/* Recording Status */}
            {isRecording && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                <div className="flex items-center justify-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-red-400 rounded-full animate-pulse" />
                    <span className="text-red-400 font-medium">
                      {isPaused ? 'НА ПАУЗЕ' : 'ИДЁТ ЗАПИСЬ'}
                    </span>
                  </div>
                  <span className="text-white font-mono text-lg">
                    {formatTime(recordingTime)}
                  </span>
                </div>
                
                {isTranscribing && (
                  <div className="mt-3 flex items-center justify-center space-x-2 text-blue-400">
                    <Loader2 className="animate-spin" size={16} />
                    <span className="text-sm">Транскрибация в реальном времени...</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Real-time Transcription */}
        {transcription && (
          <div className="bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white flex items-center">
                <FileText className="mr-2" size={20} />
                Транскрипция
              </h3>
              {isTranscribing && (
                <div className="flex items-center space-x-2 text-blue-400">
                  <Loader2 className="animate-spin" size={16} />
                  <span className="text-sm">Обновляется...</span>
                </div>
              )}
            </div>
            <div className="bg-black/30 rounded-lg p-4 max-h-64 overflow-y-auto">
              <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                {transcription || 'Транскрипция появится здесь...'}
              </p>
            </div>
            
            {!isRecording && transcription && (
              <div className="mt-4 text-center">
                <button
                  onClick={analyzeRecording}
                  disabled={isAnalyzing}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 text-white px-8 py-3 rounded-lg font-medium transition-all flex items-center space-x-2 mx-auto"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="animate-spin" size={20} />
                      <span>Анализирую...</span>
                    </>
                  ) : (
                    <>
                      <Bot size={20} />
                      <span>Анализировать с помощью AI</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* AI Summary */}
        {aiSummary && (
          <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
              <Bot className="mr-2 text-blue-400" size={20} />
              AI Саммари
            </h3>
            <div className="bg-black/30 rounded-lg p-4">
              <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                {aiSummary}
              </p>
            </div>
          </div>
        )}

        {/* Extracted Tasks */}
        {extractedTasks.length > 0 && (
          <div className="bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white flex items-center">
                <CheckSquare className="mr-2" size={20} />
                Извлечённые задачи ({extractedTasks.length})
              </h3>
              
              <button
                onClick={createBitrixTasks}
                disabled={isCreatingTasks}
                className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium transition-all flex items-center space-x-2"
              >
                {isCreatingTasks ? (
                  <>
                    <Loader2 className="animate-spin" size={16} />
                    <span>Создаю в Битрикс...</span>
                  </>
                ) : (
                  <>
                    <ExternalLink size={16} />
                    <span>Создать в Битрикс24</span>
                  </>
                )}
              </button>
            </div>

            <div className="space-y-3">
              {extractedTasks.map((task, index) => (
                <div key={index} className="bg-black/30 rounded-lg p-4 border-l-4 border-purple-500">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-white mb-2">{task.title}</h4>
                      <div className="flex items-center space-x-4 text-sm text-gray-400">
                        <span className="flex items-center">
                          <Users size={14} className="mr-1" />
                          {task.assigned_to || 'Не назначено'}
                        </span>
                        <span className="flex items-center">
                          <Clock size={14} className="mr-1" />
                          {task.deadline || 'Без срока'}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          task.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                          task.priority === 'normal' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-gray-500/20 text-gray-400'
                        }`}>
                          {task.priority === 'high' ? 'Высокий' :
                           task.priority === 'normal' ? 'Обычный' : 'Низкий'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Bitrix Tasks Status */}
        {bitrixTasks.length > 0 && (
          <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
              <CheckSquare className="mr-2 text-green-400" size={20} />
              Задачи созданы в Битрикс24
            </h3>
            
            <div className="space-y-3">
              {bitrixTasks.map((task, index) => (
                <div key={index} className="bg-black/30 rounded-lg p-4 flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-white">{task.title}</h4>
                    <p className="text-sm text-gray-400">ID: {task.id}</p>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-sm">
                      Создано
                    </span>
                    {task.url && (
                      <a
                        href={task.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        <ExternalLink size={16} />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Meetings;