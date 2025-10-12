import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  addEdge,
  useEdgesState,
  useNodesState,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './MindMap.css';
import dagre from 'dagre';

const initialNodes = [
  { id: 'root', position: { x: 0, y: 0 }, data: { label: 'Центральная идея', color: 'blue', icon: '💡' }, style: { width: 200 } },
];

const NODE_WIDTH = 200;
const NODE_HEIGHT = 60;

function getLayoutedElements(nodes, edges, direction = 'LR') {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: direction });
  g.setDefaultEdgeLabel(() => ({}));
  nodes.forEach((node) => g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT }));
  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  dagre.layout(g);
  return nodes.map((node) => {
    const n = g.node(node.id);
    return { ...node, position: { x: n.x - NODE_WIDTH / 2, y: n.y - NODE_HEIGHT / 2 } };
  });
}

const MindMap = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const idRef = useRef(1);
  const [direction, setDirection] = useState('LR');

  const onConnect = useCallback((params) => setEdges((eds) => addEdge({ ...params, markerEnd: { type: MarkerType.ArrowClosed } }, eds)), [setEdges]);

  const addChild = useCallback((parentId) => {
    const id = String(++idRef.current);
    const parent = nodes.find(n => n.id === parentId);
    const newNode = { id, position: { x: 0, y: 0 }, data: { label: 'Новый узел', color: 'green', icon: '🧩' }, style: { width: NODE_WIDTH } };
    const nextNodes = [...nodes, newNode];
    const nextEdges = [...edges, { id: `e-${parentId}-${id}`, source: parentId, target: id, markerEnd: { type: MarkerType.ArrowClosed } }];
    const layouted = getLayoutedElements(nextNodes, nextEdges, direction);
    setNodes(layouted);
    setEdges(nextEdges);
  }, [nodes, edges, setNodes, setEdges, direction]);

  const removeNode = useCallback((id) => {
    const nextNodes = nodes.filter(n => n.id !== id);
    const nextEdges = edges.filter(e => e.source !== id && e.target !== id);
    const layouted = getLayoutedElements(nextNodes, nextEdges, direction);
    setNodes(layouted);
    setEdges(nextEdges);
  }, [nodes, edges, setNodes, setEdges, direction]);

  const onNodeDoubleClick = useCallback((_, node) => {
    const label = window.prompt('Название узла', node?.data?.label || '');
    if (label != null) {
      setNodes(nds => nds.map(n => n.id === node.id ? { ...n, data: { ...n.data, label } } : n));
    }
  }, [setNodes]);

  const changeColor = useCallback((nodeId, color) => {
    setNodes(nds => nds.map(n => n.id === nodeId ? { ...n, data: { ...n.data, color } } : n));
  }, []);

  const changeIcon = useCallback((nodeId) => {
    const icon = window.prompt('Иконка (эмодзи)', '✅');
    if (icon != null) setNodes(nds => nds.map(n => n.id === nodeId ? { ...n, data: { ...n.data, icon } } : n));
  }, []);

  const exportJson = () => {
    const data = JSON.stringify({ nodes, edges }, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mindmap.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const importJson = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        if (Array.isArray(data.nodes) && Array.isArray(data.edges)) {
          setNodes(getLayoutedElements(data.nodes, data.edges, direction));
          setEdges(data.edges);
        } else {
          alert('Неверный формат файла');
        }
      } catch (err) {
        alert('Ошибка чтения файла');
      }
    };
    reader.readAsText(file);
  };

  const NodeToolbar = ({ node }) => (
    <div className="toolbar flex gap-2 text-xs mt-1">
      <button onClick={() => addChild(node.id)} className="px-2 py-1 bg-blue-50 border rounded">+ Узел</button>
      {node.id !== 'root' && (
        <button onClick={() => removeNode(node.id)} className="px-2 py-1 bg-red-50 border rounded">Удалить</button>
      )}
      <select className="border rounded px-1" value={node.data.color||'blue'} onChange={e=>changeColor(node.id, e.target.value)}>
        <option value="blue">Синий</option>
        <option value="green">Зелёный</option>
        <option value="yellow">Жёлтый</option>
        <option value="red">Красный</option>
        <option value="purple">Фиолетовый</option>
      </select>
      <button onClick={() => changeIcon(node.id)} className="px-2 py-1 bg-white border rounded">Иконка</button>
    </div>
  );

  const nodeTypes = useMemo(() => ({
    default: (props) => (
      <div className={`mindmap-node color-${props.data.color||'blue'}`} onDoubleClick={(e)=>onNodeDoubleClick(e, props)}>
        <div className="title">
          <span className="mr-1">{props.data.icon||'🧠'}</span>
          {props.data.label}
        </div>
        {props.data.subtitle && <div className="subtitle">{props.data.subtitle}</div>}
        <NodeToolbar node={props} />
      </div>
    )
  }), [onNodeDoubleClick, addChild, removeNode, changeColor, changeIcon]);

  const autoLayout = useCallback((dir) => {
    setNodes(nds => getLayoutedElements(nds, edges, dir));
    setDirection(dir);
  }, [edges]);

  const templates = [
    { id: 'flow', name: 'Поток (3 шага)', build: () => {
      const base = [
        { id: 'root', position: { x: 0, y: 0 }, data: { label: 'Старт', color: 'blue', icon: '🚀' }, style: { width: NODE_WIDTH } },
        { id: '1', position: { x: 0, y: 0 }, data: { label: 'Шаг 1', color: 'green', icon: '🧩' }, style: { width: NODE_WIDTH } },
        { id: '2', position: { x: 0, y: 0 }, data: { label: 'Шаг 2', color: 'yellow', icon: '⚙️' }, style: { width: NODE_WIDTH } },
        { id: '3', position: { x: 0, y: 0 }, data: { label: 'Готово', color: 'purple', icon: '✅' }, style: { width: NODE_WIDTH } },
      ];
      const baseEdges = [
        { id: 'e-root-1', source: 'root', target: '1' },
        { id: 'e-1-2', source: '1', target: '2' },
        { id: 'e-2-3', source: '2', target: '3' },
      ];
      idRef.current = 3;
      setEdges(baseEdges.map(e => ({ ...e, markerEnd: { type: MarkerType.ArrowClosed } })));
      setNodes(getLayoutedElements(base, baseEdges, direction));
    }},
    { id: 'tree', name: 'Дерево (root + 3)', build: () => {
      const base = [
        { id: 'root', position: { x: 0, y: 0 }, data: { label: 'Центр', color: 'blue', icon: '🌐' }, style: { width: NODE_WIDTH } },
        { id: 'a', position: { x: 0, y: 0 }, data: { label: 'Ветка A', color: 'green', icon: '🧩' }, style: { width: NODE_WIDTH } },
        { id: 'b', position: { x: 0, y: 0 }, data: { label: 'Ветка B', color: 'yellow', icon: '⚙️' }, style: { width: NODE_WIDTH } },
        { id: 'c', position: { x: 0, y: 0 }, data: { label: 'Ветка C', color: 'purple', icon: '✅' }, style: { width: NODE_WIDTH } },
      ];
      const baseEdges = [
        { id: 'e-root-a', source: 'root', target: 'a' },
        { id: 'e-root-b', source: 'root', target: 'b' },
        { id: 'e-root-c', source: 'root', target: 'c' },
      ];
      idRef.current = 3;
      setEdges(baseEdges.map(e => ({ ...e, markerEnd: { type: MarkerType.ArrowClosed } })));
      setNodes(getLayoutedElements(base, baseEdges, direction));
    }}];

  // Autosave to localStorage
  useEffect(() => {
    try {
      const data = JSON.stringify({ nodes, edges });
      localStorage.setItem('mindmap_v1', data);
    } catch (e) {}
  }, [nodes, edges]);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem('mindmap_v1');
      if (raw) {
        const data = JSON.parse(raw);
        if (Array.isArray(data.nodes) && Array.isArray(data.edges)) {
          setNodes(getLayoutedElements(data.nodes, data.edges, direction));
          setEdges(data.edges);
          // attempt to continue id sequence
          const maxId = data.nodes
            .map(n => (Number.isFinite(+n.id) ? +n.id : -1))
            .reduce((a,b)=>Math.max(a,b), 0);
          if (maxId > 0) idRef.current = maxId;
        }
      }
    } catch (e) {}
  }, []);

  return (
    <div className="bg-white rounded-xl shadow-elegant">
      <div className="mindmap-toolbar p-2 flex items-center gap-2 flex-wrap">
        <button className="px-3 py-1 bg-white border rounded" onClick={exportJson}>Экспорт JSON</button>
        <label className="px-3 py-1 bg-white border rounded cursor-pointer">
          Импорт JSON
          <input type="file" accept="application/json" className="hidden" onChange={(e)=> e.target.files && importJson(e.target.files[0])} />
        </label>
        <div className="ml-2 flex items-center gap-1">
          <span className="text-xs text-gray-500">Авто‑расстановка:</span>
          <button className="px-2 py-1 bg-white border rounded" onClick={()=>autoLayout('LR')}>Слева→Право</button>
          <button className="px-2 py-1 bg-white border rounded" onClick={()=>autoLayout('TB')}>Сверху→Вниз</button>
        </div>
        <div className="ml-2 flex items-center gap-1">
          <span className="text-xs text-gray-500">Шаблоны:</span>
          {templates.map(t => (
            <button key={t.id} className="px-2 py-1 bg-white border rounded" onClick={t.build}>{t.name}</button>
          ))}
        </div>
      </div>
      <div className="mindmap-wrapper">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        >
          <MiniMap pannable zoomable />
          <Controls showInteractive={false} />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </div>
    </div>
  );
};

export default MindMap;
