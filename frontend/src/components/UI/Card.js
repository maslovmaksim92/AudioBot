import React from 'react';

const Card = ({ 
  children, 
  className = '', 
  title,
  subtitle,
  padding = 'default',
  shadow = 'default',
  ...props 
}) => {
  const baseClasses = 'bg-white rounded-lg border border-gray-200';
  
  const paddings = {
    none: '',
    sm: 'p-3',
    default: 'p-6',
    lg: 'p-8'
  };

  const shadows = {
    none: '',
    sm: 'shadow-sm',
    default: 'shadow',
    lg: 'shadow-lg'
  };

  const classes = `${baseClasses} ${paddings[padding]} ${shadows[shadow]} ${className}`;

  return (
    &lt;div className={classes} {...props}&gt;
      {(title || subtitle) && (
        &lt;div className="mb-4"&gt;
          {title && &lt;h3 className="text-lg font-semibold text-gray-900"&gt;{title}&lt;/h3&gt;}
          {subtitle && &lt;p className="text-sm text-gray-600 mt-1"&gt;{subtitle}&lt;/p&gt;}
        &lt;/div&gt;
      )}
      {children}
    &lt;/div&gt;
  );
};

export default Card;