import React, { useState, useCallback } from 'react';
import {
  ReactFlow,
  addEdge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './FunctionStudio.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL;

// Типы узлов для автоматизации
const NODE_TYPES = {
  TRIGGER: {
    type: 'trigger',
    label: '⚡ Триггер',
    color: '#10b981',
    options: [
      { value: 'cron', label: 'По расписанию (Cron)' },
      { value: 'webhook', label: 'Webhook' },
      { value: 'telegram_message', label: 'Сообщение в Telegram' },
      { value: 'bitrix_task', label: 'Задача в Bitrix24' },
      { value: 'manual', label: 'Ручной запуск' }
    ]
  },
  CONDITION: {
    type: 'condition',
    label: '❓ Условие',
    color: '#f59e0b',
    options: [
      { value: 'if', label: 'Если...' },
      { value: 'switch', label: 'Выбор (Switch)' },
      { value: 'filter', label: 'Фильтр' }
    ]
  },
  ACTION: {
    type: 'action',
    label: '⚙️ Действие',
    color: '#3b82f6',
    options: [
      { value: 'telegram_send', label: 'Отправить в Telegram' },
      { value: 'bitrix_create', label: 'Создать задачу Bitrix24' },
      { value: 'log_create', label: 'Записать в Logs' },
      { value: 'ai_call', label: 'AI звонок' },
      { value: 'email_send', label: 'Отправить Email' },
      { value: 'http_request', label: 'HTTP запрос' }
    ]
  },
  DATA: {
    type: 'data',
    label: '💾 Данные',
    color: '#8b5cf6',
    options: [
      { value: 'get_houses', label: 'Получить дома' },
      { value: 'get_tasks', label: 'Получить задачи' },
      { value: 'get_users', label: 'Получить пользователей' },
      { value: 'variable', label: 'Переменная' }
    ]
  }
};

const FunctionStudio = () => {
  // Начальные узлы для примера
  const initialNodes = [
    {
      id: 'welcome',
      type: 'default',
      position: { x: 250, y: 100 },
      data: {
        label: '🚀 Добро пожаловать в Function Studio!'
      },
      style: {
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        border: '2px solid white',
        borderRadius: '15px',
        padding: '20px',
        fontWeight: 'bold',
        fontSize: '16px',
        boxShadow: '0 8px 20px rgba(102, 126, 234, 0.3)',
        minWidth: '300px',
        textAlign: 'center'
      }
    },
    {
      id: 'info',
      type: 'default',
      position: { x: 200, y: 250 },
      data: {
        label: '👈 Добавляйте узлы слева\n🔗 Соединяйте их для создания автоматизаций'
      },
      style: {
        background: '#f3f4f6',
        color: '#1f2937',
        border: '2px dashed #9ca3af',
        borderRadius: '10px',
        padding: '15px',
        fontSize: '14px',
        minWidth: '350px',
        textAlign: 'center',
        whiteSpace: 'pre-line'
      }
    }
  ];

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [workflowName, setWorkflowName] = useState('Новая автоматизация');

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Добавление нового узла
  const addNode = (nodeType) => {
    const typeConfig = NODE_TYPES[nodeType];
    const newNode = {
      id: `${nodeType.toLowerCase()}-${Date.now()}`,
      type: 'default',
      position: { x: Math.random() * 400, y: Math.random() * 300 },
      data: {
        label: typeConfig.label,
        nodeType: nodeType,
        config: {
          type: typeConfig.type,
          selectedOption: typeConfig.options?.[0]?.value || '',
          params: {}
        }
      },
      style: {
        background: typeConfig.color,
        color: 'white',
        border: '2px solid white',
        borderRadius: '10px',
        padding: '10px',
        fontWeight: 'bold',
        boxShadow: '0 4px 10px rgba(0,0,0,0.2)'
      }
    };

    setNodes((nds) => [...nds, newNode]);
  };

  // Сохранение workflow
  const saveWorkflow = async () => {
    const workflow = {
      name: workflowName,
      nodes,
      edges,
      version: 1,
      created_at: new Date().toISOString()
    };

    try {
      const res = await fetch(`${BACKEND_URL}/api/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflow)
      });

      if (res.ok) {
        alert('✅ Автоматизация сохранена!');
      } else {
        alert('❌ Ошибка сохранения');
      }
    } catch (e) {
      alert('❌ Ошибка подключения к серверу');
    }
  };

  // Запуск workflow (тест)
  const runWorkflow = async () => {
    if (nodes.length === 0) {
      alert('⚠️ Добавьте хотя бы один узел');
      return;
    }

    alert('🚀 Запуск автоматизации... (в разработке)');
  };

  return (
    <div className="function-studio-container">
      <div className="function-studio-header">
        <div className="header-left">
          <h1 className="studio-title">🔧 Function Studio</h1>
          <input
            type="text"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="workflow-name-input"
            placeholder="Название автоматизации"
          />
        </div>
        <div className="header-right">
          <button onClick={saveWorkflow} className="btn btn-save">
            💾 Сохранить
          </button>
          <button onClick={runWorkflow} className="btn btn-run">
            ▶️ Запустить
          </button>
        </div>
      </div>

      <div className="function-studio-body">
        {/* Панель инструментов */}
        <div className="tools-panel">
          <h3 className="tools-title">Инструменты</h3>
          
          <div className="tool-section">
            <h4 className="tool-section-title">Триггеры</h4>
            <button
              onClick={() => addNode('TRIGGER')}
              className="tool-btn"
              style={{ background: NODE_TYPES.TRIGGER.color }}
            >
              {NODE_TYPES.TRIGGER.label}
            </button>
          </div>

          <div className="tool-section">
            <h4 className="tool-section-title">Условия</h4>
            <button
              onClick={() => addNode('CONDITION')}
              className="tool-btn"
              style={{ background: NODE_TYPES.CONDITION.color }}
            >
              {NODE_TYPES.CONDITION.label}
            </button>
          </div>

          <div className="tool-section">
            <h4 className="tool-section-title">Действия</h4>
            <button
              onClick={() => addNode('ACTION')}
              className="tool-btn"
              style={{ background: NODE_TYPES.ACTION.color }}
            >
              {NODE_TYPES.ACTION.label}
            </button>
          </div>

          <div className="tool-section">
            <h4 className="tool-section-title">Данные</h4>
            <button
              onClick={() => addNode('DATA')}
              className="tool-btn"
              style={{ background: NODE_TYPES.DATA.color }}
            >
              {NODE_TYPES.DATA.label}
            </button>
          </div>
        </div>

        {/* Canvas React Flow */}
        <div className="flow-canvas">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(e, node) => setSelectedNode(node)}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>

        {/* Панель настроек */}
        <div className="config-panel">
          <h3 className="config-title">Настройки узла</h3>
          {selectedNode ? (
            <div className="config-content">
              <p><strong>ID:</strong> {selectedNode.id}</p>
              <p><strong>Тип:</strong> {selectedNode.data.nodeType}</p>
              
              <div className="config-field">
                <label>Действие:</label>
                <select className="config-select">
                  {NODE_TYPES[selectedNode.data.nodeType]?.options?.map(opt => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="config-field">
                <label>Параметры:</label>
                <textarea
                  className="config-textarea"
                  placeholder='{"key": "value"}'
                  rows="5"
                />
              </div>

              <button className="btn btn-delete">
                🗑️ Удалить узел
              </button>
            </div>
          ) : (
            <div className="config-empty">
              <p>Выберите узел для настройки</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FunctionStudio;
