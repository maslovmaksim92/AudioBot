import React, { useState, useEffect, useRef } from "react";
import { 
  Send, 
  Mic, 
  MicOff, 
  Phone, 
  PhoneOff, 
  Volume2, 
  VolumeX, 
  Bot, 
  User,
  Loader,
  Zap,
  Radio
} from "lucide-react";
import { useLocation } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AIChat = () => {
  const location = useLocation();
  const isVoicePage = location.pathname === "/voice";
  
  // State management
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isLiveConnected, setIsLiveConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  
  // Refs
  const messagesEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const peerConnectionRef = useRef(null);
  const audioRef = useRef(null);
  const realtimeTokenRef = useRef(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window) {
      const recognition = new window.webkitSpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'ru-RU';
      
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage(transcript);
      };
      
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
      };
      
      recognition.onend = () => {
        setIsRecording(false);
      };
      
      recognitionRef.current = recognition;
    }
  }, []);

  // Send text message
  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage("");
    setIsLoading(true);

    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      text: userMessage,
      sender: "user",
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await fetch(`${BACKEND_URL}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();

      // Add AI response to chat
      const aiMessage = {
        id: Date.now() + 1,
        text: data.response,
        sender: "ai",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMessage]);

      // Speak the response if not muted
      if (!isMuted && !isVoicePage) {
        speakText(data.response);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: "Извините, произошла ошибка при отправке сообщения. Попробуйте еще раз.",
        sender: "ai",
        timestamp: new Date(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Text-to-speech function
  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ru-RU';
      utterance.rate = 0.9;
      utterance.pitch = 1;
      window.speechSynthesis.speak(utterance);
    }
  };

  // Start/stop voice recording
  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
    } else {
      if (recognitionRef.current) {
        recognitionRef.current.start();
        setIsRecording(true);
      }
    }
  };

  // Get OpenAI Realtime token
  const getRealtimeToken = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/realtime/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get realtime token');
      }

      const data = await response.json();
      realtimeTokenRef.current = data.token;
      return data.token;
    } catch (error) {
      console.error('Error getting realtime token:', error);
      throw error;
    }
  };

  // Initialize WebSocket connection to OpenAI Realtime API
  const initializeRealtimeConnection = async () => {
    try {
      setConnectionStatus("connecting");
      
      // Connect to our WebSocket proxy
      const wsUrl = BACKEND_URL.replace(/^https?/, 'ws') + '/ws/realtime';
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('Connected to Realtime API');
        setIsLiveConnected(true);
        setConnectionStatus("connected");
        
        // Get user media (microphone) for audio input
        navigator.mediaDevices.getUserMedia({ audio: true })
          .then(stream => {
            const mediaRecorder = new MediaRecorder(stream, {
              mimeType: 'audio/webm;codecs=opus'
            });
            
            mediaRecorder.ondataavailable = (event) => {
              if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
                // Convert audio data to base64 and send to OpenAI
                const reader = new FileReader();
                reader.onload = () => {
                  const audioData = reader.result.split(',')[1]; // Remove data URL prefix
                  ws.send(JSON.stringify({
                    type: "input_audio_buffer.append",
                    audio: audioData
                  }));
                };
                reader.readAsDataURL(event.data);
              }
            };
            
            // Start recording continuously
            mediaRecorder.start(100); // Send data every 100ms
            mediaRecorderRef.current = mediaRecorder;
          })
          .catch(err => {
            console.error('Error accessing microphone:', err);
            setConnectionStatus("failed");
            setIsLiveConnected(false);
          });
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Received:', data);
          
          // Handle different message types
          switch (data.type) {
            case "response.audio.delta":
              // Play incoming audio
              if (data.delta && audioRef.current) {
                const audioData = atob(data.delta);
                const audioArray = new Uint8Array(audioData.length);
                for (let i = 0; i < audioData.length; i++) {
                  audioArray[i] = audioData.charCodeAt(i);
                }
                
                // Create audio blob and play
                const audioBlob = new Blob([audioArray], { type: 'audio/pcm' });
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                audio.play().catch(e => console.error('Audio play error:', e));
              }
              break;
              
            case "response.text.delta":
              // Display text response in chat
              if (data.delta) {
                const aiMessage = {
                  id: Date.now(),
                  text: data.delta,
                  sender: "ai",
                  timestamp: new Date()
                };
                setMessages(prev => [...prev, aiMessage]);
              }
              break;
              
            case "input_audio_buffer.speech_started":
              console.log("Speech started");
              break;
              
            case "input_audio_buffer.speech_stopped":
              console.log("Speech stopped");
              // Commit the audio buffer
              ws.send(JSON.stringify({
                type: "input_audio_buffer.commit"
              }));
              break;
              
            case "error":
              console.error("OpenAI Realtime error:", data);
              setConnectionStatus("failed");
              break;
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus("failed");
        setIsLiveConnected(false);
      };
      
      ws.onclose = () => {
        console.log('WebSocket connection closed');
        setIsLiveConnected(false);
        setConnectionStatus("disconnected");
        
        // Stop media recorder
        if (mediaRecorderRef.current) {
          mediaRecorderRef.current.stop();
          mediaRecorderRef.current = null;
        }
      };
      
      // Store WebSocket reference
      peerConnectionRef.current = ws;
      
    } catch (error) {
      console.error('Error initializing realtime connection:', error);
      setConnectionStatus("failed");
      setIsLiveConnected(false);
    }
  };

  // Disconnect from live voice
  const disconnectLiveVoice = () => {
    if (peerConnectionRef.current && peerConnectionRef.current instanceof WebSocket) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    
    // Stop media recorder
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    
    setIsLiveConnected(false);
    setConnectionStatus("disconnected");
    
    if (audioRef.current) {
      audioRef.current.srcObject = null;
    }
  };

  // Toggle live voice connection
  const toggleLiveVoice = () => {
    if (isLiveConnected) {
      disconnectLiveVoice();
    } else {
      initializeRealtimeConnection();
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="h-full max-w-6xl mx-auto">
      {/* Header */}
      <div className="glass rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl">
              <Bot className="text-white" size={28} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">
                {isVoicePage ? "Живой голосовой чат" : "AI Чат"}
              </h1>
              <p className="text-gray-400">
                {isVoicePage 
                  ? "Разговаривайте с AI человеческим голосом" 
                  : "Общайтесь с умным AI помощником"
                }
              </p>
            </div>
          </div>
          
          {/* Voice controls */}
          {isVoicePage && (
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${
                connectionStatus === "connected" ? "bg-green-500/20 border border-green-500/30" :
                connectionStatus === "connecting" ? "bg-yellow-500/20 border border-yellow-500/30" :
                "bg-red-500/20 border border-red-500/30"
              }`}>
                <Radio size={16} className={`${
                  connectionStatus === "connected" ? "text-green-400" :
                  connectionStatus === "connecting" ? "text-yellow-400" :
                  "text-red-400"
                }`} />
                <span className={`text-sm font-medium ${
                  connectionStatus === "connected" ? "text-green-400" :
                  connectionStatus === "connecting" ? "text-yellow-400" :
                  "text-red-400"
                }`}>
                  {connectionStatus === "connected" ? "Подключено" :
                   connectionStatus === "connecting" ? "Подключение..." :
                   "Отключено"}
                </span>
              </div>
              
              <button
                onClick={toggleLiveVoice}
                disabled={connectionStatus === "connecting"}
                className={`p-3 rounded-lg transition-all duration-300 ${
                  isLiveConnected
                    ? "bg-red-500 hover:bg-red-600 text-white"
                    : "bg-green-500 hover:bg-green-600 text-white"
                } ${connectionStatus === "connecting" ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                {connectionStatus === "connecting" ? (
                  <Loader className="animate-spin" size={24} />
                ) : isLiveConnected ? (
                  <PhoneOff size={24} />
                ) : (
                  <Phone size={24} />
                )}
              </button>
            </div>
          )}
          
          {/* Text chat controls */}
          {!isVoicePage && (
            <button
              onClick={() => setIsMuted(!isMuted)}
              className={`p-3 rounded-lg transition-all duration-300 ${
                isMuted ? "bg-red-500/20 text-red-400" : "bg-blue-500/20 text-blue-400"
              }`}
            >
              {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
            </button>
          )}
        </div>
      </div>

      {/* Live voice connection status */}
      {isVoicePage && isLiveConnected && (
        <div className="glass rounded-xl p-6 mb-6 bg-green-500/10 border border-green-500/20">
          <div className="flex items-center space-x-4">
            <div className="w-4 h-4 bg-green-400 rounded-full live-indicator" />
            <div>
              <h3 className="text-lg font-bold text-green-400">Живое соединение активно</h3>
              <p className="text-gray-300">Говорите естественно, AI будет отвечать человеческим голосом</p>
            </div>
          </div>
        </div>
      )}

      {/* Chat Messages */}
      <div className="glass rounded-xl p-6 mb-6 h-96 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <div className="p-4 bg-gradient-to-r from-blue-500/20 to-purple-600/20 rounded-xl">
              <Bot className="text-blue-400" size={48} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-2">
                {isVoicePage ? "Готов к живому общению!" : "Начните разговор"}
              </h3>
              <p className="text-gray-400">
                {isVoicePage 
                  ? "Нажмите кнопку подключения для начала голосового чата"
                  : "Задайте любой вопрос или просто поздоровайтесь"
                }
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex items-start space-x-3 message-appear ${
                  message.sender === "user" ? "flex-row-reverse space-x-reverse" : ""
                }`}
              >
                <div className={`p-2 rounded-lg flex-shrink-0 ${
                  message.sender === "user" 
                    ? "bg-gradient-to-r from-blue-500 to-purple-600" 
                    : message.error
                    ? "bg-red-500/20"
                    : "bg-gradient-to-r from-green-500 to-emerald-600"
                }`}>
                  {message.sender === "user" ? (
                    <User className="text-white" size={16} />
                  ) : (
                    <Bot className="text-white" size={16} />
                  )}
                </div>
                <div className={`flex-1 ${
                  message.sender === "user" ? "text-right" : ""
                }`}>
                  <div className={`inline-block p-4 rounded-xl max-w-md ${
                    message.sender === "user"
                      ? "bg-blue-500/20 border border-blue-500/30 text-white"
                      : message.error
                      ? "bg-red-500/20 border border-red-500/30 text-red-300"
                      : "bg-white/10 border border-white/20 text-white"
                  }`}>
                    <p className="whitespace-pre-wrap">{message.text}</p>
                    <p className="text-xs opacity-70 mt-2">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex items-start space-x-3">
                <div className="p-2 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg">
                  <Bot className="text-white" size={16} />
                </div>
                <div className="bg-white/10 border border-white/20 rounded-xl p-4">
                  <div className="flex items-center space-x-2">
                    <Loader className="animate-spin text-blue-400" size={16} />
                    <span className="text-gray-300">AI думает...</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Only show for text chat or when not connected to live voice */}
      {(!isVoicePage || !isLiveConnected) && (
        <div className="glass rounded-xl p-6">
          <div className="flex items-end space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isVoicePage ? "Или напишите сообщение..." : "Введите сообщение..."}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                rows="2"
                disabled={isLoading}
              />
            </div>
            
            {/* Voice input button */}
            {!isVoicePage && (
              <button
                onClick={toggleRecording}
                disabled={isLoading}
                className={`p-3 rounded-lg transition-all duration-300 ${
                  isRecording
                    ? "bg-red-500 hover:bg-red-600 recording-pulse"
                    : "bg-purple-500 hover:bg-purple-600"
                } text-white disabled:opacity-50`}
              >
                {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
              </button>
            )}
            
            {/* Send button */}
            <button
              onClick={sendMessage}
              disabled={isLoading || !inputMessage.trim()}
              className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-lg text-white transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed pulse-glow"
            >
              {isLoading ? (
                <Loader className="animate-spin" size={20} />
              ) : (
                <Send size={20} />
              )}
            </button>
          </div>
          
          {isRecording && (
            <div className="mt-4 flex items-center justify-center space-x-2 text-red-400">
              <div className="w-3 h-3 bg-red-400 rounded-full recording-pulse" />
              <span className="text-sm">Говорите...</span>
            </div>
          )}
        </div>
      )}

      {/* Hidden audio element for live voice */}
      <audio ref={audioRef} autoPlay className="hidden" />
    </div>
  );
};

export default AIChat;