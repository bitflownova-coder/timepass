import React from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Brain,
  ShieldCheck,
  Globe,
  Wrench,
  Briefcase,
  Monitor,
  ChevronLeft,
  ChevronRight,
  Cpu,
  CalendarCheck,
  Server,
  Settings,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

interface NavItem {
  path: string;
  label: string;
  icon: React.ElementType;
  enabled: boolean;
  badge?: string;
}

const navGroups: { title: string; items: NavItem[] }[] = [
  {
    title: 'Overview',
    items: [
      { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, enabled: true },
    ],
  },
  {
    title: 'Intelligence',
    items: [
      { path: '/ai-intelligence', label: 'AI Intelligence', icon: Brain, enabled: true },
      { path: '/code-health', label: 'Code Health', icon: ShieldCheck, enabled: true },
    ],
  },
  {
    title: 'Operations',
    items: [
      { path: '/web-crawler', label: 'Web Crawler', icon: Globe, enabled: true },
      { path: '/dev-tools', label: 'Dev Tools', icon: Wrench, enabled: true },
      { path: '/business', label: 'Business', icon: Briefcase, enabled: true },
    ],
  },
  {
    title: 'System',
    items: [
      { path: '/device-monitor', label: 'Device Monitor', icon: Monitor, enabled: true },
      { path: '/meetings', label: 'Meetings', icon: CalendarCheck, enabled: true },
      { path: '/infrastructure', label: 'Infrastructure', icon: Server, enabled: true },
      { path: '/settings', label: 'Settings', icon: Settings, enabled: true },
    ],
  },
];

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside
      className={cn(
        'h-full bg-surface-0 border-r border-surface-3 flex flex-col transition-all duration-200',
        collapsed ? 'w-16' : 'w-56'
      )}
    >
      {/* Navigation */}
      <nav className="flex-1 py-3 overflow-y-auto">
        {navGroups.map((group) => (
          <div key={group.title} className="mb-3">
            {!collapsed && (
              <div className="px-4 py-1">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-600">
                  {group.title}
                </span>
              </div>
            )}
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.enabled ? item.path : '#'}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 mx-2 px-3 py-2 rounded-lg text-sm transition-all duration-150',
                      isActive && item.enabled
                        ? 'bg-brand-600/15 text-brand-400 font-medium'
                        : item.enabled
                          ? 'text-gray-400 hover:text-gray-200 hover:bg-surface-3'
                          : 'text-gray-700 cursor-not-allowed',
                      collapsed && 'justify-center px-2'
                    )
                  }
                  onClick={(e) => !item.enabled && e.preventDefault()}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className={cn('w-4.5 h-4.5 flex-shrink-0', collapsed ? 'w-5 h-5' : '')} />
                  {!collapsed && (
                    <>
                      <span className="flex-1 truncate">{item.label}</span>
                      {item.badge && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-surface-4 text-gray-500">
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div className="p-2 border-t border-surface-3">
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-center p-2 rounded-lg hover:bg-surface-3 text-gray-500 transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
