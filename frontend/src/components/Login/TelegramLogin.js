import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const TelegramLogin = () => {
  const [username, setUsername] = useState('');
  const [authCode, setAuthCode] = useState('');
  const [qrCode, setQrCode] = useState('');
  const [botLink, setBotLink] = useState('');
  const [status, setStatus] = useState('idle'); // idle, waiting, error, success
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    // Проверяем, есть ли уже токен
    const token = localStorage.getItem('access_token');
    if (token) {
      navigate('/');
    }
  }, [navigate]);

  useEffect(() => {
    // Если есть authCode, начинаем polling
    if (authCode && status === 'waiting') {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`${BACKEND_URL}/api/telegram-auth/status/${authCode}`);
          const data = await response.json();

          if (data.status === 'confirmed') {
            // Успешная аутентификация!
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            setStatus('success');
            clearInterval(interval);
            
            // Перенаправляем на главную
            setTimeout(() => {
              navigate('/');
            }, 1000);
          } else if (data.status === 'expired' || data.status === 'invalid') {
            setStatus('error');
            setError('Код истёк или недействителен. Попробуйте снова.');
            clearInterval(interval);
          }
        } catch (err) {
          console.error('Error checking auth status:', err);
        }
      }, 2000); // Проверка каждые 2 секунды

      return () => clearInterval(interval);
    }
  }, [authCode, status, BACKEND_URL, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setStatus('loading');

    try {
      const response = await fetch(`${BACKEND_URL}/api/telegram-auth/init`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Ошибка входа');
      }

      const data = await response.json();
      
      setAuthCode(data.auth_code);
      setQrCode(data.qr_code);
      setBotLink(data.bot_link);
      setStatus('waiting');

    } catch (err) {
      setStatus('error');
      setError(err.message);
    }
  };

  const handleReset = () => {
    setUsername('');
    setAuthCode('');
    setQrCode('');
    setBotLink('');
    setStatus('idle');
    setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Логотип */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full mb-4 shadow-lg">
            <span className="text-4xl">🏠</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">ВашДом</h1>
          <p className="text-gray-600 mt-2">Вход через Telegram</p>
        </div>

        {/* Форма входа */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {status === 'idle' || status === 'loading' || status === 'error' ? (
            <form onSubmit={handleSubmit}>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Логин (email или имя)
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Введите ваш логин"
                  required
                  disabled={status === 'loading'}
                />
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  ❌ {error}
                </div>
              )}

              <button
                type="submit"
                disabled={status === 'loading'}
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {status === 'loading' ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Проверка...
                  </div>
                ) : (
                  '🔐 Войти через Telegram'
                )}
              </button>
            </form>
          ) : status === 'waiting' ? (
            <div className="text-center">
              <div className="mb-6">
                <div className="inline-block p-4 bg-purple-50 rounded-xl">
                  {qrCode && (
                    <img src={qrCode} alt="QR Code" className="w-48 h-48 mx-auto" />
                  )}
                </div>
              </div>

              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                📱 Отсканируйте QR-код
              </h3>
              <p className="text-gray-600 mb-4">
                или перейдите по ссылке в Telegram
              </p>

              {botLink && (
                <a
                  href={botLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block mb-6 px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-all"
                >
                  💬 Открыть в Telegram
                </a>
              )}

              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800 mb-2">
                  📝 <strong>Следующие шаги:</strong>
                </p>
                <ol className="text-sm text-blue-700 text-left space-y-1">
                  <li>1. Откройте бота в Telegram</li>
                  <li>2. Нажмите "Старт"</li>
                  <li>3. Подтвердите вход</li>
                  <li>4. Вы будете автоматически перенаправлены</li>
                </ol>
              </div>

              <div className="mt-6 flex items-center justify-center gap-2 text-gray-500">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span className="text-sm">Ожидание подтверждения...</span>
              </div>

              <button
                onClick={handleReset}
                className="mt-6 text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                ← Вернуться назад
              </button>
            </div>
          ) : status === 'success' ? (
            <div className="text-center">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-4xl">✅</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Вход выполнен!
              </h3>
              <p className="text-gray-600">
                Перенаправление...
              </p>
            </div>
          ) : null}
        </div>

        {/* Информация */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>🔒 Безопасный вход через Telegram</p>
          <p className="mt-1">Не требуется пароль</p>
        </div>
      </div>
    </div>
  );
};

export default TelegramLogin;
