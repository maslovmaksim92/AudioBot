import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line } from 'recharts';

// Круговая диаграмма - дома по бригадам
export const BrigadesPieChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        Нет данных для отображения
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({label, value}) => `${label}: ${value}`}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};

// Линейный график - уборки по месяцам
export const CleaningLineChart = ({ data }) => {
  if (!data || !data.months) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        Нет данных для отображения
      </div>
    );
  }

  const chartData = data.months.map((month, idx) => ({
    name: month,
    Запланировано: data.planned[idx],
    Выполнено: data.completed[idx]
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="Запланировано" stroke="#3B82F6" strokeWidth={2} />
        <Line type="monotone" dataKey="Выполнено" stroke="#10B981" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
};

// Прогресс-бар для задач
export const TaskProgressBar = ({ completed, total }) => {
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
  
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">Выполнено</span>
        <span className="font-semibold text-gray-900">{completed} / {total}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div 
          className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="text-right text-xs text-gray-500">{percentage}%</div>
    </div>
  );
};
