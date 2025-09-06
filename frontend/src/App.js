import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState('generator');
  const [bitrixMethods, setBitrixMethods] = useState({});
  const [selectedCategory, setSelectedCategory] = useState('crm');
  const [selectedMethod, setSelectedMethod] = useState('');
  const [parameters, setParameters] = useState('{}');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [webhookStatus, setWebhookStatus] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [sessionId] = useState(() => 'session-' + Date.now());

  useEffect(() => {
    loadBitrixMethods();
    testConnection();
  }, []);

  const testConnection = async () => {
    try {
      const response = await axios.get(`${API}/`);
      console.log('Backend connected:', response.data.message);
    } catch (e) {
      console.error('Backend connection error:', e);
    }
  };

  const loadBitrixMethods = async () => {
    try {
      const response = await axios.get(`${API}/bitrix/methods`);
      setBitrixMethods(response.data);
      if (response.data.crm && response.data.crm.length > 0) {
        setSelectedMethod(response.data.crm[0]);
      }
    } catch (e) {
      console.error('Error loading methods:', e);
    }
  };

  const setWebhook = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/telegram/set-webhook`);
      setWebhookStatus(response.data);
    } catch (e) {
      setWebhookStatus({ success: false, error: e.response?.data?.detail || e.message });
    }
    setLoading(false);
  };

  const executeBitrixRequest = async () => {
    if (!selectedMethod) return;
    
    setLoading(true);
    try {
      let params = {};
      try {
        params = JSON.parse(parameters);
      } catch (e) {
        throw new Error('Неверный формат параметров JSON');
      }

      const response = await axios.post(`${API}/bitrix/request`, {
        method: selectedMethod,
        parameters: params
      });
      setResponse(response.data);
    } catch (e) {
      setResponse({ 
        success: false, 
        error: e.response?.data?.detail || e.message 
      });
    }
    setLoading(false);
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;

    const userMessage = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');

    try {
      const response = await axios.post(`${API}/chat`, {
        message: chatInput,
        session_id: sessionId
      });

      const aiMessage = { role: 'assistant', content: response.data.response };
      setChatMessages(prev => [...prev, aiMessage]);
    } catch (e) {
      const errorMessage = { role: 'error', content: 'Ошибка: ' + (e.response?.data?.detail || e.message) };
      setChatMessages(prev => [...prev, errorMessage]);
    }
  };

  const CategoryButton = ({ category, label, active, onClick }) => (
    <button
      className={`px-4 py-2 rounded-lg font-medium transition-all ${
        active
          ? 'bg-blue-600 text-white shadow-md'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
      onClick={onClick}
    >
      {label}
    </button>
  );

  const MethodCard = ({ method, selected, onClick }) => (
    <div
      className={`p-4 border rounded-lg cursor-pointer transition-all ${
        selected
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
      }`}
      onClick={onClick}
    >
      <div className="font-mono text-sm text-blue-600">{method}</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">Генератор запросов Bitrix24</h1>
            <div className="flex space-x-4">
              <button
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'generator'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                onClick={() => setActiveTab('generator')}
              >
                Генератор
              </button>
              <button
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'webhook'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                onClick={() => setActiveTab('webhook')}
              >
                Webhook
              </button>
              <button
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'chat'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                onClick={() => setActiveTab('chat')}
              >
                AI Чат
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'generator' && (
          <div className="space-y-6">
            {/* Method Selection */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Метод</h2>
              
              <div className="flex space-x-2 mb-6">
                <CategoryButton
                  category="crm"
                  label="CRM"
                  active={selectedCategory === 'crm'}
                  onClick={() => {
                    setSelectedCategory('crm');
                    if (bitrixMethods.crm?.length > 0) {
                      setSelectedMethod(bitrixMethods.crm[0]);
                    }
                  }}
                />
                <CategoryButton
                  category="task"
                  label="Задачи"
                  active={selectedCategory === 'task'}
                  onClick={() => {
                    setSelectedCategory('task');
                    if (bitrixMethods.task?.length > 0) {
                      setSelectedMethod(bitrixMethods.task[0]);
                    }
                  }}
                />
                <CategoryButton
                  category="user"
                  label="Пользователи"
                  active={selectedCategory === 'user'}
                  onClick={() => {
                    setSelectedCategory('user');
                    if (bitrixMethods.user?.length > 0) {
                      setSelectedMethod(bitrixMethods.user[0]);
                    }
                  }}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {bitrixMethods[selectedCategory]?.map((method) => (
                  <MethodCard
                    key={method}
                    method={method}
                    selected={selectedMethod === method}
                    onClick={() => setSelectedMethod(method)}
                  />
                ))}
              </div>

              {selectedMethod && (
                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-blue-200 rounded flex items-center justify-center">
                      <span className="text-blue-600 font-bold">+</span>
                    </div>
                    <div>
                      <div className="font-mono text-sm text-blue-600">{selectedMethod}</div>
                      <div className="text-xs text-blue-500">выбрать</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Parameters */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Параметры</h2>
              <textarea
                className="w-full h-32 p-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={parameters}
                onChange={(e) => setParameters(e.target.value)}
                placeholder='{"select": ["ID", "TITLE"], "filter": {"STAGE_ID": "NEW"}}'
              />
              <p className="text-xs text-gray-500 mt-2">Введите параметры в формате JSON</p>
            </div>

            {/* Execute Button */}
            <div className="flex justify-center">
              <button
                className="px-8 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                onClick={executeBitrixRequest}
                disabled={loading || !selectedMethod}
              >
                {loading ? 'Выполняется...' : 'Выполнить запрос'}
              </button>
            </div>

            {/* Response */}
            {response && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Ответ</h2>
                <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-auto max-h-96">
                  {JSON.stringify(response, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {activeTab === 'webhook' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Настройка Telegram Webhook</h2>
              <p className="text-gray-600 mb-6">
                Для активации Telegram бота необходимо установить webhook
              </p>
              
              <button
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-all"
                onClick={setWebhook}
                disabled={loading}
              >
                {loading ? 'Устанавливается...' : 'Установить Webhook'}
              </button>

              {webhookStatus && (
                <div className={`mt-6 p-4 rounded-lg ${
                  webhookStatus.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                }`}>
                  <div className={`font-medium ${
                    webhookStatus.success ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {webhookStatus.success ? '✅ Webhook установлен' : '❌ Ошибка установки'}
                  </div>
                  <div className="text-sm mt-2 text-gray-600">
                    <pre>{JSON.stringify(webhookStatus, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'chat' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Помощник</h2>
              
              <div className="h-96 border border-gray-300 rounded-lg p-4 overflow-y-auto mb-4 bg-gray-50">
                {chatMessages.length === 0 ? (
                  <div className="text-gray-500 text-center py-8">
                    Начните диалог с AI помощником
                  </div>
                ) : (
                  <div className="space-y-4">
                    {chatMessages.map((msg, index) => (
                      <div
                        key={index}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                            msg.role === 'user'
                              ? 'bg-blue-600 text-white'
                              : msg.role === 'error'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-white border border-gray-200'
                          }`}
                        >
                          <div className="text-sm">{msg.content}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex space-x-2">
                <input
                  type="text"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                  placeholder="Задайте вопрос AI помощнику..."
                />
                <button
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all"
                  onClick={sendChatMessage}
                >
                  Отправить
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;