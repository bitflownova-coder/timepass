import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import AIIntelligence from './pages/AIIntelligence';
import CodeHealth from './pages/CodeHealth';
import WebCrawler from './pages/WebCrawler';
import { LoadingState } from './components/ui/States';

const DevTools = lazy(() => import('./pages/DevTools'));
const Settings = lazy(() => import('./pages/Settings'));
const DeviceMonitor = lazy(() => import('./pages/DeviceMonitor'));
const Business = lazy(() => import('./pages/Business'));
const Meetings = lazy(() => import('./pages/Meetings'));
const Infrastructure = lazy(() => import('./pages/Infrastructure'));

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="ai-intelligence" element={<AIIntelligence />} />
        <Route path="code-health" element={<CodeHealth />} />
        <Route path="web-crawler" element={<WebCrawler />} />
        <Route path="dev-tools" element={<Suspense fallback={<LoadingState message="Loading Dev Tools..." />}><DevTools /></Suspense>} />
        <Route path="settings" element={<Suspense fallback={<LoadingState message="Loading Settings..." />}><Settings /></Suspense>} />
        <Route path="device-monitor" element={<Suspense fallback={<LoadingState message="Loading Device Monitor..." />}><DeviceMonitor /></Suspense>} />
        <Route path="business" element={<Suspense fallback={<LoadingState message="Loading Business..." />}><Business /></Suspense>} />
        <Route path="meetings" element={<Suspense fallback={<LoadingState message="Loading Meetings..." />}><Meetings /></Suspense>} />
        <Route path="infrastructure" element={<Suspense fallback={<LoadingState message="Loading Infrastructure..." />}><Infrastructure /></Suspense>} />
      </Route>
    </Routes>
  );
}
