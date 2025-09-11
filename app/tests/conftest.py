import pytest
import asyncio
from typing import Generator

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_voice_message():
    """Sample voice message for testing"""
    return {
        "text": "Привет! Сколько домов в управлении?",
        "user_id": "test_user_123"
    }

@pytest.fixture
def sample_telegram_update():
    """Sample Telegram update for testing"""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {"id": 123, "first_name": "TestUser", "username": "test_user"},
            "chat": {"id": 123, "type": "private"},
            "date": 1234567890,
            "text": "Тест VasDom AudioBot"
        }
    }

@pytest.fixture
def sample_meeting():
    """Sample meeting data for testing"""
    return {
        "title": "Тестовая планерка",
        "transcription": "Тестовая транскрипция встречи",
        "summary": "Краткое содержание",
        "status": "completed"
    }