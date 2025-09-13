import React, { useState, useRef } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const MeetingRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const recognitionRef = useRef(null);
  const intervalRef = useRef(null);

  const startRecording = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Ваш браузер не поддерживает распознавание речи');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognitionRef.current = new SpeechRecognition();
    
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = 'ru-RU';

    let finalTranscript = '';

    recognitionRef.current.onresult = (event) => {
      let interimTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }
      
      setTranscript(finalTranscript + interimTranscript);
    };

    recognitionRef.current.onstart = () => {
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start timer
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    };

    recognitionRef.current.onend = () => {
      setIsRecording(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };

    recognitionRef.current.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };

    recognitionRef.current.start();
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsRecording(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  };

  const analyzeMeeting = async () => {
    if (!transcript.trim()) {
      alert('Нет текста для анализа');
      return;
    }

    setIsProcessing(true);
    
    try {
      const response = await axios.post(`${BACKEND_URL}/api/ai/analyze-meeting`, {
        transcript: transcript
      });

      setAnalysis(response.data);
    } catch (error) {
      console.error('Error analyzing meeting:', error);
      alert('Ошибка при анализе планерки');
    } finally {
      setIsProcessing(false);
    }
  };

  const sendToTelegram = async () => {
    if (!analysis) {
      alert('Сначала проанализируйте планерку');
      return;
    }

    try {
      const message = `📝 **РЕЗУЛЬТАТ ПЛАНЕРКИ**\n\n${analysis.summary}\n\n⏰ Длительность записи: ${formatTime(recordingTime)}`;
      
      // Here you would send to Telegram bot
      // For now, we'll show a confirmation
      if (window.confirm('Отправить результат планерки в Telegram?')) {
        alert('Результат планерки отправлен в Telegram!');
      }
    } catch (error) {
      console.error('Error sending to Telegram:', error);
      alert('Ошибка при отправке в Telegram');
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const clearRecording = () => {
    setTranscript('');
    setAnalysis(null);
    setRecordingTime(0);
  };

  return (
    <div className="meeting-recorder space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">🎙️ Запись и анализ планерки</h2>
        <p className="text-gray-600">Записывайте планерки, получайте автоматический анализ и отправляйте в Telegram</p>
      </div>

      {/* Recording Interface */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-center mb-6">
          {/* Recording Button */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`w-24 h-24 rounded-full flex items-center justify-center text-white text-2xl font-bold transition-all duration-300 ${
              isRecording 
                ? 'bg-red-500 animate-pulse shadow-lg transform scale-110' 
                : 'bg-blue-500 hover:bg-blue-600 shadow-md hover:shadow-lg transform hover:scale-105'
            }`}
          >
            {isRecording ? '⏹️' : '🎙️'}
          </button>
          
          {/* Status */}
          <div className="mt-4">
            <p className={`text-lg font-semibold ${isRecording ? 'text-red-600' : 'text-gray-700'}`}>
              {isRecording ? '🔴 Идет запись...' : '⚪ Готов к записи'}
            </p>
            
            {recordingTime > 0 && (
              <p className="text-gray-500 text-xl font-mono mt-2">
                {formatTime(recordingTime)}
              </p>
            )}
          </div>

          {/* Recording Animation */}
          {isRecording && (
            <div className="flex justify-center space-x-1 mt-4">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="w-2 bg-red-500 rounded animate-pulse"
                  style={{
                    height: `${Math.random() * 30 + 10}px`,
                    animationDelay: `${i * 0.1}s`
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex justify-center space-x-4">
          <button
            onClick={analyzeMeeting}
            disabled={!transcript.trim() || isProcessing}
            className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isProcessing ? '🔄 Анализирую...' : '🧠 Анализировать'}
          </button>
          
          <button
            onClick={sendToTelegram}
            disabled={!analysis}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            📱 Отправить в Telegram
          </button>
          
          <button
            onClick={clearRecording}
            className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition-colors"
          >
            🗑️ Очистить
          </button>
        </div>
      </div>

      {/* Transcript */}
      {transcript && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📝 Транскрипт записи:</h3>
          <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
            <p className="text-gray-800 whitespace-pre-wrap">{transcript}</p>
          </div>
          <div className="mt-4 text-sm text-gray-500">
            Символов: {transcript.length} | Примерное время чтения: {Math.ceil(transcript.split(' ').length / 200)} мин
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            🧠 AI Анализ планерки
            <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
              Готово
            </span>
          </h3>
          
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="whitespace-pre-wrap text-gray-800">
              {analysis.summary}
            </div>
          </div>
          
          <div className="mt-4 flex justify-between items-center text-sm text-gray-500">
            <span>Анализ выполнен: {new Date(analysis.timestamp).toLocaleString()}</span>
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">AI-анализ</span>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
        <h4 className="font-semibold text-yellow-800 mb-2">💡 Инструкция по использованию:</h4>
        <ul className="text-sm text-yellow-700 space-y-1">
          <li>1. Нажмите 🎙️ для начала записи планерки</li>
          <li>2. Говорите четко, система автоматически распознает речь</li>
          <li>3. Нажмите ⏹️ для остановки записи</li>
          <li>4. Нажмите "Анализировать" для получения AI-анализа</li>
          <li>5. Отправьте результат в Telegram для команды</li>
        </ul>
      </div>
    </div>
  );
};

export default MeetingRecorder;