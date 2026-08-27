import type { Severity, InvestigationStatus } from '@/data/mockData';

const severityConfig: Record<Severity, { label: string; dot: string; text: string; bg: string; border: string }> = {
  critical: {
    label: 'Critical',
    dot: 'bg-rose-500',
    text: 'text-rose-700 dark:text-rose-300',
    bg: 'bg-rose-50/80 dark:bg-rose-950/50',
    border: 'border-rose-200 dark:border-rose-800/80',
  },
  warning: {
    label: 'Warning',
    dot: 'bg-amber-500',
    text: 'text-amber-700 dark:text-amber-300',
    bg: 'bg-amber-50/80 dark:bg-amber-950/50',
    border: 'border-amber-200 dark:border-amber-800/80',
  },
  info: {
    label: 'Info',
    dot: 'bg-accent-600 dark:bg-accent-400',
    text: 'text-accent-700 dark:text-accent-300',
    bg: 'bg-accent-50/80 dark:bg-accent-950/50',
    border: 'border-accent-200 dark:border-accent-800/80',
  },
};

export function SeverityBadge({ severity, className = '' }: { severity: Severity; className?: string }) {
  const c = severityConfig[severity];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${c.bg} ${c.text} ${c.border} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}

const statusConfig: Record<InvestigationStatus, { label: string; text: string; bg: string; border: string; dot: string }> = {
  investigated: {
    label: 'Investigated',
    text: 'text-ink-700 dark:text-ink-300',
    bg: 'bg-ink-100/70 dark:bg-ink-800/60',
    border: 'border-ink-200 dark:border-ink-700',
    dot: 'bg-ink-400 dark:bg-ink-500',
  },
  resolved: {
    label: 'Resolved',
    text: 'text-emerald-700 dark:text-emerald-300',
    bg: 'bg-emerald-50/80 dark:bg-emerald-950/50',
    border: 'border-emerald-200 dark:border-emerald-800/80',
    dot: 'bg-emerald-500',
  },
  investigating: {
    label: 'Investigating',
    text: 'text-amber-800 dark:text-amber-300',
    bg: 'bg-amber-50/80 dark:bg-amber-950/50',
    border: 'border-amber-200 dark:border-amber-800/80',
    dot: 'bg-amber-500',
  },
};

export function StatusPill({ status, className = '' }: { status: InvestigationStatus; className?: string }) {
  const c = statusConfig[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${c.bg} ${c.text} ${c.border} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}

export function LiveStatusBadge({ label = 'Investigating', className = '' }: { label?: string; className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50/80 px-3 py-1 text-xs font-semibold text-amber-800 dark:border-amber-800/80 dark:bg-amber-950/60 dark:text-amber-300 ${className}`}
    >
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
      </span>
      {label}
    </span>
  );
}

export function CompleteStatusBadge({ label = 'Investigation complete', className = '' }: { label?: string; className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50/80 px-3 py-1 text-xs font-semibold text-emerald-800 dark:border-emerald-800/80 dark:bg-emerald-950/60 dark:text-emerald-300 ${className}`}
    >
      <span className="h-2 w-2 rounded-full bg-emerald-500" />
      {label}
    </span>
  );
}

export type TrustCategory = 'observed' | 'analysis' | 'root_cause' | 'recommendation';

const trustConfig: Record<TrustCategory, { label: string; bg: string; text: string; border: string }> = {
  observed: {
    label: 'OBSERVED DATA',
    bg: 'bg-ink-100 dark:bg-ink-800/80',
    text: 'text-ink-700 dark:text-ink-300',
    border: 'border-ink-300/70 dark:border-ink-700',
  },
  analysis: {
    label: 'ANALYSIS SIGNAL',
    bg: 'bg-accent-50 dark:bg-accent-950/70',
    text: 'text-accent-700 dark:text-accent-300',
    border: 'border-accent-200 dark:border-accent-800',
  },
  root_cause: {
    label: 'PRIMARY ROOT CAUSE',
    bg: 'bg-rose-50 dark:bg-rose-950/70',
    text: 'text-rose-700 dark:text-rose-300',
    border: 'border-rose-200 dark:border-rose-800',
  },
  recommendation: {
    label: 'RECOMMENDED ACTION',
    bg: 'bg-emerald-50 dark:bg-emerald-950/70',
    text: 'text-emerald-800 dark:text-emerald-300',
    border: 'border-emerald-200 dark:border-emerald-800',
  },
};

export function TrustTag({ category, className = '' }: { category: TrustCategory; className?: string }) {
  const c = trustConfig[category];
  return (
    <span
      className={`inline-flex items-center rounded border px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider ${c.bg} ${c.text} ${c.border} ${className}`}
    >
      {c.label}
    </span>
  );
}
