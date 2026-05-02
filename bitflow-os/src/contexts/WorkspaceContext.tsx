import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as engine from '@/api/engineClient';
import type { WorkspaceResponse } from '@/api/types';

interface WorkspaceContextValue {
  workspace: string;
  workspaceId: number | null;
  workspaces: WorkspaceResponse[];
  setWorkspace: (path: string) => void;
  registerWorkspace: (path: string, name?: string) => Promise<void>;
  removeWorkspace: (id: number) => Promise<void>;
  isLoading: boolean;
}

const DEFAULT_WORKSPACE = 'D:\\Bitflow_softwares\\timepass';

const WorkspaceContext = createContext<WorkspaceContextValue>({
  workspace: DEFAULT_WORKSPACE,
  workspaceId: null,
  workspaces: [],
  setWorkspace: () => {},
  registerWorkspace: async () => {},
  removeWorkspace: async () => {},
  isLoading: false,
});

export function useWorkspace() {
  return useContext(WorkspaceContext);
}

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [workspace, setWorkspaceState] = useState<string>(() => {
    return localStorage.getItem('bitflow-workspace') || DEFAULT_WORKSPACE;
  });
  const queryClient = useQueryClient();

  const { data: workspaces = [], isLoading } = useQuery({
    queryKey: ['workspaces'],
    queryFn: engine.getWorkspaces,
    staleTime: 60_000,
    retry: 1,
  });

  const workspaceId = workspaces.find((w) => w.path === workspace)?.id ?? null;

  const setWorkspace = useCallback((path: string) => {
    setWorkspaceState(path);
    localStorage.setItem('bitflow-workspace', path);
    // Invalidate all workspace-dependent queries
    queryClient.invalidateQueries();
  }, [queryClient]);

  const registerMutation = useMutation({
    mutationFn: ({ path, name }: { path: string; name?: string }) =>
      engine.registerWorkspace({ path, name }),
    onSuccess: (newWs) => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
      setWorkspace(newWs.path);
    },
  });

  const removeMutation = useMutation({
    mutationFn: (id: number) => engine.deleteWorkspace(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
    },
  });

  const registerWorkspace = useCallback(
    async (path: string, name?: string) => {
      await registerMutation.mutateAsync({ path, name });
    },
    [registerMutation]
  );

  const removeWorkspace = useCallback(
    async (id: number) => {
      await removeMutation.mutateAsync(id);
    },
    [removeMutation]
  );

  return (
    <WorkspaceContext.Provider
      value={{
        workspace,
        workspaceId,
        workspaces,
        setWorkspace,
        registerWorkspace,
        removeWorkspace,
        isLoading,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}
