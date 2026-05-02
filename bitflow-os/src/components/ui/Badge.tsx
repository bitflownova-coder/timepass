import React from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
  className?: string;
}

const variantClasses: Record<string, string> = {
  default: 'bg-surface-4 text-gray-400',
  success: 'bg-accent-green/15 text-accent-green border border-accent-green/30',
  warning: 'bg-accent-amber/15 text-accent-amber border border-accent-amber/30',
  danger: 'bg-accent-red/15 text-accent-red border border-accent-red/30',
  info: 'bg-brand-500/15 text-brand-400 border border-brand-500/30',
  purple: 'bg-accent-purple/15 text-accent-purple border border-accent-purple/30',
};

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold',
        variantClasses[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
