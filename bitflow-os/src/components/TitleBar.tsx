import React from 'react';
import { Minus, Square, X } from 'lucide-react';

interface TitleBarProps {
  serviceStatuses: ServiceStatus[];
}

export default function TitleBar({ serviceStatuses }: TitleBarProps) {
  const getStatusDot = (status: string) => {
    switch (status) {
      case 'running': return 'bg-accent-green';
      case 'starting': return 'bg-accent-amber status-pulse';
      case 'error': return 'bg-accent-red';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div className="h-9 bg-surface-0 border-b border-surface-3 flex items-center justify-between px-3 drag-region select-none">
      {/* Left: App name */}
      <div className="flex items-center gap-3 no-drag">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-brand-600 flex items-center justify-center text-[10px] font-bold">
            B
          </div>
          <span className="text-sm font-semibold text-gray-300">Bitflow AI OS</span>
        </div>
      </div>

      {/* Center: Service status indicators */}
      <div className="flex items-center gap-4">
        {serviceStatuses.map((s) => (
          <div key={s.id} className="flex items-center gap-1.5 no-drag" title={`${s.name}: ${s.status}`}>
            <div className={`w-2 h-2 rounded-full ${getStatusDot(s.status)}`} />
            <span className="text-[11px] text-gray-500">{s.name}</span>
          </div>
        ))}
      </div>

      {/* Right: Window controls */}
      <div className="flex items-center no-drag">
        <button
          onClick={() => window.electronAPI?.minimize()}
          className="p-2 hover:bg-surface-3 rounded transition-colors"
        >
          <Minus className="w-3.5 h-3.5 text-gray-400" />
        </button>
        <button
          onClick={() => window.electronAPI?.maximize()}
          className="p-2 hover:bg-surface-3 rounded transition-colors"
        >
          <Square className="w-3 h-3 text-gray-400" />
        </button>
        <button
          onClick={() => window.electronAPI?.close()}
          className="p-2 hover:bg-accent-red rounded transition-colors group"
        >
          <X className="w-3.5 h-3.5 text-gray-400 group-hover:text-white" />
        </button>
      </div>
    </div>
  );
}
