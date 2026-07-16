import React from 'react';

interface LoaderProps {
  type?: 'spinner' | 'pulse' | 'skeleton';
  text?: string;
  className?: string;
}

export const Loader: React.FC<LoaderProps> = ({
  type = 'spinner',
  text = 'Loading...',
  className = '',
}) => {
  if (type === 'spinner') {
    return (
      <div className={`flex flex-col items-center justify-center space-y-3 p-6 ${className}`}>
        <div className="w-8 h-8 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
        {text && <p className="text-xs text-slate-400 font-medium tracking-wide">{text}</p>}
      </div>
    );
  }

  if (type === 'pulse') {
    return (
      <div className={`flex items-center space-x-2 p-4 justify-center ${className}`}>
        <div className="w-2.5 h-2.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
        <div className="w-2.5 h-2.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
        <div className="w-2.5 h-2.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 p-4 animate-pulse ${className}`}>
      <div className="h-4 bg-slate-800 rounded-lg w-2/3"></div>
      <div className="h-3 bg-slate-800 rounded-lg w-full"></div>
      <div className="h-3 bg-slate-800 rounded-lg w-5/6"></div>
    </div>
  );
};

export default Loader;
