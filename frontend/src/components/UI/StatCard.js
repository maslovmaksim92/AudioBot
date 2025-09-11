import React from 'react';

const StatCard = ({ title, value, icon, color = 'blue', subtitle, trend }) => {
  const colorClasses = {
    blue: 'from-blue-50 to-blue-100 border-blue-200 text-blue-600',
    green: 'from-green-50 to-green-100 border-green-200 text-green-600',
    purple: 'from-purple-50 to-purple-100 border-purple-200 text-purple-600',
    yellow: 'from-yellow-50 to-yellow-100 border-yellow-200 text-yellow-600',
    red: 'from-red-50 to-red-100 border-red-200 text-red-600',
    gray: 'from-gray-50 to-gray-100 border-gray-200 text-gray-600'
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} border rounded-lg p-6 shadow-sm`}>
      <div className="flex items-center">
        <div className="flex-shrink-0">
          {icon}
        </div>
        <div className="ml-5 w-0 flex-1">
          <dl>
            <dt className="text-sm font-medium text-gray-500 truncate">
              {title}
            </dt>
            <dd className="flex items-baseline">
              <div className="text-2xl font-semibold text-gray-900">
                {typeof value === 'number' ? value.toLocaleString('ru-RU') : value}
              </div>
              {trend && (
                <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                  trend.direction === 'up' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {trend.direction === 'up' ? '↗' : '↘'}
                  {trend.value}
                </div>
              )}
            </dd>
            {subtitle && (
              <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
            )}
          </dl>
        </div>
      </div>
    </div>
  );
};

export default StatCard;