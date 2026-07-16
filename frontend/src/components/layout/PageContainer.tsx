import { ReactNode } from 'react';

interface ContainerProps {
  children: ReactNode;
  className?: string;
}

export const PageContainer = ({ children, className = '' }: ContainerProps) => {
  return (
    <div className={`max-w-7xl mx-auto space-y-6 animate-fade-in ${className}`}>
      {children}
    </div>
  );
};

interface HeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export const PageHeader = ({ title, subtitle, actions }: HeaderProps) => {
  return (
    <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-6 border-b border-slate-800 space-y-4 md:space-y-0">
      <div className="space-y-1">
        <h1 className="text-3xl font-extrabold tracking-tight text-white">{title}</h1>
        {subtitle && <p className="text-sm text-slate-400 font-medium">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center space-x-3">{actions}</div>}
    </div>
  );
};

interface ActionBarProps {
  children: ReactNode;
  className?: string;
}

export const ActionBar = ({ children, className = '' }: ActionBarProps) => {
  return (
    <div className={`bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 flex items-center justify-between space-x-4 ${className}`}>
      {children}
    </div>
  );
};

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
  icon?: ReactNode;
  className?: string;
}

export const EmptyState = ({
  title,
  description,
  action,
  icon,
  className = '',
}: EmptyStateProps) => {
  return (
    <div className={`bg-slate-900 border border-slate-800 border-dashed rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4 ${className}`}>
      {icon ? (
        <div className="text-slate-500">{icon}</div>
      ) : (
        <div className="w-12 h-12 bg-slate-800 rounded-xl flex items-center justify-center text-slate-400">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
        </div>
      )}
      <div className="space-y-1">
        <h3 className="font-bold text-slate-200 tracking-tight">{title}</h3>
        <p className="text-xs text-slate-400 font-medium max-w-sm">{description}</p>
      </div>
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
};
