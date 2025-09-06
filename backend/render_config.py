"""
Render.com Production Configuration
Environment variables and deployment settings
"""
import os
from pathlib import Path

def get_render_environment_variables():
    """
    Complete list of environment variables needed for Render.com deployment
    Copy these to your Render service Environment tab
    """
    
    # Get current domain (will be your actual Render domain)
    render_domain = os.getenv('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
    
    return {
        # ============== ОСНОВНЫЕ ПЕРЕМЕННЫЕ ==============
        "NODE_ENV": "production",
        "PORT": "8001",
        "PYTHON_VERSION": "3.11.0",
        
        # ============== БАЗА ДАННЫХ MONGO ==============
        # Замените на ваш реальный MongoDB Atlas connection string
        "MONGO_URL": "mongodb+srv://username:password@cluster.mongodb.net/vasdom?retryWrites=true&w=majority",
        "DB_NAME": "vasdom_production",
        
        # ============== AI ИНТЕГРАЦИЯ ==============
        "EMERGENT_LLM_KEY": "sk-emergent-0A408AfAeF26aCd5aB",
        
        # ============== TELEGRAM BOT ==============
        "TELEGRAM_BOT_TOKEN": "8327964628:AAHMIgT1XiGEkLc34nogRGZt-Ox-9R0TSn0",
        "TELEGRAM_WEBHOOK_URL": f"{render_domain}/api/telegram/webhook",
        "TELEGRAM_WEBHOOK_SECRET": "VasDom_Secure_Webhook_2025_Key",
        
        # ============== BITRIX24 CRM ==============
        "BITRIX24_WEBHOOK_URL": "https://vas-dom.bitrix24.ru/rest/1/2e11sgsjz1nf9l5h/",
        "BITRIX24_DOMAIN": "vas-dom.bitrix24.ru", 
        "BITRIX24_USER_ID": "1",
        "BITRIX24_SECRET": "2e11sgsjz1nf9l5h",
        
        # ============== CORS И БЕЗОПАСНОСТЬ ==============
        "CORS_ORIGINS": f"{render_domain},https://vas-dom.bitrix24.ru,https://api.telegram.org",
        "FRONTEND_URL": render_domain,
        "API_BASE_URL": f"{render_domain}/api",
        
        # ============== ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ==============
        "LOG_LEVEL": "INFO",
        "ENVIRONMENT": "production",
        "TZ": "Europe/Moscow",
        
        # ============== VOICE SERVICES (если нужны) ==============
        "SPEECH_API_KEY": "your_speech_api_key_if_needed",
        
        # ============== ДОПОЛНИТЕЛЬНАЯ БЕЗОПАСНОСТЬ ==============
        "SECRET_KEY": "VasDom_SuperSecret_Production_Key_2025",
        "ALLOWED_HOSTS": f"{render_domain.replace('https://', '')},localhost",
    }

def print_environment_setup_instructions():
    """
    Print instructions for setting up environment variables on Render
    """
    env_vars = get_render_environment_variables()
    
    print("=" * 80)
    print("🚀 RENDER.COM ENVIRONMENT VARIABLES SETUP")
    print("=" * 80)
    print()
    print("Скопируйте эти переменные в Render Dashboard > Your Service > Environment:")
    print()
    
    for key, value in env_vars.items():
        print(f"{key}={value}")
    
    print()
    print("=" * 80)
    print("📋 ПОШАГОВАЯ ИНСТРУКЦИЯ:")
    print("=" * 80)
    print()
    print("1. Зайдите на https://dashboard.render.com")
    print("2. Выберите ваш сервис (например: vasdom-app)")
    print("3. Перейдите в раздел 'Environment'")
    print("4. Добавьте каждую переменную выше (Ключ = Значение)")
    print("5. Нажмите 'Save Changes'")
    print("6. Дождитесь автоматического редеплоя")
    print()
    print("⚠️  ОБЯЗАТЕЛЬНО ЗАМЕНИТЕ:")
    print("- MONGO_URL на ваш реальный MongoDB Atlas URL")
    print("- your-app.onrender.com на ваш реальный домен Render")
    print()
    print("🔧 ПОСЛЕ ДЕПЛОЯ ВЫПОЛНИТЕ:")
    print("1. GET https://your-app.onrender.com/api/telegram/set-webhook")
    print("2. GET https://your-app.onrender.com/api/system/health")
    print("3. Проверьте работу бота в Telegram")
    print()

def validate_production_environment():
    """
    Check if all required environment variables are set for production
    """
    required_vars = [
        'MONGO_URL',
        'TELEGRAM_BOT_TOKEN', 
        'BITRIX24_WEBHOOK_URL',
        'EMERGENT_LLM_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ ОТСУТСТВУЮТ КРИТИЧЕСКИЕ ПЕРЕМЕННЫЕ:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Все критические переменные окружения настроены")
    return True

if __name__ == "__main__":
    print_environment_setup_instructions()