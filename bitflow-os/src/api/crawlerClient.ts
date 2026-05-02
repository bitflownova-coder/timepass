import type { CrawlConfig, CrawlStatus, CrawlResult } from './types';

const CRAWLER_BASE = 'http://127.0.0.1:5000';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${CRAWLER_BASE}${endpoint}`, {
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Crawler API error ${response.status}`);
  }
  return response.json();
}

export const startCrawl = (config: CrawlConfig): Promise<CrawlResult> => {
  const formData = new FormData();
  formData.append('url', config.url);
  formData.append('depth', String(config.depth));
  formData.append('concurrency', String(config.concurrency));
  formData.append('delay', String(config.delay));
  if (config.proxy) formData.append('proxy', config.proxy);
  formData.append('user_agent_strategy', config.user_agent_strategy);
  if (config.allow_regex) formData.append('allow_regex', config.allow_regex);
  if (config.deny_regex) formData.append('deny_regex', config.deny_regex);

  return fetch(`${CRAWLER_BASE}/crawl`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
    body: formData,
  }).then((r) => r.json());
};

export const getCrawlStatus = (crawlId: string): Promise<CrawlStatus> =>
  request<CrawlStatus>(`/status/${crawlId}`);

export const controlCrawl = (crawlId: string, action: 'pause' | 'resume' | 'stop') =>
  fetch(`${CRAWLER_BASE}/control/${crawlId}/${action}`, { method: 'POST' }).then((r) => r.json());

export interface CrawlerHealthResponse {
  error?: string;
  version?: string;
}

export const getCrawlerHealth = async (): Promise<CrawlerHealthResponse | null> => {
  try {
    const r = await fetch(`${CRAWLER_BASE}/`, { signal: AbortSignal.timeout(3000) });
    if (!r.ok) return null;
    return r.json();
  } catch {
    return null;
  }
};
