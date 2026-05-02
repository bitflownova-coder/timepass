import type {
  HealthResponse,
  WorkspaceCreate,
  WorkspaceResponse,
  ErrorInput,
  ErrorResponse,
  ContextRequest,
  ContextResponse,
  AutonomousDashboard,
  RiskTrendPoint,
  DriftEvent,
  EntityInfo,
  GraphStats,
  ChangeImpact,
  BehaviorStatus,
  GitCommit,
  SecurityFinding,
  ContractAnalysis,
  PipelineResult,
  SystemSnapshot,
  ProcessInfo,
  DiskPartition,
  SystemHistoryPoint,
  WorkspaceSummary,
  ProjectHealth,
  Meeting,
  ActionItem,
  FollowUp,
  MeetingStats,
  InfraEndpoint,
  CheckResult,
  InfraAlert,
  InfraStats,
} from './types';

const ENGINE_BASE = 'http://127.0.0.1:7779';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${ENGINE_BASE}${endpoint}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    const error = await response.text().catch(() => 'Unknown error');
    throw new Error(`Engine API error ${response.status}: ${error}`);
  }
  return response.json();
}

function post<T>(endpoint: string, body: Record<string, any>): Promise<T> {
  return request<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// ===== Health =====
export const getHealth = () => request<HealthResponse>('/health');
export const getCacheStats = () => request<any>('/cache/stats');
export const clearCache = () => post<any>('/cache/clear', {});

// ===== Workspace =====
export const registerWorkspace = (data: WorkspaceCreate) =>
  post<WorkspaceResponse>('/workspace/register', data);
export const getWorkspaces = () => request<WorkspaceResponse[]>('/workspaces');
export const deleteWorkspace = (id: number) =>
  request<any>(`/workspace/${id}`, { method: 'DELETE' });

// ===== Error Analysis =====
export const parseError = (data: ErrorInput) =>
  post<ErrorResponse>('/error/parse', data);
export const findSimilarErrors = (data: ErrorInput) =>
  post<any>('/error/find-similar', data);

// ===== Context =====
export const buildContext = (data: ContextRequest) =>
  post<ContextResponse>('/context/build', data);
export const debugContext = (data: ErrorInput) =>
  post<ContextResponse>('/context/debug', data);

// ===== Git =====
export const getGitDiff = (workspacePath: string) =>
  post<any>('/git/diff', { workspace_path: workspacePath });
export const getRecentCommits = (workspacePath: string, limit = 20) =>
  request<{ workspace: string; commits: GitCommit[] }>(
    `/git/recent-commits/${encodeURIComponent(workspacePath)}?limit=${limit}`
  );
export const analyzeGitChange = (workspacePath: string, filePath: string) =>
  post<any>('/git/analyze-change', { workspace_path: workspacePath, file_path: filePath });
export const correlateError = (workspacePath: string, errorText: string) =>
  post<any>('/git/correlate', { workspace_path: workspacePath, error_text: errorText });
export const getGitBranch = (workspacePath: string) =>
  request<{ workspace: string; branch: string }>(
    `/git/branch/${encodeURIComponent(workspacePath)}`
  );
export const getChangedFiles = (workspacePath: string) =>
  request<{ workspace: string; files: string[] }>(
    `/git/changed-files/${encodeURIComponent(workspacePath)}`
  );

// ===== Security =====
export const scanFile = (filePath: string) =>
  post<SecurityFinding[]>('/security/scan', { file_path: filePath });
export const scanWorkspace = (workspacePath: string) =>
  post<any>('/security/scan-workspace', { workspace_path: workspacePath });

// ===== SQL =====
export const analyzeSQL = (query: string, workspacePath?: string) =>
  post<any>('/sql/analyze', { query, workspace_path: workspacePath });
export const validateSQL = (query: string) =>
  post<any>('/sql/validate', { query });

// ===== API Detection =====
export const detectAPIs = (workspacePath: string) =>
  post<any>('/api/detect', { workspace_path: workspacePath });
export const validateAPI = (workspacePath: string, method: string, route: string) =>
  post<any>('/api/validate', { workspace_path: workspacePath, method, route });

// ===== Behavior =====
export const trackBehavior = (workspacePath: string, event: string, data: any) =>
  post<any>('/behavior/track', { workspace_path: workspacePath, event, data });
export const getBehaviorStatus = (workspacePath: string) =>
  request<BehaviorStatus>(`/behavior/status/${encodeURIComponent(workspacePath)}`);
export const getBehaviorReport = (workspacePath: string) =>
  request<any>(`/behavior/report/${encodeURIComponent(workspacePath)}`);

// ===== Prompt =====
export const optimizePrompt = (data: {
  workspace_path: string;
  task: string;
  current_file?: string;
  error_text?: string;
  code_snippet?: string;
}) => post<ContextResponse>('/prompt/optimize', data);

// ===== Prisma / ORM =====
export const analyzePrisma = (workspacePath: string) =>
  post<any>('/prisma/analyze', { workspace_path: workspacePath });
export const validatePrisma = (workspacePath: string) =>
  post<any>('/prisma/validate', { workspace_path: workspacePath });
export const getPrismaSchema = (workspacePath: string) =>
  post<any>('/prisma/schema', { workspace_path: workspacePath });
export const validateDTO = (workspacePath: string, dtoFile: string) =>
  post<any>('/prisma/validate-dto', { workspace_path: workspacePath, dto_file: dtoFile });

// ===== Contracts =====
export const analyzeContracts = (workspacePath: string) =>
  post<ContractAnalysis>('/contracts/analyze', { workspace_path: workspacePath });
export const validateContracts = (workspacePath: string) =>
  post<any>('/contracts/validate', { workspace_path: workspacePath });
export const checkContract = (workspacePath: string, method: string, path: string) =>
  post<any>('/contracts/check', { workspace_path: workspacePath, method, path });
export const getContractMap = (workspacePath: string) =>
  post<any>('/contracts/map', { workspace_path: workspacePath });

// ===== Impact =====
export const buildImpactGraph = (workspacePath: string) =>
  post<any>('/impact/build-graph', { workspace_path: workspacePath });
export const analyzeImpact = (
  workspacePath: string, changedFile: string, oldContent?: string, newContent?: string
) =>
  post<ChangeImpact>('/impact/analyze', {
    workspace_path: workspacePath, changed_file: changedFile, old_content: oldContent, new_content: newContent,
  });
export const analyzeMultiImpact = (workspacePath: string, files: string[]) =>
  post<any>('/impact/analyze-multi', { workspace_path: workspacePath, files });
export const getFileInfo = (workspacePath: string, filePath: string) =>
  post<any>('/impact/file-info', { workspace_path: workspacePath, file_path: filePath });
export const getDependencyMap = (workspacePath: string) =>
  post<any>('/impact/dependency-map', { workspace_path: workspacePath });

// ===== Validation Pipeline =====
export const fullScan = (workspacePath: string) =>
  post<PipelineResult>('/pipeline/full-scan', { workspace_path: workspacePath });
export const fileScan = (workspacePath: string, filePath: string, oldContent?: string, newContent?: string) =>
  post<any>('/pipeline/file-change', {
    workspace_path: workspacePath, file_path: filePath, old_content: oldContent, new_content: newContent,
  });
export const preCommitScan = (workspacePath: string, files: string[]) =>
  post<any>('/pipeline/pre-commit', { workspace_path: workspacePath, changed_files: files });

// ===== Stack =====
export const detectStack = (workspacePath: string) =>
  post<any>('/stack/detect', { workspace_path: workspacePath });

// ===== Autonomous =====
export const initializeAutonomous = (workspacePath: string) =>
  post<any>('/autonomous/initialize', { workspace_path: workspacePath });
export const getAutonomousHealth = (workspacePath: string) =>
  request<any>(`/autonomous/health/${encodeURIComponent(workspacePath)}`);
export const getAutonomousStatus = () =>
  request<any>('/autonomous/status');
export const getAutonomousDashboard = (workspacePath: string) =>
  request<AutonomousDashboard>(`/autonomous/dashboard/${encodeURIComponent(workspacePath)}`);
export const getRiskTrend = (workspacePath: string, limit = 50) =>
  request<RiskTrendPoint[]>(`/autonomous/risk-trend/${encodeURIComponent(workspacePath)}?limit=${limit}`);
export const getDrifts = (workspacePath: string) =>
  request<DriftEvent[]>(`/autonomous/drifts/${encodeURIComponent(workspacePath)}`);
export const getCircularDeps = () =>
  request<string[][]>('/autonomous/circular-deps');
export const getDeadCode = () =>
  request<string[]>('/autonomous/dead-code');
export const getGraphStats = () =>
  request<GraphStats>('/autonomous/graph-stats');
export const getEntities = (workspacePath: string, entityType?: string) =>
  request<EntityInfo[]>(
    `/autonomous/entities/${encodeURIComponent(workspacePath)}${entityType ? `?entity_type=${entityType}` : ''}`
  );
export const configureAutonomous = (workspacePath: string, config: any) =>
  post<any>('/autonomous/configure', { workspace_path: workspacePath, ...config });

// ===== System Monitor =====
export const getSystemStats = () =>
  request<SystemSnapshot>('/system/stats');
export const getSystemProcesses = (limit = 15, sortBy = 'cpu') =>
  request<{ processes: ProcessInfo[] }>(`/system/processes?limit=${limit}&sort_by=${sortBy}`);
export const getSystemDisks = () =>
  request<{ partitions: DiskPartition[] }>('/system/disks');
export const getSystemHistory = () =>
  request<{ history: SystemHistoryPoint[] }>('/system/history');

// ===== Project Analytics =====
export const getWorkspaceSummary = (workspacePath: string) =>
  post<WorkspaceSummary>('/analytics/workspace-summary', { workspace_path: workspacePath });
export const getProjectHealth = (workspacePath: string) =>
  post<ProjectHealth>('/analytics/project-health', { workspace_path: workspacePath });
export const compareWorkspaces = (workspacePaths: string[]) =>
  post<{ workspaces: WorkspaceSummary[] }>('/analytics/compare', { workspace_paths: workspacePaths });

// ===== Meeting Manager =====
export const createMeeting = (body: Partial<Meeting>) =>
  post<Meeting>('/meetings', body);
export const listMeetings = (filter?: string, category?: string) => {
  const params = new URLSearchParams();
  if (filter) params.set('filter', filter);
  if (category) params.set('category', category);
  const qs = params.toString();
  return request<{ meetings: Meeting[] }>(`/meetings${qs ? `?${qs}` : ''}`);
};
export const getMeeting = (id: string) =>
  request<Meeting>(`/meetings/${id}`);
export const updateMeeting = (id: string, body: Partial<Meeting>) =>
  request<Meeting>(`/meetings/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
export const deleteMeeting = (id: string) =>
  request<{ deleted: boolean }>(`/meetings/${id}`, { method: 'DELETE' });
export const addActionItem = (meetingId: string, body: Partial<ActionItem>) =>
  post<ActionItem>(`/meetings/${meetingId}/action-items`, body);
export const updateActionItem = (itemId: string, body: Partial<ActionItem>) =>
  request<ActionItem>(`/meetings/action-items/${itemId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
export const getPendingActions = () =>
  request<{ actions: ActionItem[] }>('/meetings/pending-actions');
export const addFollowUp = (meetingId: string, body: Partial<FollowUp>) =>
  post<FollowUp>(`/meetings/${meetingId}/follow-ups`, body);
export const getPendingFollowUps = () =>
  request<{ follow_ups: FollowUp[] }>('/meetings/pending-follow-ups');
export const getMeetingStats = () =>
  request<MeetingStats>('/meetings/stats');

// ===== Infrastructure Monitor =====
export const addInfraEndpoint = (body: Partial<InfraEndpoint>) =>
  post<InfraEndpoint>('/infra/endpoints', body);
export const listInfraEndpoints = () =>
  request<{ endpoints: InfraEndpoint[] }>('/infra/endpoints');
export const updateInfraEndpoint = (id: string, body: Partial<InfraEndpoint>) =>
  request<InfraEndpoint>(`/infra/endpoints/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
export const deleteInfraEndpoint = (id: string) =>
  request<{ deleted: boolean }>(`/infra/endpoints/${id}`, { method: 'DELETE' });
export const checkEndpoint = (id: string) =>
  post<CheckResult>(`/infra/check/${id}`, {});
export const checkAllEndpoints = () =>
  post<{ results: CheckResult[] }>('/infra/check-all', {});
export const getCheckHistory = (id: string, limit = 100) =>
  request<{ history: CheckResult[] }>(`/infra/history/${id}?limit=${limit}`);
export const getInfraAlerts = (acknowledged?: boolean) => {
  const qs = acknowledged !== undefined ? `?acknowledged=${acknowledged}` : '';
  return request<{ alerts: InfraAlert[] }>(`/infra/alerts${qs}`);
};
export const acknowledgeAlert = (alertId: string) =>
  request<{ acknowledged: boolean }>(`/infra/alerts/${alertId}/acknowledge`, { method: 'PUT' });
export const getInfraStats = () =>
  request<InfraStats>('/infra/stats');
