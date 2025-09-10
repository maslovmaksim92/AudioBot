import React, { useState, useRef, useEffect } from 'react';
import { 
  Phone, PhoneCall, PhoneOff, Mic, MicOff, 
  Volume2, VolumeX, Loader2, AlertCircle, CheckCircle2 
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const LiveVoiceChat = () => {
  // Connection states
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [connectionError, setConnectionError] = useState('');
  
  // Audio states
  const [isListening, setIsListening] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [transcription, setTranscription] = useState('');
  
  // Real-time feedback
  const [aiSpeaking, setAiSpeaking] = useState(false);
  const [currentMessage, setCurrentMessage] = useState('');
  
  // Refs
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const processorRef = useRef(null);
  const analyserRef = useRef(null);
  const audioLevelIntervalRef = useRef(null);

  const initializeRealtimeConnection = async () => {
    try {
      setIsConnecting(true);
      setConnectionStatus('connecting');
      setConnectionError('');
      setTranscription('Инициализация соединения с GPT-4o Realtime...');

      // Get user media first
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      mediaStreamRef.current = stream;
      
      // Create audio context
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000
      });

      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      
      source.connect(analyserRef.current);

      // Create script processor for audio data
      processorRef.current = audioContextRef.current.createScriptProcessor(1024, 1, 1);
      source.connect(processorRef.current);
      processorRef.current.connect(audioContextRef.current.destination);

      // WebSocket connection
      const wsUrl = BACKEND_URL.replace(/^https/, 'wss').replace(/^http/, 'ws') + '/ws/realtime';
      wsRef.current = new WebSocket(wsUrl);

      // Connection timeout
      const connectionTimeout = setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState !== WebSocket.OPEN) {
          wsRef.current.close();
          setConnectionError('Timeout: Не удалось подключиться к серверу');
          startVoiceSimulation(); // Fallback
        }
      }, 10000);

      wsRef.current.onopen = () => {
        clearTimeout(connectionTimeout);
        setIsConnected(true);
        setIsConnecting(false);
        setConnectionStatus('connected');
        setTranscription('🎉 Живой голос GPT-4o активен! Говорите что-нибудь...');
        
        // Start audio level monitoring
        startAudioLevelMonitoring();
        
        // Setup audio processing
        processorRef.current.onaudioprocess = (event) => {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && !isMuted) {
            const inputBuffer = event.inputBuffer.getChannelData(0);
            const pcmData = new Int16Array(inputBuffer.length);
            
            // Convert float32 to int16
            for (let i = 0; i < inputBuffer.length; i++) {
              pcmData[i] = Math.max(-32768, Math.min(32767, inputBuffer[i] * 32768));
            }
            
            const base64Audio = btoa(String.fromCharCode.apply(null, new Uint8Array(pcmData.buffer)));
            
            wsRef.current.send(JSON.stringify({
              type: "input_audio_buffer.append",
              audio: base64Audio
            }));
          }
        };
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleRealtimeMessage(data);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('Ошибка WebSocket соединения');
        startVoiceSimulation(); // Fallback
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        setConnectionStatus('disconnected');
        cleanup();
      };

    } catch (error) {
      console.error('Connection error:', error);
      setConnectionError(`Ошибка: ${error.message}`);
      setIsConnecting(false);
      startVoiceSimulation(); // Fallback
    }
  };

  const handleRealtimeMessage = (data) => {
    switch (data.type) {
      case 'input_audio_buffer.speech_started':
        setIsListening(true);
        setTranscription('🎤 Слушаю вашу речь...');
        break;
        
      case 'input_audio_buffer.speech_stopped':
        setIsListening(false);
        setTranscription('✋ Речь остановлена, обрабатываю...');
        // Commit the audio buffer
        if (wsRef.current) {
          wsRef.current.send(JSON.stringify({ type: "input_audio_buffer.commit" }));
        }
        break;
        
      case 'conversation.item.input_audio_transcription.completed':
        if (data.transcript) {
          setTranscription(`Вы сказали: "${data.transcript}"`);
          setCurrentMessage(data.transcript);
        }
        break;
        
      case 'response.audio.delta':
        setAiSpeaking(true);
        if (data.delta) {
          // Here you would implement audio playback
          playAudioDelta(data.delta);
        }
        break;
        
      case 'response.audio.done':
        setAiSpeaking(false);
        break;
        
      case 'response.text.delta':
        if (data.delta) {
          setCurrentMessage(prev => prev + data.delta);
        }
        break;
        
      case 'error':
        setConnectionError(`AI Error: ${data.error?.message || 'Unknown error'}`);
        break;
        
      default:
        console.log('Unhandled message type:', data.type);
    }
  };

  const playAudioDelta = (base64Audio) => {
    try {
      const audioData = atob(base64Audio);
      const arrayBuffer = new ArrayBuffer(audioData.length);
      const view = new Uint8Array(arrayBuffer);
      
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i) & 0xff;
      }
      
      // Convert to audio and play
      if (audioContextRef.current) {
        audioContextRef.current.decodeAudioData(arrayBuffer, (audioBuffer) => {
          const source = audioContextRef.current.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(audioContextRef.current.destination);
          source.start();
        });
      }
    } catch (error) {
      console.error('Error playing audio:', error);
    }
  };

  const startAudioLevelMonitoring = () => {
    if (!analyserRef.current) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    
    const updateAudioLevel = () => {
      if (analyserRef.current && isConnected) {
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(Math.min(100, (average / 255) * 100));
        requestAnimationFrame(updateAudioLevel);
      }
    };
    
    updateAudioLevel();
  };

  const startVoiceSimulation = () => {
    // Fallback simulation mode
    setConnectionStatus('simulation');
    setTranscription('🎭 Режим симуляции активен (WebSocket недоступен)');
    
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        mediaStreamRef.current = stream;
        setIsConnected(true);
        setIsConnecting(false);
        
        // Simulate audio level changes
        audioLevelIntervalRef.current = setInterval(() => {
          const level = Math.random() * 100;
          setAudioLevel(level);
          
          if (level > 30 && !isListening) {
            setIsListening(true);
            setTranscription('🎤 [СИМУЛЯЦИЯ] Обнаружена речь!');
          } else if (level < 10 && isListening) {
            setIsListening(false);
            setTranscription('✋ [СИМУЛЯЦИЯ] Речь остановлена');
          }
        }, 100);
      })
      .catch(error => {
        setConnectionError(`Ошибка доступа к микрофону: ${error.message}`);
        setIsConnecting(false);
      });
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    cleanup();
  };

  const cleanup = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    if (audioLevelIntervalRef.current) {
      clearInterval(audioLevelIntervalRef.current);
    }
    
    setIsConnected(false);
    setIsConnecting(false);
    setIsListening(false);
    setAiSpeaking(false);
    setAudioLevel(0);
    setTranscription('');
    setCurrentMessage('');
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-sm border-b border-white/10 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
              <Phone className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Живой голосовой чат</h1>
              <p className="text-gray-400">GPT-4o Realtime API • Человеческий голос</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Connection Status */}
            <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
              connectionStatus === 'connected' ? 'bg-green-500/20 text-green-400' :
              connectionStatus === 'connecting' ? 'bg-yellow-500/20 text-yellow-400' :
              connectionStatus === 'simulation' ? 'bg-blue-500/20 text-blue-400' :
              'bg-red-500/20 text-red-400'
            }`}>
              {connectionStatus === 'connected' && <CheckCircle2 size={16} />}
              {connectionStatus === 'connecting' && <Loader2 className="animate-spin" size={16} />}
              {connectionStatus === 'disconnected' && <AlertCircle size={16} />}
              {connectionStatus === 'simulation' && <AlertCircle size={16} />}
              <span className="text-sm font-medium">
                {connectionStatus === 'connected' ? 'Подключен' :
                 connectionStatus === 'connecting' ? 'Подключение...' :
                 connectionStatus === 'simulation' ? 'Симуляция' :
                 'Отключен'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6 space-y-6">
        {/* Connection Button */}
        {!isConnected && (
          <div className="text-center">
            <button
              onClick={initializeRealtimeConnection}
              disabled={isConnecting}
              className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-12 py-6 rounded-full text-xl font-bold transition-all hover:scale-105 flex items-center justify-center space-x-3 mx-auto"
            >
              {isConnecting ? (
                <>
                  <Loader2 className="animate-spin" size={32} />
                  <span>Подключение...</span>
                </>
              ) : (
                <>
                  <PhoneCall size={32} />
                  <span>Начать живой разговор</span>
                </>
              )}
            </button>
            
            <p className="text-gray-400 mt-4 max-w-md mx-auto">
              Нажмите для подключения к GPT-4o Realtime API. 
              Вам будет предложено разрешить доступ к микрофону.
            </p>
            
            {connectionError && (
              <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg max-w-md mx-auto">
                <p className="text-red-400 text-sm">{connectionError}</p>
              </div>
            )}
          </div>
        )}

        {/* Live Voice Interface */}
        {isConnected && (
          <div className="space-y-6">
            {/* Status Panel */}
            <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border-2 border-green-500/50 rounded-xl p-8">
              <div className="text-center mb-6">
                <div className="flex items-center justify-center space-x-4 mb-4">
                  <div className="w-6 h-6 bg-green-400 rounded-full animate-pulse" />
                  <h2 className="text-3xl font-bold text-green-400">🎙️ ЖИВОЙ ГОЛОС АКТИВЕН</h2>
                  <div className="w-6 h-6 bg-green-400 rounded-full animate-pulse" />
                </div>
                {connectionStatus === 'simulation' && (
                  <p className="text-yellow-400 font-medium">Режим симуляции (WebSocket недоступен)</p>
                )}
              </div>

              {/* Audio Level Indicator */}
              <div className="bg-black/30 rounded-xl p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-lg font-medium text-white">🔊 Уровень микрофона</span>
                  <span className="text-2xl font-bold text-green-400">{Math.round(audioLevel)}%</span>
                </div>
                <div className="w-full h-8 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 transition-all duration-100"
                    style={{ width: `${Math.max(5, audioLevel)}%` }}
                  />
                </div>
                <div className="text-center mt-2 text-sm text-gray-400">
                  {audioLevel > 30 ? '🗣️ Громко говорите!' : audioLevel > 10 ? '🤫 Тихо...' : '🔇 Тишина'}
                </div>
              </div>

              {/* Speaking Status */}
              <div className="bg-black/30 rounded-xl p-6">
                <div className="flex items-center space-x-4">
                  <div className={`p-4 rounded-full ${
                    isListening ? 'bg-red-500 animate-pulse' : 
                    aiSpeaking ? 'bg-purple-500 animate-pulse' : 
                    'bg-blue-500'
                  }`}>
                    {isListening ? (
                      <Mic className="text-white" size={32} />
                    ) : aiSpeaking ? (
                      <Volume2 className="text-white" size={32} />
                    ) : (
                      <Phone className="text-white" size={32} />
                    )}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-white">
                      {isListening ? '🎤 СЛУШАЮ ВАШУ РЕЧЬ...' : 
                       aiSpeaking ? '🔊 AI ГОВОРИТ...' : 
                       '🤖 AI ГОТОВ К ОТВЕТУ'}
                    </h3>
                    <p className="text-lg text-gray-300 mt-2">
                      {transcription || 'Говорите что-нибудь, чтобы начать разговор'}
                    </p>
                    {isListening && (
                      <div className="flex items-center space-x-2 mt-3">
                        <span className="text-red-400 font-medium">ЗАПИСЬ:</span>
                        <div className="flex space-x-1">
                          {[0, 1, 2, 3, 4].map(i => (
                            <div 
                              key={i}
                              className="w-2 h-6 bg-red-400 rounded animate-pulse"
                              style={{animationDelay: `${i * 0.1}s`}}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Current Message */}
            {currentMessage && (
              <div className="bg-black/20 border border-white/10 rounded-xl p-6">
                <h3 className="text-lg font-bold text-white mb-3">Текущий диалог:</h3>
                <p className="text-gray-300 leading-relaxed">{currentMessage}</p>
              </div>
            )}

            {/* Controls */}
            <div className="flex justify-center space-x-6">
              <button
                onClick={toggleMute}
                className={`p-4 rounded-full transition-all ${
                  isMuted 
                    ? 'bg-red-500 hover:bg-red-600 text-white' 
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                }`}
              >
                {isMuted ? <MicOff size={24} /> : <Mic size={24} />}
              </button>
              
              <button
                onClick={disconnect}
                className="bg-red-500 hover:bg-red-600 text-white p-4 rounded-full transition-all"
              >
                <PhoneOff size={24} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveVoiceChat;