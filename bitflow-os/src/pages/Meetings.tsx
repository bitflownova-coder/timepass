import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CalendarCheck, ListTodo, Users, Clock, CheckCircle, Plus,
  Trash2, Edit3, ChevronDown, ChevronUp, AlertTriangle, X,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import * as engine from '@/api/engineClient';
import type { Meeting, ActionItem, FollowUp } from '@/api/types';
import { cn } from '@/lib/utils';

const CATEGORY_COLORS: Record<string, string> = {
  general: 'bg-gray-500/20 text-gray-400',
  standup: 'bg-blue-500/20 text-blue-400',
  planning: 'bg-purple-500/20 text-purple-400',
  review: 'bg-amber-500/20 text-amber-400',
  client: 'bg-green-500/20 text-green-400',
  '1on1': 'bg-pink-500/20 text-pink-400',
};

const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-500/20 text-red-400',
  medium: 'bg-amber-500/20 text-amber-400',
  low: 'bg-green-500/20 text-green-400',
};

function formatDate(d: string): string {
  if (!d) return '—';
  try {
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch { return d; }
}

function isOverdue(d: string): boolean {
  if (!d) return false;
  try { return new Date(d) < new Date(); } catch { return false; }
}

// ── Stats Bar ──
function StatsBar() {
  const { data } = useQuery({ queryKey: ['meeting-stats'], queryFn: engine.getMeetingStats, refetchInterval: 15_000 });
  if (!data) return null;
  const cards = [
    { label: 'Total Meetings', value: data.total_meetings, icon: CalendarCheck, color: 'text-brand-400' },
    { label: 'This Week', value: data.this_week, icon: Clock, color: 'text-purple-400' },
    { label: 'Pending Actions', value: data.pending_actions, icon: ListTodo, color: 'text-amber-400' },
    { label: 'Completion', value: `${data.completion_rate}%`, icon: CheckCircle, color: 'text-green-400' },
  ];
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
      {cards.map((c) => (
        <div key={c.label} className="bg-surface-2 rounded-xl p-4 flex items-center gap-3">
          <c.icon className={cn('w-8 h-8', c.color)} />
          <div>
            <p className="text-2xl font-bold text-white">{c.value}</p>
            <p className="text-xs text-gray-500">{c.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── New Meeting Form ──
function NewMeetingForm({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [attendees, setAttendees] = useState('');
  const [category, setCategory] = useState('general');
  const [notes, setNotes] = useState('');

  const mutation = useMutation({
    mutationFn: () => engine.createMeeting({
      title, date, attendees: attendees.split(',').map(a => a.trim()).filter(Boolean),
      category, notes,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['meetings'] }); qc.invalidateQueries({ queryKey: ['meeting-stats'] }); onClose(); },
  });

  return (
    <Card className="mb-4 border border-brand-500/30">
      <CardHeader><CardTitle className="text-sm">New Meeting</CardTitle></CardHeader>
      <div className="px-4 pb-4 space-y-3">
        <input className="w-full bg-surface-3 text-white rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-brand-500 outline-none" placeholder="Meeting title" value={title} onChange={e => setTitle(e.target.value)} />
        <div className="flex gap-3">
          <input type="datetime-local" className="flex-1 bg-surface-3 text-white rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-brand-500 outline-none" value={date} onChange={e => setDate(e.target.value)} />
          <select className="bg-surface-3 text-white rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-brand-500 outline-none" value={category} onChange={e => setCategory(e.target.value)}>
            {Object.keys(CATEGORY_COLORS).map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <input className="w-full bg-surface-3 text-white rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-brand-500 outline-none" placeholder="Attendees (comma-separated)" value={attendees} onChange={e => setAttendees(e.target.value)} />
        <textarea className="w-full bg-surface-3 text-white rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-brand-500 outline-none resize-none" rows={3} placeholder="Notes..." value={notes} onChange={e => setNotes(e.target.value)} />
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-1.5 rounded-lg bg-surface-3 text-gray-400 text-sm hover:text-white">Cancel</button>
          <button onClick={() => mutation.mutate()} disabled={!title || mutation.isPending} className="px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm hover:bg-brand-500 disabled:opacity-50">
            {mutation.isPending ? 'Creating...' : 'Create'}
          </button>
        </div>
      </div>
    </Card>
  );
}

// ── Meeting Detail ──
function MeetingDetail({ meeting }: { meeting: Meeting }) {
  const qc = useQueryClient();
  const { data: detail } = useQuery({ queryKey: ['meeting', meeting.id], queryFn: () => engine.getMeeting(meeting.id) });
  const [aiText, setAiText] = useState('');
  const [aiAssignee, setAiAssignee] = useState('');
  const [aiPriority, setAiPriority] = useState('medium');
  const [fuText, setFuText] = useState('');

  const addAI = useMutation({
    mutationFn: () => engine.addActionItem(meeting.id, { text: aiText, assignee: aiAssignee, priority: aiPriority }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['meeting', meeting.id] }); qc.invalidateQueries({ queryKey: ['meeting-stats'] }); setAiText(''); setAiAssignee(''); },
  });
  const toggleAI = useMutation({
    mutationFn: (item: ActionItem) => engine.updateActionItem(item.id, { completed: item.completed ? 0 : 1 }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['meeting', meeting.id] }); qc.invalidateQueries({ queryKey: ['pending-actions'] }); qc.invalidateQueries({ queryKey: ['meeting-stats'] }); },
  });
  const addFU = useMutation({
    mutationFn: () => engine.addFollowUp(meeting.id, { text: fuText }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['meeting', meeting.id] }); setFuText(''); },
  });

  const m = detail || meeting;
  const actions = m.action_items || [];
  const followUps = m.follow_ups || [];

  return (
    <div className="bg-surface-1 rounded-lg p-4 mt-2 border border-surface-3 space-y-4">
      {m.notes && <p className="text-sm text-gray-400 whitespace-pre-wrap">{m.notes}</p>}

      {/* Action Items */}
      <div>
        <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Action Items ({actions.length})</h4>
        {actions.map(ai => (
          <div key={ai.id} className="flex items-center gap-2 py-1.5 border-b border-surface-3 last:border-0">
            <button onClick={() => toggleAI.mutate(ai)} className={cn('w-4 h-4 rounded border flex-shrink-0', ai.completed ? 'bg-green-500 border-green-500' : 'border-gray-600')}>
              {ai.completed ? <CheckCircle className="w-4 h-4 text-white" /> : null}
            </button>
            <span className={cn('text-sm flex-1', ai.completed ? 'line-through text-gray-600' : 'text-gray-300')}>{ai.text}</span>
            {ai.assignee && <span className="text-xs text-gray-500">@{ai.assignee}</span>}
            <Badge className={PRIORITY_COLORS[ai.priority] || ''}>{ai.priority}</Badge>
          </div>
        ))}
        <div className="flex gap-2 mt-2">
          <input className="flex-1 bg-surface-3 text-white rounded px-2 py-1 text-xs outline-none" placeholder="New action item..." value={aiText} onChange={e => setAiText(e.target.value)} />
          <input className="w-24 bg-surface-3 text-white rounded px-2 py-1 text-xs outline-none" placeholder="Assignee" value={aiAssignee} onChange={e => setAiAssignee(e.target.value)} />
          <select className="bg-surface-3 text-white rounded px-2 py-1 text-xs outline-none" value={aiPriority} onChange={e => setAiPriority(e.target.value)}>
            <option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
          </select>
          <button onClick={() => addAI.mutate()} disabled={!aiText} className="px-2 py-1 rounded bg-brand-600 text-white text-xs hover:bg-brand-500 disabled:opacity-50">Add</button>
        </div>
      </div>

      {/* Follow-ups */}
      <div>
        <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Follow-ups ({followUps.length})</h4>
        {followUps.map(fu => (
          <div key={fu.id} className="flex items-center gap-2 py-1.5 border-b border-surface-3 last:border-0">
            <span className={cn('text-sm flex-1', fu.completed ? 'line-through text-gray-600' : 'text-gray-300')}>{fu.text}</span>
            {fu.due_date && <span className={cn('text-xs', isOverdue(fu.due_date) && !fu.completed ? 'text-red-400' : 'text-gray-500')}>{formatDate(fu.due_date)}</span>}
          </div>
        ))}
        <div className="flex gap-2 mt-2">
          <input className="flex-1 bg-surface-3 text-white rounded px-2 py-1 text-xs outline-none" placeholder="New follow-up..." value={fuText} onChange={e => setFuText(e.target.value)} />
          <button onClick={() => addFU.mutate()} disabled={!fuText} className="px-2 py-1 rounded bg-brand-600 text-white text-xs hover:bg-brand-500 disabled:opacity-50">Add</button>
        </div>
      </div>
    </div>
  );
}

// ── Meetings List Tab ──
function MeetingsListTab() {
  const [showForm, setShowForm] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const qc = useQueryClient();

  const { data, isLoading, error } = useQuery({ queryKey: ['meetings', filter], queryFn: () => engine.listMeetings(filter), refetchInterval: 10_000 });
  const deleteMut = useMutation({
    mutationFn: (id: string) => engine.deleteMeeting(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['meetings'] }); qc.invalidateQueries({ queryKey: ['meeting-stats'] }); },
  });
  const statusMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => engine.updateMeeting(id, { status }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['meetings'] }); },
  });

  if (isLoading) return <LoadingState message="Loading meetings..." />;
  if (error) return <ErrorState message="Failed to load meetings" />;
  const meetings = data?.meetings || [];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          {[undefined, 'upcoming', 'completed'].map(f => (
            <button key={f ?? 'all'} onClick={() => setFilter(f)}
              className={cn('px-3 py-1 rounded-lg text-xs font-medium', filter === f ? 'bg-brand-600 text-white' : 'bg-surface-3 text-gray-400 hover:text-white')}>
              {f ?? 'All'}
            </button>
          ))}
        </div>
        <button onClick={() => setShowForm(v => !v)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm hover:bg-brand-500">
          <Plus className="w-4 h-4" /> New Meeting
        </button>
      </div>

      {showForm && <NewMeetingForm onClose={() => setShowForm(false)} />}

      {meetings.length === 0 ? <EmptyState message="No meetings found" /> : (
        <div className="space-y-2">
          {meetings.map(m => (
            <Card key={m.id} className="hover:border-surface-4 transition-colors">
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 cursor-pointer" onClick={() => setExpanded(expanded === m.id ? null : m.id)}>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-medium text-white">{m.title}</h3>
                      <Badge className={CATEGORY_COLORS[m.category] || CATEGORY_COLORS.general}>{m.category}</Badge>
                      <Badge className={m.status === 'upcoming' ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'}>{m.status}</Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{formatDate(m.date)}</span>
                      {m.attendees?.length > 0 && <span className="flex items-center gap-1"><Users className="w-3 h-3" />{m.attendees.length}</span>}
                      <span className="flex items-center gap-1"><ListTodo className="w-3 h-3" />{m.action_items_done || 0}/{m.action_item_count || 0}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {m.status === 'upcoming' && (
                      <button onClick={() => statusMut.mutate({ id: m.id, status: 'completed' })} className="p-1 rounded text-gray-500 hover:text-green-400" title="Mark completed">
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    )}
                    <button onClick={() => deleteMut.mutate(m.id)} className="p-1 rounded text-gray-500 hover:text-red-400" title="Delete">
                      <Trash2 className="w-4 h-4" />
                    </button>
                    {expanded === m.id ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
                  </div>
                </div>
                {expanded === m.id && <MeetingDetail meeting={m} />}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Action Items Tab ──
function ActionItemsTab() {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ['pending-actions'], queryFn: engine.getPendingActions, refetchInterval: 10_000 });
  const toggle = useMutation({
    mutationFn: (item: ActionItem) => engine.updateActionItem(item.id, { completed: item.completed ? 0 : 1 }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['pending-actions'] }); qc.invalidateQueries({ queryKey: ['meeting-stats'] }); },
  });

  if (isLoading) return <LoadingState message="Loading action items..." />;
  if (error) return <ErrorState message="Failed to load action items" />;
  const actions = data?.actions || [];

  return actions.length === 0 ? <EmptyState message="All caught up! No pending action items." /> : (
    <div className="space-y-1">
      {actions.map(ai => (
        <div key={ai.id} className="flex items-center gap-3 bg-surface-2 rounded-lg p-3 hover:bg-surface-3 transition-colors">
          <button onClick={() => toggle.mutate(ai)} className={cn('w-5 h-5 rounded border flex-shrink-0 flex items-center justify-center', ai.completed ? 'bg-green-500 border-green-500' : 'border-gray-600 hover:border-brand-400')}>
            {ai.completed ? <CheckCircle className="w-4 h-4 text-white" /> : null}
          </button>
          <div className="flex-1 min-w-0">
            <p className={cn('text-sm', ai.completed ? 'line-through text-gray-600' : 'text-gray-200')}>{ai.text}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              From: {ai.meeting_title || ai.meeting_id}
              {ai.assignee && <span className="ml-2">@{ai.assignee}</span>}
            </p>
          </div>
          <Badge className={PRIORITY_COLORS[ai.priority] || ''}>{ai.priority}</Badge>
          {ai.due_date && (
            <span className={cn('text-xs flex-shrink-0', isOverdue(ai.due_date) ? 'text-red-400 font-medium' : 'text-gray-500')}>
              {isOverdue(ai.due_date) && <AlertTriangle className="w-3 h-3 inline mr-1" />}
              {formatDate(ai.due_date)}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Follow-ups Tab ──
function FollowUpsTab() {
  const { data, isLoading, error } = useQuery({ queryKey: ['pending-follow-ups'], queryFn: engine.getPendingFollowUps, refetchInterval: 10_000 });

  if (isLoading) return <LoadingState message="Loading follow-ups..." />;
  if (error) return <ErrorState message="Failed to load follow-ups" />;
  const followUps = data?.follow_ups || [];

  return followUps.length === 0 ? <EmptyState message="No pending follow-ups." /> : (
    <div className="space-y-1">
      {followUps.map(fu => (
        <div key={fu.id} className="flex items-center gap-3 bg-surface-2 rounded-lg p-3">
          <Clock className="w-4 h-4 text-gray-500 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-gray-200">{fu.text}</p>
            <p className="text-xs text-gray-500 mt-0.5">From: {fu.meeting_title || fu.meeting_id}</p>
          </div>
          {fu.due_date && (
            <span className={cn('text-xs flex-shrink-0', isOverdue(fu.due_date) ? 'text-red-400' : 'text-gray-500')}>
              {formatDate(fu.due_date)}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Main Page ──
type Tab = 'meetings' | 'actions' | 'follow-ups';

export default function Meetings() {
  const [tab, setTab] = useState<Tab>('meetings');

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: 'meetings', label: 'Meetings', icon: CalendarCheck },
    { key: 'actions', label: 'Action Items', icon: ListTodo },
    { key: 'follow-ups', label: 'Follow-ups', icon: Clock },
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <CalendarCheck className="w-6 h-6 text-brand-400" />
        <h1 className="text-xl font-bold text-white">Meetings</h1>
      </div>

      <StatsBar />

      <div className="flex gap-1 mb-6 bg-surface-1 p-1 rounded-xl w-fit">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={cn('flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              tab === t.key ? 'bg-surface-3 text-white' : 'text-gray-500 hover:text-gray-300')}>
            <t.icon className="w-4 h-4" />{t.label}
          </button>
        ))}
      </div>

      {tab === 'meetings' && <MeetingsListTab />}
      {tab === 'actions' && <ActionItemsTab />}
      {tab === 'follow-ups' && <FollowUpsTab />}
    </div>
  );
}
