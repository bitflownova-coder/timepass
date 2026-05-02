import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { X, AlertTriangle, CheckCircle, Info, AlertOctagon, Bell } from 'lucide-react';
import { cn } from '@/lib/utils';

type ToastType = 'info' | 'success' | 'warning' | 'error';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  timestamp: number;
  duration?: number; // ms, 0 = persistent
}

interface NotificationContextValue {
  toasts: Toast[];
  addToast: (type: ToastType, title: string, message?: string, duration?: number) => void;
  removeToast: (id: string) => void;
  clearAll: () => void;
  history: Toast[];
}

const NotificationContext = createContext<NotificationContextValue>({
  toasts: [],
  addToast: () => {},
  removeToast: () => {},
  clearAll: () => {},
  history: [],
});

export function useNotifications() {
  return useContext(NotificationContext);
}

let toastCounter = 0;

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [history, setHistory] = useState<Toast[]>([]);
  const timersRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  const addToast = useCallback(
    (type: ToastType, title: string, message?: string, duration = 5000) => {
      const id = `toast-${++toastCounter}`;
      const toast: Toast = { id, type, title, message, timestamp: Date.now(), duration };

      setToasts((prev) => [...prev.slice(-9), toast]); // Max 10 visible
      setHistory((prev) => [...prev.slice(-99), toast]); // Keep last 100

      if (duration > 0) {
        const timer = setTimeout(() => removeToast(id), duration);
        timersRef.current.set(id, timer);
      }
    },
    [removeToast]
  );

  const clearAll = useCallback(() => {
    timersRef.current.forEach((timer) => clearTimeout(timer));
    timersRef.current.clear();
    setToasts([]);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => clearTimeout(timer));
    };
  }, []);

  return (
    <NotificationContext.Provider value={{ toasts, addToast, removeToast, clearAll, history }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </NotificationContext.Provider>
  );
}

// ===== Toast Display =====

const typeConfig: Record<ToastType, { icon: React.ElementType; accent: string; bg: string; border: string }> = {
  info: { icon: Info, accent: 'text-brand-400', bg: 'bg-brand-600/10', border: 'border-brand-600/30' },
  success: { icon: CheckCircle, accent: 'text-accent-green', bg: 'bg-accent-green/10', border: 'border-accent-green/30' },
  warning: { icon: AlertTriangle, accent: 'text-accent-amber', bg: 'bg-accent-amber/10', border: 'border-accent-amber/30' },
  error: { icon: AlertOctagon, accent: 'text-accent-red', bg: 'bg-accent-red/10', border: 'border-accent-red/30' },
};

function ToastContainer({ toasts, onRemove }: { toasts: Toast[]; onRemove: (id: string) => void }) {
  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={() => onRemove(toast.id)} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const config = typeConfig[toast.type];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'pointer-events-auto flex items-start gap-3 p-3 rounded-xl border shadow-lg backdrop-blur-sm animate-slide-up',
        config.bg,
        config.border,
        'bg-surface-2/95'
      )}
    >
      <Icon className={cn('w-4 h-4 mt-0.5 flex-shrink-0', config.accent)} />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-gray-200">{toast.title}</p>
        {toast.message && (
          <p className="text-[11px] text-gray-500 mt-0.5 line-clamp-2">{toast.message}</p>
        )}
      </div>
      <button
        onClick={onClose}
        className="flex-shrink-0 p-0.5 rounded hover:bg-surface-4 text-gray-600 hover:text-gray-300 transition-colors"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
