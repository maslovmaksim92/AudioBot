import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Badge } from '../ui/badge';
import { Mic, Square, Play, Pause } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MeetingRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [meetings, setMeetings] = useState([]);
  const [currentMeeting, setCurrentMeeting] = useState(null);
  const [meetingTitle, setMeetingTitle] = useState('');
  const [participants, setParticipants] = useState('');
  const [transcript, setTranscript] = useState('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    fetchMeetings();
  }, []);

  const fetchMeetings = async () => {
    try {
      const response = await axios.get(`${API}/meetings`);
      setMeetings(response.data);
    } catch (error) {
      console.error('Error fetching meetings:', error);
    }
  };

  const startRecording = async () => {
    try {
      if (!meetingTitle.trim()) {
        alert('Пожалуйста, введите название планерки');
        return;
      }

      // Создать новую планерку
      const response = await axios.post(`${API}/meetings/create`, {
        title: meetingTitle,
        participants: participants.split(',').map(p => p.trim()).filter(Boolean)
      });
      
      setCurrentMeeting(response.data);
      
      // Запросить доступ к микрофону
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        // Здесь можно обработать аудио файл
        audioChunksRef.current = [];
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
      setIsPaused(false);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Ошибка при запуске записи');
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
    }
  };

  const stopRecording = async () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    
    setIsRecording(false);
    setIsPaused(false);
    
    if (currentMeeting) {
      try {
        await axios.post(`${API}/meetings/${currentMeeting.id}/complete`);
        fetchMeetings();
      } catch (error) {
        console.error('Error completing meeting:', error);
      }
    }
  };

  const transcribeMeeting = async (meetingId) => {
    setIsTranscribing(true);
    try {
      // Симуляция транскрипции (в реальности здесь была бы обработка аудио)
      const mockTranscript = transcript || "Это пример транскрипции планерки. В реальном приложении здесь будет распознанный текст из аудио записи.";
      
      const response = await axios.post(`${API}/meetings/${meetingId}/transcribe`, {
        transcript: mockTranscript
      });
      
      alert('Планерка успешно транскрибирована!');
      fetchMeetings();
      
    } catch (error) {
      console.error('Error transcribing meeting:', error);
      alert('Ошибка при транскрибации');
    } finally {
      setIsTranscribing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">🎤 Диктофон Планерок</h2>
        <p className="text-muted-foreground">
          Записывайте планерки и получайте автоматические транскрипции с ИИ анализом
        </p>
      </div>

      {/* Форма создания планерки */}
      <Card>
        <CardHeader>
          <CardTitle>Новая Планерка</CardTitle>
          <CardDescription>Создайте новую запись планерки</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Название планерки</label>
            <Input
              value={meetingTitle}
              onChange={(e) => setMeetingTitle(e.target.value)}
              placeholder="Еженедельная планерка команды"
              disabled={isRecording}
            />
          </div>
          <div>
            <label className="text-sm font-medium">Участники (через запятую)</label>
            <Input
              value={participants}
              onChange={(e) => setParticipants(e.target.value)}
              placeholder="Иван Петров, Мария Сидорова"
              disabled={isRecording}
            />
          </div>
          
          {/* Ручной ввод транскрипта для тестирования */}
          <div>
            <label className="text-sm font-medium">Тестовый транскрипт (для демо)</label>
            <Textarea
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Введите текст для тестирования ИИ анализа..."
              rows={3}
            />
          </div>

          {/* Кнопки управления записью */}
          <div className="flex gap-2">
            {!isRecording ? (
              <Button onClick={startRecording} className="bg-red-600 hover:bg-red-700">
                <Mic className="w-4 h-4 mr-2" />
                Начать Запись
              </Button>
            ) : (
              <div className="flex gap-2">
                {!isPaused ? (
                  <Button onClick={pauseRecording} variant="outline">
                    <Pause className="w-4 h-4 mr-2" />
                    Пауза
                  </Button>
                ) : (
                  <Button onClick={resumeRecording} className="bg-green-600 hover:bg-green-700">
                    <Play className="w-4 h-4 mr-2" />
                    Продолжить
                  </Button>
                )}
                <Button onClick={stopRecording} variant="destructive">
                  <Square className="w-4 h-4 mr-2" />
                  Остановить
                </Button>
              </div>
            )}
          </div>

          {isRecording && (
            <div className="flex items-center space-x-2 text-red-600">
              <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">
                {isPaused ? 'Запись на паузе' : 'Идет запись...'}
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* История планерок */}
      <Card>
        <CardHeader>
          <CardTitle>История Планерок</CardTitle>
          <CardDescription>Все ваши записанные планерки</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {meetings.map((meeting) => (
              <div key={meeting.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{meeting.title}</h3>
                  <Badge variant={meeting.status === 'completed' ? 'default' : 'secondary'}>
                    {meeting.status === 'completed' ? 'Завершена' : 'В процессе'}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-2">
                  {new Date(meeting.date).toLocaleString('ru-RU')}
                </p>
                {meeting.participants.length > 0 && (
                  <p className="text-sm mb-2">
                    <strong>Участники:</strong> {meeting.participants.join(', ')}
                  </p>
                )}
                
                {meeting.transcript && (
                  <div className="mt-4 p-3 bg-gray-50 rounded">
                    <p className="text-sm font-medium mb-1">Транскрипт:</p>
                    <p className="text-sm text-gray-700 mb-2">{meeting.transcript}</p>
                    
                    {meeting.summary && (
                      <div className="mt-2 p-2 bg-blue-50 rounded">
                        <p className="text-sm font-medium text-blue-800 mb-1">ИИ Саммари:</p>
                        <p className="text-sm text-blue-700">{meeting.summary}</p>
                      </div>
                    )}
                  </div>
                )}
                
                {meeting.status === 'completed' && !meeting.transcript && (
                  <Button
                    onClick={() => transcribeMeeting(meeting.id)}
                    disabled={isTranscribing}
                    size="sm"
                    className="mt-2"
                  >
                    {isTranscribing ? 'Транскрибация...' : 'Транскрибировать'}
                  </Button>
                )}
              </div>
            ))}
            
            {meetings.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                У вас пока нет записанных планерок
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MeetingRecorder;