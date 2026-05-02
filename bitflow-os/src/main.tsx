import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { WorkspaceProvider } from './contexts/WorkspaceContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { WebSocketProvider } from './contexts/WebSocketProvider';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
      staleTime: 30_000,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <WorkspaceProvider>
        <NotificationProvider>
          <WebSocketProvider>
            <BrowserRouter>
              <App />
            </BrowserRouter>
          </WebSocketProvider>
        </NotificationProvider>
      </WorkspaceProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
