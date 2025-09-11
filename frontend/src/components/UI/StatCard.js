import React from 'react';
import Card from './Card';

const StatCard = ({ 
  title, 
  value, 
  icon, 
  color = 'blue',
  trend,
  trendDirection,
  subtitle,
  onClick,
  className = ''
}) => {
  const colors = {
    blue: 'text-blue-600 bg-blue-50',
    green: 'text-green-600 bg-green-50', 
    yellow: 'text-yellow-600 bg-yellow-50',
    red: 'text-red-600 bg-red-50',
    purple: 'text-purple-600 bg-purple-50',
    gray: 'text-gray-600 bg-gray-50'
  };

  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600'
  };

  const cardClasses = onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : '';

  return (
    <Card 
      className={`${cardClasses} ${className}`}
      onClick={onClick}
      padding="default"
      shadow="sm"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
          {trend && trendDirection && (
            <div className={`flex items-center mt-2 text-sm ${trendColors[trendDirection]}`}>
              <span>{trend}</span>
              {trendDirection === 'up' && <span className="ml-1">↗</span>}
              {trendDirection === 'down' && <span className="ml-1">↘</span>}
              {trendDirection === 'neutral' && <span className="ml-1">→</span>}
            </div>
          )}
        </div>
        {icon && (
          <div className={`p-3 rounded-full ${colors[color]}`}>
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
};

export default StatCard;