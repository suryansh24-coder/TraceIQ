import { useState } from 'react';
import { ArrowUpRight, Bot, ChevronRight, Clock3, GitBranch, Mic, MoreHorizontal, Search, ShieldAlert, Sparkles, Zap } from 'lucide-react';
import { Card, SectionHeader, SeverityBadge, StatusPill, TrustTag } from '@/components/ui';
import { examplePrompt, recentInvestigations, systemStats } from '@/data/mockData';
import { AskTraceButton } from '@/components/voice';

interface DashboardProps {
  onInvestigate: (prompt?: string) => void;
  onAskTrace: () => void;
}

export function Dashboard({ onInvestigate, onAskTrace }: DashboardProps) {
  const [prompt, setPrompt] = useState('');

  const submit = () => {
    if (prompt.trim()) onInvestigate(prompt.trim());
  };

  return (
    <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-10 lg:py-10 animate-fade-in">
      <div className="mb-9 flex flex-col justify-between gap-5 sm:flex-row sm:items-end animate-slide-up">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-accent-600 dark:text-accent-400">Monday, October 23, 2024</p>
          <h2 className="text-2xl font-bold tracking-tight text-ink-950 dark:text-ink-50 sm:text-3xl">Good afternoon, Raghav</h2>
          <p className="mt-2 text-sm text-ink-500 dark:text-ink-400 sm:text-base">Investigate engineering incidents with context, evidence, and AI.</p>
        </div>
        <AskTraceButton onClick={onAskTrace} />
      </div>

      {/* Hero Investigation Prompt */}
      <Card className="relative overflow-hidden border border-ink-300 bg-white p-6 sm:p-8 animate-slide-up [animation-delay:100ms] dark:border-ink-800 dark:bg-ink-900 shadow-soft">
        <div className="relative">
          <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
            <div>
              <div className="mb-3 flex items-center gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-lg bg-ink-900 text-white dark:bg-accent-600 shadow-soft">
                  <Search size={14} />
                </span>
                <TrustTag category="analysis" />
              </div>
              <h3 className="text-xl font-bold tracking-tight text-ink-950 dark:text-ink-50 sm:text-2xl">Correlated Incident Investigation</h3>
              <p className="mt-1.5 max-w-xl text-sm leading-6 text-ink-600 dark:text-ink-300">
                Enter an API signature, endpoint, or error log snippet. TraceIQ correlates telemetry metrics, deployment commits, and matching runbooks.
              </p>
            </div>
            <div className="hidden rounded-xl border border-emerald-200 bg-emerald-50/90 px-3.5 py-2 text-xs font-semibold text-emerald-900 dark:border-emerald-800/80 dark:bg-emerald-950/70 dark:text-emerald-300 sm:flex sm:items-center sm:gap-2 self-start">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Workspace Healthy • 24 APIs Monitored</span>
            </div>
          </div>

          <div className="rounded-xl border border-ink-300 bg-white p-2 shadow-soft transition-all duration-200 focus-within:border-accent-500 focus-within:ring-4 focus-within:ring-accent-100 dark:border-ink-700 dark:bg-ink-950 dark:focus-within:border-accent-400 dark:focus-within:ring-accent-900/60 sm:flex sm:items-center">
            <input
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              onKeyDown={(event) => { if (event.key === 'Enter') submit(); }}
              placeholder="Describe an API failure or ask TraceIQ a question..."
              className="h-11 min-w-0 flex-1 bg-transparent px-3 text-sm text-ink-900 outline-none placeholder:text-ink-400 dark:text-ink-100 dark:placeholder:text-ink-500 font-sans"
            />
            <div className="flex items-center gap-2 px-1.5 pb-1.5 sm:pb-0">
              <button
                onClick={onAskTrace}
                aria-label="Use voice input"
                className="grid h-10 w-10 place-items-center rounded-lg text-ink-500 transition hover:bg-ink-100/70 hover:text-ink-900 active:scale-95 dark:text-ink-400 dark:hover:bg-ink-800 dark:hover:text-ink-100"
              >
                <Mic size={18} />
              </button>
              <button
                onClick={submit}
                disabled={!prompt.trim()}
                className="flex h-10 items-center gap-2 rounded-lg bg-accent-600 px-4 text-sm font-semibold text-white shadow-soft transition-all hover:-translate-y-0.5 hover:bg-accent-700 hover:shadow-card active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-40 dark:bg-accent-600 dark:hover:bg-accent-500"
              >
                Investigate <ArrowUpRight size={16} />
              </button>
            </div>
          </div>

          <button
            onClick={() => { setPrompt(examplePrompt); onInvestigate(examplePrompt); }}
            className="group mt-3.5 flex max-w-full items-center gap-2 truncate px-1 text-left text-xs text-ink-500 transition hover:text-accent-700 dark:text-ink-400 dark:hover:text-accent-400"
          >
            <span className="shrink-0 font-semibold text-ink-700 dark:text-ink-300 group-hover:text-accent-700 dark:group-hover:text-accent-400">Try an example</span>
            <span className="truncate">“{examplePrompt}”</span>
            <ChevronRight size={14} className="shrink-0 transition-transform group-hover:translate-x-1" />
          </button>
        </div>
      </Card>

      <div className="mt-10 grid gap-8 xl:grid-cols-[minmax(0,1.45fr)_minmax(330px,0.75fr)] animate-slide-up [animation-delay:200ms]">
        <section>
          <SectionHeader
            title="Recent Investigations"
            subtitle="Latest correlated incident analyses"
            action={
              <button className="group flex items-center gap-1 text-xs font-semibold text-accent-600 transition hover:text-accent-800 dark:text-accent-400 dark:hover:text-accent-300">
                View all <ChevronRight size={14} className="transition-transform group-hover:translate-x-1" />
              </button>
            }
          />
          <div className="mt-4 space-y-3">
            {recentInvestigations.map((item, index) => (
              <button
                key={item.id}
                onClick={() => onInvestigate(examplePrompt)}
                className={`group flex w-full items-center gap-4 rounded-xl border p-4 text-left shadow-soft transition-all duration-250 hover:-translate-y-1 hover:shadow-card active:scale-[0.99] sm:p-5 ${
                  index === 0
                    ? 'border-2 border-rose-300/90 bg-rose-50/20 dark:border-rose-800 dark:bg-rose-950/30'
                    : 'border-ink-200 bg-white dark:border-ink-800 dark:bg-ink-900'
                }`}
              >
                <div
                  className={`hidden h-10 w-10 shrink-0 place-items-center rounded-xl border sm:grid transition-transform duration-200 group-hover:scale-110 ${
                    item.severity === 'critical'
                      ? 'border-rose-200/80 bg-rose-50/80 text-rose-600 dark:border-rose-800/80 dark:bg-rose-950/60 dark:text-rose-400'
                      : 'border-amber-200/80 bg-amber-50/80 text-amber-600 dark:border-amber-800/80 dark:bg-amber-950/60 dark:text-amber-400'
                  }`}
                >
                  <ShieldAlert size={19} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="truncate text-sm font-bold text-ink-950 group-hover:text-accent-600 dark:text-ink-50 dark:group-hover:text-accent-400 transition-colors">
                      {item.service}
                    </h4>
                    <SeverityBadge severity={item.severity} />
                  </div>
                  <p className="mt-1 truncate text-xs text-ink-500 dark:text-ink-400">{item.title}</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="hidden items-end gap-1.5 sm:flex sm:flex-col">
                    <span className="text-xs text-ink-400 dark:text-ink-500">{item.timeAgo}</span>
                    <StatusPill status={item.status} />
                  </div>
                  {index === 0 ? (
                    <span className="flex items-center gap-1.5 rounded-lg bg-accent-600 px-3 py-1.5 text-xs font-semibold text-white shadow-soft transition-transform group-hover:scale-105 dark:bg-accent-600">
                      Investigate <ArrowUpRight size={14} />
                    </span>
                  ) : (
                    <ChevronRight size={17} className="shrink-0 text-ink-300 transition-all duration-200 group-hover:translate-x-1 group-hover:text-accent-600 dark:text-ink-600 dark:group-hover:text-accent-400" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </section>

        <section>
          <SectionHeader
            title="System Overview"
            subtitle="Live telemetry signals"
            action={
              <button className="grid h-8 w-8 place-items-center rounded-lg text-ink-400 transition hover:bg-ink-100 hover:text-ink-700 active:scale-95 dark:text-ink-500 dark:hover:bg-ink-800 dark:hover:text-ink-200" aria-label="More options">
                <MoreHorizontal size={17} />
              </button>
            }
          />
          <Card className="mt-4 overflow-hidden border-ink-200 dark:border-ink-800">
            <div className="grid grid-cols-2 divide-x divide-y divide-ink-100 dark:divide-ink-800">
              {systemStats.map((stat, i) => (
                <div key={stat.label} className="p-4 sm:p-5 transition-colors duration-200 hover:bg-ink-50/50 dark:hover:bg-ink-800/30">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-xs font-semibold text-ink-500 dark:text-ink-400">{stat.label}</span>
                    <span className={`h-1.5 w-1.5 rounded-full ${i === 1 ? 'bg-amber-500' : 'bg-emerald-500'}`} />
                  </div>
                  <p className="text-2xl font-bold tracking-tight text-ink-950 dark:text-ink-50">{stat.value}</p>
                  <p className="mt-1 text-[11px] text-ink-400 dark:text-ink-500">{stat.hint}</p>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-3 border-t border-ink-100 bg-ink-50/70 px-5 py-3.5 dark:border-ink-800 dark:bg-ink-950/60">
              <div className="grid h-7 w-7 place-items-center rounded-lg border border-emerald-200/80 bg-emerald-50 text-emerald-700 dark:border-emerald-800/80 dark:bg-emerald-950/60 dark:text-emerald-300">
                <Zap size={14} />
              </div>
              <div>
                <p className="text-xs font-semibold text-ink-800 dark:text-ink-200">All Core Systems Operational</p>
                <p className="text-[11px] text-ink-400 dark:text-ink-500">Last telemetry check: 12 seconds ago</p>
              </div>
              <div className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            </div>
          </Card>
        </section>
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-3 animate-slide-up [animation-delay:300ms]">
        {[
          { icon: GitBranch, title: 'GitHub Activity', text: '14 commits analyzed today', color: 'text-accent-700 dark:text-accent-300 bg-accent-50/80 dark:bg-accent-950/60 border-accent-200/70 dark:border-accent-800/80' },
          { icon: ActivityIcon, title: 'Monitoring Signals', text: '24 APIs reporting normally', color: 'text-emerald-700 dark:text-emerald-300 bg-emerald-50/80 dark:bg-emerald-950/60 border-emerald-200/70 dark:border-emerald-800/80' },
          { icon: Bot, title: 'AI Investigations', text: '18 analyses completed today', color: 'text-amber-800 dark:text-amber-300 bg-amber-50/80 dark:bg-amber-950/60 border-amber-200/70 dark:border-amber-800/80' },
        ].map(({ icon: Icon, title, text, color }) => (
          <Card key={title} className="group flex items-center gap-4 p-4 transition-all duration-250 hover:-translate-y-1 hover:border-ink-300 hover:shadow-card dark:hover:border-ink-700">
            <div className={`grid h-10 w-10 place-items-center rounded-xl border transition-transform duration-200 group-hover:scale-110 ${color}`}>
              <Icon size={18} />
            </div>
            <div>
              <p className="text-sm font-semibold text-ink-800 group-hover:text-accent-600 dark:text-ink-100 dark:group-hover:text-accent-400 transition-colors">{title}</p>
              <p className="mt-1 text-xs text-ink-500 dark:text-ink-400">{text}</p>
            </div>
            <Clock3 size={15} className="ml-auto text-ink-300 group-hover:text-ink-500 dark:text-ink-600 dark:group-hover:text-ink-400 transition-colors" />
          </Card>
        ))}
      </div>
    </div>
  );
}

function ActivityIcon(props: { size?: number }) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width={props.size ?? 24} height={props.size ?? 24}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>;
}
