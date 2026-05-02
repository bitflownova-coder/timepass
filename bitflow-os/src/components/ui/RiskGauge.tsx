import React from 'react';
import { cn, getRiskColor, getRiskLabel } from '@/lib/utils';

interface RiskGaugeProps {
  score: number;
  maxScore?: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function RiskGauge({ score, maxScore = 10, size = 'md', showLabel = true }: RiskGaugeProps) {
  const percentage = (score / maxScore) * 100;
  const circumference = 2 * Math.PI * 40;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const dimensions = { sm: 80, md: 120, lg: 160 };
  const dim = dimensions[size];

  const getStrokeColor = (s: number) => {
    if (s <= 2) return '#10b981';
    if (s <= 4) return '#3b82f6';
    if (s <= 6) return '#f59e0b';
    if (s <= 8) return '#f97316';
    return '#ef4444';
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: dim, height: dim }}>
        <svg viewBox="0 0 100 100" className="transform -rotate-90" style={{ width: dim, height: dim }}>
          {/* Background circle */}
          <circle
            cx="50" cy="50" r="40"
            fill="none"
            stroke="#1a1a24"
            strokeWidth="8"
          />
          {/* Progress circle */}
          <circle
            cx="50" cy="50" r="40"
            fill="none"
            stroke={getStrokeColor(score)}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn('font-bold', getRiskColor(score), size === 'lg' ? 'text-3xl' : size === 'md' ? 'text-2xl' : 'text-lg')}>
            {score.toFixed(1)}
          </span>
          <span className="text-[10px] text-gray-600">/ {maxScore}</span>
        </div>
      </div>
      {showLabel && (
        <span className={cn('text-xs font-semibold', getRiskColor(score))}>
          {getRiskLabel(score)}
        </span>
      )}
    </div>
  );
}
