import React from 'react';

const LoadingSpinner = ({ size = 'md', className = '', text = '' }) => {
  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8', 
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  };

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <svg 
        className={`animate-spin ${sizes[size]} text-blue-600`} 
        fill="none" 
        viewBox="0 0 24 24"
      >
        <circle 
          className="opacity-25" 
          cx="12" 
          cy="12" 
          r="10" 
          stroke="currentColor" 
          strokeWidth="4"
        ></circle>
        <path 
          className="opacity-75" 
          fill="currentColor" 
          d="m12 2v3m0 16v-3m10-8h-3M5 12H2m17.07-5.07l-2.12 2.12M9.05 14.95l-2.12 2.12m12.02 0l-2.12-2.12M9.05 9.05L6.93 6.93"
        ></path>
      </svg>
      {text && <p className="mt-2 text-sm text-gray-600">{text}</p>}
    </div>
  );
};

export default LoadingSpinner;