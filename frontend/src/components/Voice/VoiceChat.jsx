import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { ScrollArea } from '../ui/scroll-area';
import { Badge } from '../ui/badge';
import { Mic, Send, MessageCircle, Bot } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VoiceChat = () => {
  const [currentSession, setCurrentSession] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API}/voice/sessions`);
      setSessions(response.data);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const startNewSession = async () => {
    try {
      const response = await axios.post(`${API}/voice/start-session`);
      setCurrentSession(response.data);
      setSelectedSessionId(response.data.id);
      setMessages([]);
      fetchSessions();
    } catch (error) {
      console.error('Error starting session:', error);
      alert('Ошибка при создании сессии');
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const response = await axios.get(`${API}/voice/${sessionId}/history`);
      setSelectedSessionId(sessionId);
      setCurrentSession({ id: sessionId });
      
      // Преобразуем историю в формат сообщений
      const sessionMessages = response.data.messages.map(msg => ([
        {
          type: 'user',
          content: msg.user_message,
          timestamp: msg.timestamp
        },
        {
          type: 'ai',
          content: msg.ai_response,
          timestamp: msg.timestamp
        }
      ])).flat();
      
      setMessages(sessionMessages);
    } catch (error) {
      console.error('Error loading session:', error);
    }
  };

  const sendTextMessage = async () => {
    if (!textInput.trim() || !currentSession) return;

    const userMessage = textInput.trim();
    setTextInput('');
    setIsProcessing(true);

    // Добавляем сообщение пользователя
    const newUserMessage = {
      type: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await axios.post(`${API}/voice/${currentSession.id}/chat`, {
        message: userMessage
      });

      // Добавляем ответ ИИ
      const aiMessage = {
        type: 'ai',
        content: response.data.ai_response,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        type: 'ai',
        content: 'Извините, произошла ошибка при обработке сообщения.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const startVoiceRecording = async () => {
    try {
      if (!currentSession) {
        await startNewSession();
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        audioChunksRef.current = [];
        
        // В реальном приложении здесь была бы отправка аудио на сервер для распознавания
        // Пока используем заглушку
        const recognizedText = "Привет, как дела?"; // Заглушка для распознанного текста
        
        if (recognizedText) {
          setTextInput(recognizedText);
        }
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
      
    } catch (error) {
      console.error('Error starting voice recording:', error);
      alert('Ошибка при доступе к микрофону');
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    setIsRecording(false);
  };

  const endSession = async () => {
    if (!currentSession) return;
    
    try {
      await axios.post(`${API}/voice/${currentSession.id}/end`);
      setCurrentSession(null);
      setSelectedSessionId(null);
      setMessages([]);
      fetchSessions();
    } catch (error) {
      console.error('Error ending session:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">💬 Живой Разговор с ИИ</h2>
        <p className="text-muted-foreground">
          Общайтесь с ИИ голосом или текстом в режиме реального времени
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Боковая панель с сессиями */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Сессии</CardTitle>
            <Button onClick={startNewSession} className="w-full">
              <MessageCircle className="w-4 h-4 mr-2" />
              Новый Чат
            </Button>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-60">
              <div className="space-y-2">
                {sessions.map((session) => (
                  <Button
                    key={session.id}
                    variant={selectedSessionId === session.id ? "default" : "ghost"}
                    className="w-full justify-start text-sm"
                    onClick={() => loadSession(session.id)}
                  >
                    <div className="flex items-center">
                      <MessageCircle className="w-3 h-3 mr-2" />
                      <span className="truncate">
                        {new Date(session.start_time).toLocaleDateString('ru-RU')}
                      </span>
                      <Badge 
                        variant={session.status === 'active' ? 'default' : 'secondary'}
                        className="ml-auto text-xs"
                      >
                        {session.status === 'active' ? 'Активна' : 'Завершена'}
                      </Badge>
                    </div>
                  </Button>
                ))}
                
                {sessions.length === 0 && (
                  <p className="text-center text-muted-foreground text-sm py-4">
                    Нет сессий
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Основная область чата */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>
                {currentSession ? `Чат ${currentSession.id.slice(0, 8)}...` : 'Выберите или создайте сессию'}
              </CardTitle>
              {currentSession && (
                <Button variant="outline" onClick={endSession}>
                  Завершить Сессию
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Область сообщений */}
            <ScrollArea className="h-96 w-full p-4 border rounded-lg">
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.type === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <div className="flex items-center mb-1">
                        {message.type === 'user' ? (
                          <MessageCircle className="w-3 h-3 mr-1" />
                        ) : (
                          <Bot className="w-3 h-3 mr-1" />
                        )}
                        <span className="text-xs opacity-75">
                          {message.type === 'user' ? 'Вы' : 'ИИ'}
                        </span>
                      </div>
                      <p className="text-sm">{message.content}</p>
                    </div>
                  </div>
                ))}
                
                {isProcessing && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 px-4 py-2 rounded-lg">
                      <div className="flex items-center space-x-1">
                        <Bot className="w-3 h-3" />
                        <span className="text-sm">ИИ печатает...</span>
                        <div className="flex space-x-1">
                          <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce"></div>
                          <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                {!currentSession && (
                  <div className="text-center text-muted-foreground py-8">
                    <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-20" />
                    <p>Создайте новую сессию, чтобы начать общение</p>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Область ввода */}
            {currentSession && (
              <div className="space-y-2">
                <div className="flex space-x-2">
                  <Input
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="Введите сообщение или используйте голосовой ввод..."
                    onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendTextMessage()}
                    disabled={isProcessing}
                  />
                  <Button
                    onClick={sendTextMessage}
                    disabled={!textInput.trim() || isProcessing}
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
                
                {/* Голосовой ввод */}
                <div className="flex justify-center">
                  <Button
                    onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
                    variant={isRecording ? "destructive" : "outline"}
                    className="w-full max-w-md"
                  >
                    <Mic className="w-4 h-4 mr-2" />
                    {isRecording ? 'Остановить запись' : 'Голосовой ввод'}
                    {isRecording && (
                      <div className="ml-2 w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                    )}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default VoiceChat;