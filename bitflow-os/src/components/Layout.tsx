import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TitleBar from './TitleBar';

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const [serviceStatuses, setServiceStatuses] = useState<ServiceStatus[]>([]);

  useEffect(() => {
    // Fetch initial service statuses
    window.electronAPI?.getServiceStatuses?.().then(setServiceStatuses).catch(() => {});

    // Listen for real-time status updates
    const unsub = window.electronAPI?.onServiceStatus?.((statuses) => {
      setServiceStatuses(statuses);
    });
    return () => unsub?.();
  }, []);

  return (
    <div className="h-screen flex flex-col bg-surface-0 overflow-hidden">
      <TitleBar serviceStatuses={serviceStatuses} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
        <main className="flex-1 overflow-y-auto bg-surface-1">
          <div className="p-6 page-enter">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
