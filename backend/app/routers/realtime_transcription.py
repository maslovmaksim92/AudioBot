from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI
import os
import logging
import json
import base64

router = APIRouter()
logger = logging.getLogger(__name__)

# Инициализация OpenAI клиента
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint для транскрипции аудио в реальном времени.
    Клиент отправляет аудио чанки, сервер возвращает транскрипцию через Whisper API.
    """
    await websocket.accept()
    logger.info("🎤 WebSocket connection established for transcription")
    
    try:
        while True:
            # Получаем данные от клиента
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "audio":
                # Получаем base64 закодированное аудио
                audio_base64 = message.get("audio")
                
                if not audio_base64:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No audio data provided"
                    })
                    continue
                
                try:
                    # Декодируем аудио из base64
                    audio_data = base64.b64decode(audio_base64)
                    
                    # Сохраняем временно в файл (Whisper API требует файл)
                    temp_file = "/tmp/temp_audio.webm"
                    with open(temp_file, "wb") as f:
                        f.write(audio_data)
                    
                    # Отправляем на Whisper API
                    logger.info("📤 Sending audio to Whisper API...")
                    with open(temp_file, "rb") as audio_file:
                        transcription = await client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="ru",  # Русский язык
                            response_format="text"
                        )
                    
                    # Отправляем транскрипцию обратно клиенту
                    await websocket.send_json({
                        "type": "transcription",
                        "text": transcription,
                        "is_final": True
                    })
                    logger.info(f"✅ Transcription: {transcription}")
                    
                except Exception as e:
                    logger.error(f"❌ Transcription error: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Transcription failed: {str(e)}"
                    })
            
            elif message.get("type") == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
