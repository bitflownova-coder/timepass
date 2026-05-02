import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatUptime(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}

export function formatTimestamp(ts: string | number): string {
  const date = new Date(ts);
  return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

export function getRiskColor(score: number): string {
  if (score <= 2) return 'text-accent-green';
  if (score <= 4) return 'text-brand-400';
  if (score <= 6) return 'text-accent-amber';
  if (score <= 8) return 'text-orange-500';
  return 'text-accent-red';
}

export function getRiskBgColor(score: number): string {
  if (score <= 2) return 'bg-accent-green/10';
  if (score <= 4) return 'bg-brand-400/10';
  if (score <= 6) return 'bg-accent-amber/10';
  if (score <= 8) return 'bg-orange-500/10';
  return 'bg-accent-red/10';
}

export function getRiskLabel(score: number): string {
  if (score <= 2) return 'Healthy';
  if (score <= 4) return 'Good';
  if (score <= 6) return 'Caution';
  if (score <= 8) return 'At Risk';
  return 'Critical';
}

export function getSeverityColor(severity: string): string {
  switch (severity?.toUpperCase()) {
    case 'CRITICAL': return 'text-accent-red bg-accent-red/10 border-accent-red/30';
    case 'HIGH': return 'text-orange-400 bg-orange-400/10 border-orange-400/30';
    case 'MEDIUM': return 'text-accent-amber bg-accent-amber/10 border-accent-amber/30';
    case 'LOW': return 'text-accent-green bg-accent-green/10 border-accent-green/30';
    default: return 'text-gray-400 bg-gray-400/10 border-gray-400/30';
  }
}
