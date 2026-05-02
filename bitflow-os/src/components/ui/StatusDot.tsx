import React from 'react';
import { cn } from '@/lib/utils';

interface StatusDotProps {
  status: 'running' | 'starting' | 'stopped' | 'error' | 'disabled' | string;
  size?: 'sm' | 'md' | 'lg';
  label?: string;
}

export function StatusDot({ status, size = 'md', label }: StatusDotProps) {
  const colorMap: Record<string, string> = {
    running: 'bg-accent-green',
    starting: 'bg-accent-amber status-pulse',
    stopped: 'bg-gray-600',
    error: 'bg-accent-red',
    disabled: 'bg-gray-700',
  };

  const sizeMap = { sm: 'w-2 h-2', md: 'w-2.5 h-2.5', lg: 'w-3 h-3' };

  return (
    <div className="flex items-center gap-2">
      <div className={cn('rounded-full', sizeMap[size], colorMap[status] || 'bg-gray-600')} />
      {label && <span className="text-xs text-gray-400">{label}</span>}
    </div>
  );
}

interface ServiceHealthRowProps {
  services: ServiceStatus[];
  onRestart?: (id: string) => void;
}

export function ServiceHealthRow({ services, onRestart }: ServiceHealthRowProps) {
  return (
    <div className="flex items-center gap-6">
      {services.map((service) => (
        <div
          key={service.id}
          className="flex items-center gap-2 bg-surface-2 border border-surface-4 rounded-lg px-3 py-2"
        >
          <StatusDot status={service.status} />
          <div>
            <p className="text-xs font-medium text-gray-300">{service.name}</p>
            <p className="text-[10px] text-gray-600">
              {service.status === 'running' ? `:${service.port}` : service.status}
            </p>
          </div>
          {onRestart && service.status !== 'disabled' && (
            <button
              onClick={() => onRestart(service.id)}
              className="ml-2 text-[10px] text-gray-600 hover:text-brand-400 transition-colors"
              title="Restart"
            >
              ↻
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
