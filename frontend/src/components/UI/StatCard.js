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
    &lt;Card 
      className={`${cardClasses} ${className}`}
      onClick={onClick}
      padding="default"
      shadow="sm"
    &gt;
      &lt;div className="flex items-center justify-between"&gt;
        &lt;div className="flex-1"&gt;
          &lt;p className="text-sm font-medium text-gray-600"&gt;{title}&lt;/p&gt;
          &lt;p className="text-2xl font-bold text-gray-900 mt-1"&gt;
            {typeof value === 'number' ? value.toLocaleString() : value}
          &lt;/p&gt;
          {subtitle && (
            &lt;p className="text-xs text-gray-500 mt-1"&gt;{subtitle}&lt;/p&gt;
          )}
          {trend && trendDirection && (
            &lt;div className={`flex items-center mt-2 text-sm ${trendColors[trendDirection]}`}&gt;
              &lt;span&gt;{trend}&lt;/span&gt;
              {trendDirection === 'up' && &lt;span className="ml-1"&gt;↗&lt;/span&gt;}
              {trendDirection === 'down' && &lt;span className="ml-1"&gt;↘&lt;/span&gt;}
              {trendDirection === 'neutral' && &lt;span className="ml-1"&gt;→&lt;/span&gt;}
            &lt;/div&gt;
          )}
        &lt;/div&gt;
        {icon && (
          &lt;div className={`p-3 rounded-full ${colors[color]}`}&gt;
            {icon}
          &lt;/div&gt;
        )}
      &lt;/div&gt;
    &lt;/Card&gt;
  );
};

export default StatCard;