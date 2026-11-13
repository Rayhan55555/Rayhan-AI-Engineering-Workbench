import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  href?: string;
  external?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  href,
  external,
  className = '',
  children,
  ...props
}) => {
  const baseClasses =
    'inline-flex items-center justify-center font-medium transition-all duration-150 rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#00D4FF] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0A0F1E] disabled:opacity-50 disabled:pointer-events-none whitespace-nowrap shrink-0';

  const sizeClasses = {
    sm: 'text-xs px-3 py-1.5 gap-1.5 font-mono',
    md: 'text-sm px-4 py-2 gap-2 font-sans',
    lg: 'text-sm sm:text-base px-6 py-2.5 gap-2.5 font-sans font-semibold',
  };

  const variantClasses = {
    primary:
      'bg-[#00D4FF] text-[#0A0F1E] hover:bg-[#38bdf8] shadow-[0_0_15px_rgba(0,212,255,0.25)] hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] font-semibold',
    secondary:
      'bg-[#162036] text-slate-100 hover:bg-[#1E293B] border border-slate-700/80 hover:border-slate-600',
    outline:
      'bg-transparent text-slate-200 hover:text-white border border-slate-700 hover:border-[#00D4FF] hover:bg-[#00D4FF]/5',
    ghost:
      'bg-transparent text-slate-400 hover:text-slate-100 hover:bg-slate-800/60',
  };

  const combinedClasses = `${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`;

  if (href) {
    return (
      <a
        href={href}
        target={external ? '_blank' : undefined}
        rel={external ? 'noopener noreferrer' : undefined}
        className={combinedClasses}
      >
        {children}
      </a>
    );
  }

  return (
    <button className={combinedClasses} {...props}>
      {children}
    </button>
  );
};
