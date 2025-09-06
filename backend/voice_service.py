"""
Enhanced Voice Service for realistic AI voice responses
"""

import os
import tempfile
import logging
from typing import Optional, Dict, Any
import aiohttp
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class VoiceService:
    """Service for enhanced voice synthesis and processing"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "ai_voice"
        self.temp_dir.mkdir(exist_ok=True)
    
    def make_voice_natural(self, text: str) -> str:
        """Make text more natural for voice synthesis"""
        # Add pauses and emotions
        enhanced_text = text
        
        # Add pauses after important phrases
        enhanced_text = enhanced_text.replace(".", "... ")
        enhanced_text = enhanced_text.replace("!", "! ")
        enhanced_text = enhanced_text.replace("?", "? ")
        
        # Add emotional markers
        if "проблем" in text.lower() or "ошибк" in text.lower():
            enhanced_text = f"<speak><prosody rate='0.9' pitch='-10%'>{enhanced_text}</prosody></speak>"
        elif "отлично" in text.lower() or "успешно" in text.lower():
            enhanced_text = f"<speak><prosody rate='1.1' pitch='+5%'>{enhanced_text}</prosody></speak>"
        else:
            enhanced_text = f"<speak><prosody rate='1.0'>{enhanced_text}</prosody></speak>"
        
        return enhanced_text
    
    async def text_to_speech_telegram(self, text: str, voice_type: str = "director") -> Optional[bytes]:
        """Convert text to speech for Telegram voice messages"""
        try:
            # For now, we'll simulate voice generation
            # In production, you'd use a TTS service like Google Cloud TTS, Azure Speech, etc.
            
            natural_text = self.make_voice_natural(text)
            
            # Simulate voice generation (replace with real TTS service)
            voice_data = await self._generate_mock_voice(natural_text, voice_type)
            
            return voice_data
            
        except Exception as e:
            logger.error(f"Error generating voice: {e}")
            return None
    
    async def _generate_mock_voice(self, text: str, voice_type: str) -> bytes:
        """Mock voice generation - replace with real TTS service"""
        try:
            # Create a simple audio file placeholder
            # In production, replace this with actual TTS API call
            
            voice_file = self.temp_dir / f"voice_{hash(text)}.ogg"
            
            # For demo purposes, create a minimal OGG file
            # This should be replaced with actual TTS service
            mock_ogg_data = b'\x4f\x67\x67\x53\x00\x02\x00\x00'  # OGG header
            
            with open(voice_file, 'wb') as f:
                f.write(mock_ogg_data)
            
            with open(voice_file, 'rb') as f:
                voice_data = f.read()
            
            # Clean up temp file
            voice_file.unlink(missing_ok=True)
            
            return voice_data
            
        except Exception as e:
            logger.error(f"Error in mock voice generation: {e}")
            return b""
    
    def add_director_personality(self, text: str) -> str:
        """Add director personality to voice text"""
        # Add director-like speech patterns
        director_phrases = {
            "я думаю": "по моему анализу",
            "возможно": "рекомендую",
            "может быть": "необходимо",
            "попробуйте": "выполните",
            "стоит": "требуется"
        }
        
        enhanced_text = text
        for casual, formal in director_phrases.items():
            enhanced_text = enhanced_text.replace(casual, formal)
        
        # Add director intro phrases
        if not any(phrase in enhanced_text.lower() for phrase in ["по данным", "анализ показывает", "рекомендую"]):
            enhanced_text = f"По данным системы: {enhanced_text}"
        
        return enhanced_text
    
    def format_for_speech(self, text: str) -> str:
        """Format text for better speech synthesis"""
        # Replace numbers with words
        replacements = {
            "₽": "рублей",
            "%": "процентов",
            "№": "номер",
            "&": "и",
            "г.": "город",
            "тыс.": "тысяч",
            "млн": "миллионов"
        }
        
        formatted_text = text
        for symbol, word in replacements.items():
            formatted_text = formatted_text.replace(symbol, word)
        
        # Break long sentences
        if len(formatted_text) > 200:
            sentences = formatted_text.split('.')
            formatted_text = '. '.join(sentences[:3]) + '.'
        
        return formatted_text

# Global voice service instance
voice_service = VoiceService()

# Utility functions
async def generate_voice_message(text: str, voice_type: str = "director") -> Optional[bytes]:
    """Generate voice message for Telegram"""
    try:
        # Add director personality
        enhanced_text = voice_service.add_director_personality(text)
        
        # Format for speech
        speech_text = voice_service.format_for_speech(enhanced_text)
        
        # Generate voice
        voice_data = await voice_service.text_to_speech_telegram(speech_text, voice_type)
        
        return voice_data
        
    except Exception as e:
        logger.error(f"Error generating voice message: {e}")
        return None

def make_text_conversational(text: str) -> str:
    """Make text more conversational for voice"""
    # Add natural speech patterns
    conversational = text
    
    # Add thinking pauses
    conversational = conversational.replace("Анализирую", "Так... анализирую")
    conversational = conversational.replace("Проверяю", "Минуточку, проверяю")
    conversational = conversational.replace("Рекомендую", "Вот что я рекомендую")
    
    # Add confirmations
    if "?" in conversational:
        conversational += " Понятно?"
    
    return conversational