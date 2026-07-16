import React, { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  className?: string;
  isHoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  actions,
  className = '',
  isHoverable = false,
}) => {
  return (
    <div
      className={`bg-slate-900 border border-slate-800 rounded-2xl p-6 transition duration-150 ${
        isHoverable ? 'hover:border-slate-700 hover:shadow-xl hover:shadow-slate-950/20' : ''
      } ${className}`}
    >
      {(title || subtitle || actions) && (
        <div className="flex items-center justify-between mb-4 pb-4 border-b border-slate-800/60">
          <div className="space-y-1">
            {title && typeof title === 'string' ? (
              <h3 className="font-bold text-slate-100 tracking-tight">{title}</h3>
            ) : (
              title
            )}
            {subtitle && typeof subtitle === 'string' ? (
              <p className="text-xs text-slate-400 font-medium">{subtitle}</p>
            ) : (
              subtitle
            )}
          </div>
          {actions && <div className="flex items-center space-x-2">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
};

export default Card;
