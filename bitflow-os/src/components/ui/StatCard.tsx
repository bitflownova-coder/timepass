import React from 'react';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color: string; // tailwind color class prefix like 'brand' or 'accent-green'
  trend?: { value: number; label: string };
}

export function StatCard({ title, value, subtitle, icon: Icon, color, trend }: StatCardProps) {
  return (
    <div className="bg-surface-2 border border-surface-4 rounded-xl p-4 flex items-start gap-4">
      <div className={cn('p-2.5 rounded-lg bg-opacity-15', `bg-${color}/15`)}>
        <Icon className={cn('w-5 h-5', `text-${color}`)} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-white mt-0.5">{value}</p>
        {subtitle && <p className="text-[11px] text-gray-600 mt-1">{subtitle}</p>}
        {trend && (
          <p className={cn('text-[11px] mt-1', trend.value >= 0 ? 'text-accent-green' : 'text-accent-red')}>
            {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}% {trend.label}
          </p>
        )}
      </div>
    </div>
  );
}
