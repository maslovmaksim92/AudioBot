import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const TelegramLogin = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState('idle'); // idle, loading, error, success
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setStatus('loading');

    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          email: username,
          password: password
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Неверный логин или пароль');
      }

      const data = await response.json();
      
      // Сохраняем токен
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user || { email: username }));
      
      setStatus('success');
      
      // Перенаправляем на главную
      setTimeout(() => {
        navigate('/');
      }, 500);

    } catch (err) {
      setStatus('error');
      setError(err.message);
    }
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
          <p className="text-gray-600 mt-2">Вход в систему</p>
        </div>

        {/* Форма входа */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {status === 'success' ? (
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
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Логин
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Введите логин"
                  required
                  disabled={status === 'loading'}
                  autoComplete="username"
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Пароль
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Введите пароль"
                  required
                  disabled={status === 'loading'}
                  autoComplete="current-password"
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
                    Вход...
                  </div>
                ) : (
                  '🔐 Войти'
                )}
              </button>
            </form>
          )}
        </div>

        {/* Информация */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>🔒 Безопасный вход в систему</p>
          <p className="mt-1">Тестовые аккаунты: тест1-тест7, пароль: test123</p>
        </div>
      </div>
    </div>
  );
};

export default TelegramLogin;
