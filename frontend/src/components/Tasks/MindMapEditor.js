import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { X, Plus, Save, Download, Upload, Circle, Square, Diamond, Trash2 } from 'lucide-react';
import { taskService } from '../../services/taskService';
import './MindMapEditor.css';

// Кастомные узлы
const MainIdeaNode = ({ data }) => {
  return (
    <div className="mindmap-node main-idea">
      <div className="node-content">
        <div className="node-icon">💡</div>
        <div className="node-text">{data.label}</div>
      </div>
    </div>
  );
};

const SubIdeaNode = ({ data }) => {
  return (
    <div className="mindmap-node sub-idea">
      <div className="node-content">
        <div className="node-icon">🔸</div>
        <div className="node-text">{data.label}</div>
      </div>
    </div>
  );
};

const TaskNode = ({ data }) => {
  return (
    <div className="mindmap-node task-node">
      <div className="node-content">
        <div className="node-icon">✓</div>
        <div className="node-text">{data.label}</div>
      </div>
    </div>
  );
};

const nodeTypes = {
  mainIdea: MainIdeaNode,
  subIdea: SubIdeaNode,
  taskNode: TaskNode,
};

const MindMapEditor = ({ task, onClose, onSave }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNodeType, setSelectedNodeType] = useState('subIdea');
  const [editingNode, setEditingNode] = useState(null);
  const [nodeLabel, setNodeLabel] = useState('');
  const [saving, setSaving] = useState(false);

  // Загрузка существующей mind-map
  useEffect(() => {
    if (task && task.mindmap) {
      const mindmap = task.mindmap;
      if (mindmap.nodes && mindmap.nodes.length > 0) {
        setNodes(mindmap.nodes);
        setEdges(mindmap.edges || []);
      } else {
        initializeDefaultMindmap();
      }
    } else {
      initializeDefaultMindmap();
    }
  }, [task]);

  const initializeDefaultMindmap = () => {
    const mainNode = {
      id: '1',
      type: 'mainIdea',
      position: { x: 400, y: 200 },
      data: { label: task?.title || 'Главная идея' },
    };
    setNodes([mainNode]);
    setEdges([]);
  };

  const onConnect = useCallback((params) => {
    const edge = {
      ...params,
      type: 'smoothstep',
      animated: true,
      markerEnd: {
        type: MarkerType.ArrowClosed,
      },
      style: { stroke: '#3b82f6', strokeWidth: 2 },
    };
    setEdges((eds) => addEdge(edge, eds));
  }, []);

  const addNode = useCallback((type) => {
    const newNode = {
      id: `${Date.now()}`,
      type: type,
      position: { 
        x: Math.random() * 400 + 200, 
        y: Math.random() * 300 + 100 
      },
      data: { label: 'Новая идея' },
    };
    setNodes((nds) => [...nds, newNode]);
  }, []);

  const onNodeDoubleClick = useCallback((event, node) => {
    setEditingNode(node.id);
    setNodeLabel(node.data.label);
  }, []);

  const updateNodeLabel = useCallback(() => {
    if (editingNode && nodeLabel.trim()) {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === editingNode
            ? { ...node, data: { ...node.data, label: nodeLabel } }
            : node
        )
      );
      setEditingNode(null);
      setNodeLabel('');
    }
  }, [editingNode, nodeLabel]);

  const deleteNode = useCallback((nodeId) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const mindmapData = {
        nodes: nodes,
        edges: edges,
      };
      await taskService.updateMindmap(task.id, mindmapData);
      alert('Mind-map сохранена!');
      if (onSave) {
        onSave();
      }
    } catch (error) {
      alert('Ошибка сохранения: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  const exportMindmap = () => {
    const data = { nodes, edges };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mindmap-${task.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const importMindmap = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result);
          setNodes(data.nodes || []);
          setEdges(data.edges || []);
        } catch (error) {
          alert('Ошибка импорта файла');
        }
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="mindmap-editor-container">
      {/* Заголовок */}
      <div className="mindmap-header">
        <div>
          <h2 className="mindmap-title">🧠 Mind-Map редактор</h2>
          <p className="mindmap-subtitle">{task?.title}</p>
        </div>
        <button onClick={onClose} className="close-button">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* React Flow */}
      <div className="mindmap-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeDoubleClick={onNodeDoubleClick}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background color="#e5e7eb" gap={16} />
          <Controls />
          <MiniMap 
            nodeColor={(node) => {
              if (node.type === 'mainIdea') return '#8b5cf6';
              if (node.type === 'subIdea') return '#3b82f6';
              return '#10b981';
            }}
          />

          {/* Панель инструментов */}
          <Panel position="top-left" className="mindmap-toolbar">
            <div className="toolbar-section">
              <h3>Добавить узел:</h3>
              <div className="toolbar-buttons">
                <button
                  onClick={() => addNode('mainIdea')}
                  className="tool-button main"
                  title="Главная идея"
                >
                  <Circle className="w-4 h-4" />
                  Главная
                </button>
                <button
                  onClick={() => addNode('subIdea')}
                  className="tool-button sub"
                  title="Подидея"
                >
                  <Square className="w-4 h-4" />
                  Подидея
                </button>
                <button
                  onClick={() => addNode('taskNode')}
                  className="tool-button task"
                  title="Задача"
                >
                  <Diamond className="w-4 h-4" />
                  Задача
                </button>
              </div>
            </div>

            <div className="toolbar-section">
              <h3>Действия:</h3>
              <div className="toolbar-buttons">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="tool-button save"
                  title="Сохранить"
                >
                  <Save className="w-4 h-4" />
                  {saving ? 'Сохранение...' : 'Сохранить'}
                </button>
                <button
                  onClick={exportMindmap}
                  className="tool-button export"
                  title="Экспорт"
                >
                  <Download className="w-4 h-4" />
                  Экспорт
                </button>
                <label className="tool-button import" title="Импорт">
                  <Upload className="w-4 h-4" />
                  Импорт
                  <input
                    type="file"
                    accept=".json"
                    onChange={importMindmap}
                    className="hidden"
                  />
                </label>
              </div>
            </div>

            <div className="toolbar-info">
              <p>💡 <strong>Двойной клик</strong> - редактировать</p>
              <p>🔗 <strong>Перетащите</strong> от узла - создать связь</p>
              <p>📍 <strong>Перемещайте</strong> узлы drag-and-drop</p>
            </div>
          </Panel>
        </ReactFlow>
      </div>

      {/* Модальное окно редактирования узла */}
      {editingNode && (
        <div className="edit-modal-overlay">
          <div className="edit-modal">
            <h3>Редактировать узел</h3>
            <input
              type="text"
              value={nodeLabel}
              onChange={(e) => setNodeLabel(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && updateNodeLabel()}
              className="edit-input"
              autoFocus
            />
            <div className="edit-buttons">
              <button onClick={() => setEditingNode(null)} className="cancel-btn">
                Отмена
              </button>
              <button onClick={() => deleteNode(editingNode)} className="delete-btn">
                <Trash2 className="w-4 h-4" />
                Удалить
              </button>
              <button onClick={updateNodeLabel} className="save-btn">
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MindMapEditor;