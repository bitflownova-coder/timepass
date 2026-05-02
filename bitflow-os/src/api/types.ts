// ===== Copilot Engine Types (matching models.py) =====

export interface HealthResponse {
  status: string;
  version: string;
  uptime: number;
  watched_workspaces: string[];
}

export interface WorkspaceCreate {
  path: string;
  name?: string;
}

export interface WorkspaceResponse {
  id: number;
  path: string;
  name: string;
  language: string;
  framework: string;
  last_active: string;
}

export interface ErrorInput {
  error_text: string;
  workspace_path?: string;
  file_path?: string;
}

export interface ErrorResponse {
  error_type: string;
  message: string;
  file_path: string;
  line_number: number;
  suggestions: string[];
  related_files: string[];
  language: string;
}

export interface ContextRequest {
  workspace_path: string;
  current_file?: string;
  error_text?: string;
  task: string;
  include_schema?: boolean;
}

export interface ContextResponse {
  prompt: string;
  token_estimate: number;
  metadata: Record<string, any>;
}

export interface SecurityFinding {
  type: string;
  severity: string;
  file: string;
  line: number;
  message: string;
  suggestion: string;
}

export interface RiskCategory {
  score: number;
  level: string;
  issues: string[];
}

export interface RiskResult {
  overall_score: number;
  health_level: 'HEALTHY' | 'CAUTION' | 'AT_RISK' | 'DEGRADED' | 'CRITICAL';
  categories: {
    schema: RiskCategory;
    contract: RiskCategory;
    migration: RiskCategory;
    dependency: RiskCategory;
    security: RiskCategory;
    naming: RiskCategory;
    drift: RiskCategory;
  };
  timestamp: string;
}

export interface DriftEvent {
  id: number;
  workspace_id: number;
  file_path: string;
  entity_name: string;
  drift_type: string;
  old_value: string;
  new_value: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  timestamp: string;
  resolved: boolean;
  resolution: string | null;
}

export interface EntityInfo {
  id: number;
  file_path: string;
  entity_type: string;
  entity_name: string;
  line_start: number;
  line_end: number;
  signature: string;
  extra_info: Record<string, any>;
}

export interface GraphStats {
  total_files: number;
  file_edges: number;
  entity_edges: number;
  most_depended: { file: string; dependents: number }[];
  dead_code_files: string[];
  circular_count: number;
}

export interface ChangeImpact {
  changed_file: string;
  category: string;
  risk_score: number;
  risk_level: string;
  affected_files: string[];
  breaking_changes: string[];
  warnings: string[];
  details: Record<string, any>;
}

export interface BehaviorStatus {
  error_count: number;
  repeated_errors: number;
  most_repeated_error: string;
  file_switches: number;
  rapid_switches: number;
  files_visited: number;
  saves: number;
  terminal_runs: number;
  focus_mode_suggested: boolean;
  message: string;
  session_minutes: number;
}

export interface AutonomousDashboard {
  health: RiskResult;
  risk_trend: RiskTrendPoint[];
  unresolved_drifts: DriftEvent[];
  circular_dependencies: string[][];
  dead_code_files: string[];
  timestamp: string;
}

export interface RiskTrendPoint {
  timestamp: string;
  overall_score: number;
  schema: number;
  contract: number;
  migration: number;
  dependency: number;
  security: number;
  naming: number;
  drift: number;
}

export interface GitCommit {
  hash: string;
  author: string;
  date: string;
  message: string;
  files_changed: number;
}

export interface ContractAnalysis {
  endpoints: ContractEndpoint[];
  violations: ContractViolation[];
  stats: { total: number; valid: number; violations: number };
}

export interface ContractEndpoint {
  method: string;
  path: string;
  file: string;
  line: number;
  handler: string;
}

export interface ContractViolation {
  type: string;
  endpoint: string;
  message: string;
  severity: string;
}

export interface PipelineResult {
  passed: boolean;
  checks: PipelineCheck[];
  summary: { total: number; passed: number; failed: number; warnings: number };
}

export interface PipelineCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  message: string;
  details?: Record<string, any>;
}

// ===== Crawler Types =====

export interface CrawlConfig {
  url: string;
  depth: number;
  concurrency: number;
  delay: number;
  proxy?: string;
  user_agent_strategy: string;
  allow_regex?: string;
  deny_regex?: string;
}

export interface CrawlStatus {
  status: string;
  pending_queue: number;
  url?: string;
  pages_crawled?: number;
  pages_queued?: number;
  errors?: number;
}

export interface CrawlResult {
  crawl_id: string;
  status: string;
}

// ===== System Monitor Types =====

export interface SystemCpu {
  percent: number;
  per_core: number[];
  cores_physical: number;
  cores_logical: number;
  freq_current: number;
  freq_max: number;
}

export interface SystemMemory {
  total: number;
  used: number;
  available: number;
  percent: number;
  swap_total: number;
  swap_used: number;
  swap_percent: number;
}

export interface SystemDisk {
  total: number;
  used: number;
  free: number;
  percent: number;
}

export interface SystemNetwork {
  bytes_sent: number;
  bytes_recv: number;
  packets_sent: number;
  packets_recv: number;
}

export interface SystemInfo {
  platform: string;
  platform_release: string;
  hostname: string;
  architecture: string;
  python_version: string;
  boot_time: number;
  uptime_seconds: number;
}

export interface SystemBattery {
  percent: number;
  plugged: boolean;
  secs_left: number;
}

export interface SystemSnapshot {
  timestamp: number;
  cpu: SystemCpu;
  memory: SystemMemory;
  disk: SystemDisk;
  network: SystemNetwork;
  system: SystemInfo;
  battery?: SystemBattery;
}

export interface ProcessInfo {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_percent: number;
  status: string;
}

export interface DiskPartition {
  device: string;
  mountpoint: string;
  fstype: string;
  total: number;
  used: number;
  free: number;
  percent: number;
}

export interface SystemHistoryPoint {
  timestamp: number;
  cpu: number;
  memory: number;
  disk: number;
  net_sent: number;
  net_recv: number;
}

// ===== Project Analytics Types =====

export interface LanguageStat {
  language: string;
  files: number;
  lines: number;
  bytes: number;
}

export interface WorkspaceSummary {
  workspace: string;
  total_files: number;
  total_lines: number;
  total_bytes: number;
  directories: number;
  languages: LanguageStat[];
  largest_files: { path: string; size: number; lines: number; language: string }[];
  analysis_time_seconds: number;
}

export interface HealthBreakdownItem {
  status: 'good' | 'warning' | 'critical';
  penalty: number;
  [key: string]: any;
}

export interface ProjectHealth {
  workspace: string;
  score: number;
  health_level: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'CRITICAL';
  breakdown: Record<string, HealthBreakdownItem>;
}

// ===== Meeting Types =====

export interface Meeting {
  id: string;
  title: string;
  date: string;
  attendees: string[];
  category: string;
  notes: string;
  status: string;
  summary: string;
  created_at: string;
  action_items?: ActionItem[];
  follow_ups?: FollowUp[];
  action_item_count?: number;
  action_items_done?: number;
  pending_follow_ups?: number;
}

export interface ActionItem {
  id: string;
  meeting_id: string;
  text: string;
  assignee: string;
  due_date: string;
  completed: number;
  completed_at: string;
  priority: string;
  created_at: string;
  meeting_title?: string;
  meeting_date?: string;
}

export interface FollowUp {
  id: string;
  meeting_id: string;
  text: string;
  due_date: string;
  completed: number;
  created_at: string;
  meeting_title?: string;
  meeting_date?: string;
}

export interface MeetingStats {
  total_meetings: number;
  this_week: number;
  pending_actions: number;
  pending_follow_ups: number;
  completion_rate: number;
}

// ===== Infrastructure Types =====

export interface LatestCheck {
  status_code: number;
  response_time_ms: number;
  is_up: number;
  error_message: string;
  checked_at: string;
}

export interface InfraEndpoint {
  id: string;
  name: string;
  url: string;
  method: string;
  expected_status: number;
  timeout_seconds: number;
  check_interval_seconds: number;
  category: string;
  enabled: number;
  created_at: string;
  latest_check: LatestCheck | null;
  uptime_24h: number;
}

export interface CheckResult {
  endpoint_id: string;
  name: string;
  url: string;
  status_code: number;
  response_time_ms: number;
  is_up: boolean;
  error_message: string;
  checked_at: string;
}

export interface InfraAlert {
  id: string;
  endpoint_id: string;
  endpoint_name: string;
  endpoint_url: string;
  alert_type: string;
  message: string;
  severity: string;
  acknowledged: number;
  created_at: string;
}

export interface InfraStats {
  total_endpoints: number;
  enabled_endpoints: number;
  endpoints_up: number;
  endpoints_down: number;
  total_checks: number;
  unacknowledged_alerts: number;
  avg_response_time_ms: number;
}
