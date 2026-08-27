import { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  ArrowUpRight,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleDot,
  Clock3,
  Code2,
  FileText,
  Github,
  GitCommit,
  HelpCircle,
  Info,
  LoaderCircle,
  MessageSquare,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  Terminal,
  Zap,
} from 'lucide-react';
import { Card, SectionHeader } from '@/components/common/Card';
import { CompleteStatusBadge, LiveStatusBadge, TrustTag } from '@/components/common/Badges';
import {
  evidenceCards,
  failureChainEvents,
  humanExplanation,
  initialProgressStages,
  investigationSteps,
  recommendedSteps,
  rootCause,
  rootCauseConfidence,
  rootCauseReasons,
} from '@/data/mockData';
import type { FailureChainEvent, ProgressStage } from '@/data/mockData';
import { AskTraceButton } from '@/components/voice/VoiceAssistant';

interface IncidentProps {
  onBack: () => void;
  onAskTrace: () => void;
}

const evidenceIconMap = { Github, Activity, BookOpen };

const stageLabels = [
  { id: 1, label: 'Collecting signals', detail: 'GitHub, Datadog' },
  { id: 2, label: 'Analyzing logs', detail: 'HTTP 401 stack' },
  { id: 3, label: 'Tracing dependencies', detail: 'payments → auth' },
  { id: 4, label: 'Correlating failures', detail: 'Secret handshake' },
  { id: 5, label: 'Identifying root cause', detail: 'Commit #a3f892' },
  { id: 6, label: 'Generating recommendation', detail: 'Config fix ready' },
];

export function Incident({ onBack, onAskTrace }: IncidentProps) {
  const [running, setRunning] = useState(false);
  const [complete, setComplete] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [stages, setStages] = useState<ProgressStage[]>(initialProgressStages);
  const [showAction, setShowAction] = useState(false);
  const [expandedEvidence, setExpandedEvidence] = useState<string | null>(null);

  const runInvestigation = () => {
    setRunning(true);
    setComplete(false);
    setShowAction(false);
    setActiveStep(0);
    setStages(initialProgressStages.map((stage, index) => ({ ...stage, status: index === 0 ? 'complete' : index === 1 ? 'active' : 'pending' })));
  };

  useEffect(() => {
    if (!running) return;
    if (activeStep >= investigationSteps.length) {
      setRunning(false);
      setComplete(true);
      setStages((items) => items.map((stage) => ({ ...stage, status: 'complete' })));
      return;
    }
    const timer = window.setTimeout(() => {
      const next = activeStep + 1;
      setActiveStep(next);
      setStages((items) => items.map((stage, index) => ({ ...stage, status: index <= Math.min(next + 1, 5) ? 'complete' : index === Math.min(next + 1, 5) + 1 ? 'active' : 'pending' })));
    }, 800);
    return () => window.clearTimeout(timer);
  }, [running, activeStep]);

  const displayedStages = running || complete ? stages : initialProgressStages;

  return (
    <div className="mx-auto max-w-[1440px] px-5 py-8 sm:px-8 lg:px-10 lg:py-10 animate-fade-in">
      {/* 1. INVESTIGATION HEADER */}
      <div className="mb-8 flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between animate-slide-up">
        <div>
          <button
            onClick={onBack}
            className="group mb-4 flex items-center gap-1.5 text-xs font-semibold text-ink-500 transition-colors hover:text-ink-900 active:scale-95 dark:text-ink-400 dark:hover:text-ink-100"
          >
            <ArrowLeft size={14} className="transition-transform group-hover:-translate-x-1" />
            Back to dashboard
          </button>
          <div className="flex flex-wrap items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl border border-rose-200/90 bg-rose-50/90 text-rose-600 shadow-soft dark:border-rose-800/80 dark:bg-rose-950/70 dark:text-rose-400">
              <ShieldAlert size={23} />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2.5">
                <span className="font-mono text-xs font-bold uppercase tracking-wider text-accent-700 dark:text-accent-400">INC-8492</span>
                <span className="text-ink-300 dark:text-ink-700">•</span>
                <h2 className="text-xl font-bold tracking-tight text-ink-950 dark:text-ink-50 sm:text-2xl">Payment API — Authentication Failure</h2>
                {complete ? <CompleteStatusBadge /> : <LiveStatusBadge />}
              </div>
              <p className="mt-1.5 text-sm text-ink-500 dark:text-ink-400">
                Correlating <span className="font-medium text-ink-700 dark:text-ink-300">payments-v2</span> microservice signals after HTTP 401 error spike.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 self-start">
          <div className="hidden flex-col items-end text-xs text-ink-400 dark:text-ink-500 xl:flex">
            <span className="font-medium text-ink-700 dark:text-ink-300">Started 4m ago</span>
            <span>Analysis duration: 1.8s</span>
          </div>
          <button
            onClick={runInvestigation}
            disabled={running}
            className="flex items-center gap-2 rounded-xl border border-ink-200 bg-white px-4 py-2.5 text-xs font-semibold text-ink-800 shadow-soft transition-all hover:-translate-y-0.5 hover:border-ink-300 hover:bg-ink-50 hover:shadow-card active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50 dark:border-ink-700 dark:bg-ink-900 dark:text-ink-200 dark:hover:bg-ink-800"
          >
            <RotateCcw size={15} className={running ? 'animate-spin' : 'transition-transform hover:rotate-90'} />
            {running ? 'Analyzing...' : 'Re-analyze Incident'}
          </button>
          <AskTraceButton onClick={onAskTrace} />
        </div>
      </div>

      {/* 2. INVESTIGATION PROGRESS */}
      <Card className="mb-8 overflow-hidden p-5 sm:p-6 animate-slide-up [animation-delay:100ms] dark:border-ink-800 dark:bg-ink-900">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Activity size={16} className="text-accent-600 dark:text-accent-400" />
              <h3 className="text-sm font-bold text-ink-900 dark:text-ink-100">Telemetry Analysis Engine</h3>
              <TrustTag category="analysis" className="ml-1" />
            </div>
            <p className="mt-1 text-xs text-ink-400 dark:text-ink-500">Correlating code commits, APM metrics, and historical runbooks in real time</p>
          </div>
          <span className="font-mono text-xs font-bold text-accent-700 dark:text-accent-400">
            {complete ? '100% Complete' : running ? `${Math.min(25 + activeStep * 19, 91)}%` : '100% Analysis Ready'}
          </span>
        </div>

        <div className="relative hidden items-start justify-between md:flex">
          <div className="absolute left-[6%] right-[6%] top-4 h-0.5 bg-ink-200 dark:bg-ink-800" />
          <div
            className="absolute left-[6%] top-4 h-0.5 bg-accent-600 transition-all duration-500 ease-out dark:bg-accent-500"
            style={{ width: `${complete ? 88 : running ? Math.min(15 + activeStep * 15, 88) : 88}%` }}
          />
          {stageLabels.map((stg, i) => {
            const isFinished = complete || (!running && i < 5) || (running && i <= activeStep);
            const isActive = running && i === activeStep;
            return (
              <div key={stg.id} className="relative z-10 flex w-1/6 flex-col items-center text-center">
                <div
                  className={`grid h-9 w-9 place-items-center rounded-full border-2 bg-white transition-all duration-300 dark:bg-ink-900 ${
                    isFinished
                      ? 'border-accent-600 bg-accent-600 text-white scale-105 dark:border-accent-500 dark:bg-accent-500'
                      : isActive
                      ? 'border-accent-600 text-accent-600 ring-4 ring-accent-100 scale-110 dark:border-accent-400 dark:text-accent-400 dark:ring-accent-950'
                      : 'border-ink-200 text-ink-300 dark:border-ink-800 dark:text-ink-600'
                  }`}
                >
                  {isFinished ? <Check size={16} strokeWidth={2.5} /> : isActive ? <LoaderCircle size={16} className="animate-spin" /> : <span className="h-2 w-2 rounded-full bg-current" />}
                </div>
                <p className={`mt-3 text-xs font-semibold transition-colors duration-200 ${isFinished || isActive ? 'text-ink-900 dark:text-ink-100' : 'text-ink-400 dark:text-ink-500'}`}>
                  {stg.label}
                </p>
                <p className="mt-0.5 text-[11px] text-ink-400 dark:text-ink-500">{stg.detail}</p>
              </div>
            );
          })}
        </div>
        <div className="space-y-3 md:hidden">
          {stageLabels.map((stg, i) => {
            const isFinished = complete || (!running && i < 5) || (running && i <= activeStep);
            return (
              <div key={stg.id} className="flex items-center gap-3">
                <div className={`grid h-7 w-7 place-items-center rounded-full border-2 transition-all ${isFinished ? 'border-accent-600 bg-accent-600 text-white' : 'border-ink-200 text-ink-300'}`}>
                  {isFinished ? <Check size={13} /> : <span className="h-1.5 w-1.5 rounded-full bg-current" />}
                </div>
                <div className="flex-1">
                  <p className="text-xs font-semibold text-ink-800 dark:text-ink-100">{stg.label}</p>
                  <p className="text-[11px] text-ink-400 dark:text-ink-500">{stg.detail}</p>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {running && (
        <Card className="mb-8 animate-fade-in border-accent-200 bg-accent-50/60 p-4 sm:p-5 shadow-soft dark:border-accent-800/80 dark:bg-accent-950/40">
          <div className="flex items-center gap-3">
            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-accent-600 text-white shadow-soft">
              <LoaderCircle size={16} className="animate-spin" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-accent-900 dark:text-accent-200">{investigationSteps[Math.min(activeStep, investigationSteps.length - 1)].label}</p>
              <p className="mt-0.5 truncate text-xs text-accent-700/80 dark:text-accent-400/80">Correlating GitHub commit #a3f892 with Datadog 401 anomaly logs...</p>
            </div>
          </div>
        </Card>
      )}

      {/* 3. FAILURE CHAIN / TIMELINE */}
      <section className="mb-10 animate-slide-up [animation-delay:150ms]">
        <SectionHeader
          title="Failure-Chain Timeline"
          subtitle="Chronological sequence from baseline traffic to critical outage"
          action={
            <div className="flex items-center gap-2">
              <TrustTag category="observed" />
              <span className="hidden items-center gap-1.5 text-xs text-ink-400 dark:text-ink-500 sm:flex">
                <Clock3 size={14} /> Reconstructed in 1.8s
              </span>
            </div>
          }
        />
        <div className="mt-4 grid gap-3">
          {failureChainEvents.map((evt) => {
            const isRoot = evt.type === 'root_cause';
            const isFail = evt.type === 'failure';
            const isWarn = evt.type === 'warning';

            const badgeStyle = isRoot
              ? 'border-accent-200 bg-accent-50 text-accent-700 dark:border-accent-800 dark:bg-accent-950 dark:text-accent-300'
              : isFail
              ? 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-800 dark:bg-rose-950 dark:text-rose-300'
              : isWarn
              ? 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-300'
              : 'border-ink-200 bg-ink-100 text-ink-600 dark:border-ink-800 dark:bg-ink-800 dark:text-ink-300';

            return (
              <div
                key={evt.id}
                className={`group flex flex-col gap-3 rounded-xl border p-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card sm:flex-row sm:items-center ${
                  isRoot
                    ? 'border-accent-300 bg-accent-50/40 dark:border-accent-800 dark:bg-accent-950/20'
                    : isFail
                    ? 'border-rose-200/90 bg-rose-50/30 dark:border-rose-900/60 dark:bg-rose-950/20'
                    : 'border-ink-200 bg-white dark:border-ink-800 dark:bg-ink-900'
                }`}
              >
                <div className="flex shrink-0 items-center gap-3 sm:w-44">
                  <span className="font-mono text-xs font-semibold text-ink-500 dark:text-ink-400">{evt.time}</span>
                  <span className={`rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${badgeStyle}`}>
                    {evt.typeLabel}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="rounded font-mono text-[11px] font-semibold text-ink-500 dark:text-ink-400">[{evt.service}]</span>
                    <h4 className="truncate text-sm font-semibold text-ink-900 dark:text-ink-100 group-hover:text-accent-600 dark:group-hover:text-accent-400 transition-colors">
                      {evt.title}
                    </h4>
                  </div>
                  <p className="mt-1 text-xs leading-5 text-ink-600 dark:text-ink-400">{evt.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* 4. ROOT CAUSE VISUAL CENTERPIECE & 5. HUMAN EXPLANATION */}
      <div className="mb-10 grid gap-8 xl:grid-cols-[minmax(0,1.2fr)_minmax(380px,0.8fr)] animate-slide-up [animation-delay:200ms]">
        {/* CENTERPIECE ROOT CAUSE CARD */}
        <Card
          className={`relative overflow-hidden border-2 border-accent-300 p-6 sm:p-8 transition-all duration-300 dark:border-accent-700 dark:bg-ink-900 ${
            complete ? 'ring-4 ring-accent-400/20 shadow-elevated animate-scale-in' : 'shadow-card'
          }`}
        >
          <div className="relative">
            <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
              <div>
                <div className="mb-2 flex items-center gap-2">
                  <span className="grid h-7 w-7 place-items-center rounded-lg bg-accent-600 text-white shadow-soft">
                    <ShieldAlert size={15} />
                  </span>
                  <TrustTag category="root_cause" />
                </div>
                <h3 className="text-2xl font-bold tracking-tight text-ink-950 dark:text-ink-50">JWT Secret Key Rotation Mismatch</h3>
              </div>
              <div className="relative grid h-20 w-20 shrink-0 place-items-center self-start sm:self-auto">
                <svg className="absolute inset-0 h-full w-full -rotate-90">
                  <circle cx="40" cy="40" r="34" fill="none" stroke="#e2e8f0" strokeWidth="6" className="dark:stroke-ink-800" />
                  <circle
                    cx="40"
                    cy="40"
                    r="34"
                    fill="none"
                    stroke="#2563eb"
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={`${2 * Math.PI * 34}`}
                    strokeDashoffset={`${2 * Math.PI * 34 * (1 - rootCauseConfidence / 100)}`}
                    className="transition-all duration-1000 ease-out dark:stroke-accent-500"
                  />
                </svg>
                <div className="text-center">
                  <span className="font-mono text-lg font-bold text-ink-950 dark:text-ink-50">{rootCauseConfidence}%</span>
                  <p className="text-[9px] uppercase font-bold text-ink-400 dark:text-ink-500">Confidence</p>
                </div>
              </div>
            </div>

            <p className="text-sm leading-7 text-ink-700 dark:text-ink-200">{rootCause}</p>

            <div className="mt-6 flex flex-wrap items-center gap-2">
              <span className="rounded-md border border-accent-200 bg-accent-50 px-2.5 py-1 font-mono text-xs font-semibold text-accent-700 dark:border-accent-800 dark:bg-accent-950 dark:text-accent-300">
                Target: payments-v2
              </span>
              <span className="rounded-md border border-rose-200 bg-rose-50 px-2.5 py-1 font-mono text-xs font-semibold text-rose-700 dark:border-rose-800 dark:bg-rose-950 dark:text-rose-300">
                Impact: 340% 401 Spike
              </span>
              <span className="rounded-md border border-ink-200 bg-ink-100 px-2.5 py-1 font-mono text-xs font-semibold text-ink-700 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-300">
                Commit: #a3f892
              </span>
            </div>

            <div className="mt-7 border-t border-ink-100 dark:border-ink-800 pt-5">
              <p className="mb-3 text-xs font-bold uppercase tracking-wider text-ink-800 dark:text-ink-200">Correlated Technical Evidence</p>
              <ul className="space-y-3">
                {rootCauseReasons.map((reason) => (
                  <li key={reason} className="flex items-start gap-3 text-sm text-ink-600 dark:text-ink-300">
                    <span className="mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full bg-accent-100 text-accent-700 dark:bg-accent-950 dark:text-accent-300 dark:border dark:border-accent-800">
                      <Check size={10} strokeWidth={3} />
                    </span>
                    {reason}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-6 flex items-center gap-2 text-xs text-ink-400 dark:text-ink-500">
              <CircleDot size={14} className="text-accent-500 animate-pulse" />
              <span>Correlated from 7 telemetry signals across GitHub, Datadog & internal knowledge base.</span>
            </div>
          </div>
        </Card>

        {/* 5. HUMAN EXPLANATION CARD ("What does this mean?") */}
        <Card className="flex flex-col border-accent-200/80 bg-accent-50/40 p-6 sm:p-7 dark:border-accent-800/80 dark:bg-accent-950/20">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HelpCircle size={18} className="text-accent-600 dark:text-accent-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-accent-700 dark:text-accent-400">Human Explanation</h3>
            </div>
            <TrustTag category="analysis" />
          </div>
          <h4 className="text-lg font-semibold tracking-tight text-ink-950 dark:text-ink-50">What does this mean for a developer?</h4>
          <p className="mt-3 text-sm leading-6 text-ink-700 dark:text-ink-300">{humanExplanation}</p>

          <div className="mt-6 space-y-3 rounded-xl border border-accent-200/70 bg-white/80 p-4 dark:border-accent-900/60 dark:bg-ink-900/80">
            <div className="flex items-start gap-2.5 text-xs text-ink-700 dark:text-ink-300">
              <Info size={15} className="mt-0.5 shrink-0 text-accent-600 dark:text-accent-400" />
              <span>
                <strong>Key Takeaway:</strong> `auth-service` rotated its JWT key in commit #a3f892, but `payments-v2` environment secrets were not updated in sync.
              </span>
            </div>
            <div className="flex items-start gap-2.5 text-xs text-ink-700 dark:text-ink-300">
              <CheckCircle2 size={15} className="mt-0.5 shrink-0 text-emerald-500" />
              <span>No database corruption or customer credit card data loss detected.</span>
            </div>
          </div>

          <div className="mt-auto pt-6">
            <button
              onClick={onAskTrace}
              className="group flex w-full items-center justify-center gap-2 rounded-xl border border-accent-300 bg-white py-2.5 text-xs font-semibold text-accent-700 shadow-soft transition-all hover:bg-accent-50 active:scale-[0.98] dark:border-accent-800 dark:bg-ink-900 dark:text-accent-300 dark:hover:bg-accent-950"
            >
              <MessageSquare size={14} className="text-accent-600 dark:text-accent-400" />
              Ask TraceIQ to explain this further
              <ArrowUpRight size={13} className="transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </button>
          </div>
        </Card>
      </div>

      {/* 6. RECOMMENDED SOLUTION */}
      <section className="mb-10 animate-slide-up [animation-delay:250ms]">
        <Card className="border-ink-200 p-6 sm:p-8 dark:border-ink-800 dark:bg-ink-900">
          <div className="mb-6 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <div className="mb-2 flex items-center gap-2">
                <Zap size={16} className="text-amber-500" />
                <TrustTag category="recommendation" />
              </div>
              <h3 className="text-xl font-bold tracking-tight text-ink-950 dark:text-ink-50">Recommended Solution Steps</h3>
            </div>
            <span className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800 dark:border-amber-800/80 dark:bg-amber-950/60 dark:text-amber-300 self-start sm:self-auto">
              High Impact • Resolution Ready
            </span>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {recommendedSteps.map((step, idx) => (
              <div
                key={step}
                className="flex flex-col justify-between rounded-xl border border-ink-200 bg-ink-50/50 p-4 transition-all hover:border-ink-300 hover:bg-white hover:shadow-soft dark:border-ink-800 dark:bg-ink-950/60 dark:hover:border-ink-700 dark:hover:bg-ink-900"
              >
                <div>
                  <div className="mb-3 flex items-center justify-between">
                    <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-accent-600 font-mono text-xs font-bold text-white shadow-soft">
                      {idx + 1}
                    </span>
                    <span className="text-[10px] font-semibold uppercase text-ink-400 dark:text-ink-500">Step {idx + 1}</span>
                  </div>
                  <p className="text-xs font-semibold leading-5 text-ink-800 dark:text-ink-200">{step}</p>
                </div>
                <p className="mt-4 text-[11px] text-ink-400 dark:text-ink-500">Why: Restores secret sync between payments & auth services.</p>
              </div>
            ))}
          </div>

          <div className="mt-8 flex flex-wrap items-center gap-3 border-t border-ink-100 pt-5 dark:border-ink-800">
            <button
              onClick={() => setShowAction(true)}
              className="flex items-center gap-2 rounded-xl bg-accent-600 px-4 py-2.5 text-xs font-semibold text-white shadow-soft transition-all hover:-translate-y-0.5 hover:bg-accent-700 hover:shadow-card active:scale-[0.97] dark:bg-accent-600 dark:hover:bg-accent-500"
            >
              <ArrowUpRight size={15} />
              Apply Fix Configuration Preview
            </button>
            <button
              onClick={onAskTrace}
              className="flex items-center gap-2 rounded-xl border border-ink-200 bg-white px-4 py-2.5 text-xs font-semibold text-ink-700 transition-all hover:bg-ink-50 active:scale-[0.97] dark:border-ink-700 dark:bg-ink-900 dark:text-ink-200 dark:hover:bg-ink-800"
            >
              <MessageSquare size={15} />
              Ask Assistant
            </button>
          </div>

          {showAction && (
            <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/90 p-4 text-xs leading-6 text-emerald-900 animate-slide-up dark:border-emerald-800/80 dark:bg-emerald-950/70 dark:text-emerald-300">
              <div className="flex items-center justify-between mb-2">
                <strong className="font-semibold text-emerald-950 dark:text-emerald-200">Next Action Queued: Secret deployment PR draft created (#PR-3841)</strong>
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">payments-v2 / config.env</span>
              </div>
              <div className="overflow-x-auto rounded-lg bg-ink-950 p-3 font-mono text-[11px] text-ink-200 dark:bg-ink-950">
                <p className="text-rose-400">- AUTH_SECRET_KEY = "v1_legacy_secret_44012"</p>
                <p className="text-emerald-400">+ AUTH_SECRET_KEY = "v2_secret_key_9981a_rotated"</p>
              </div>
              <p className="mt-2 text-[11px] text-emerald-800 dark:text-emerald-300">
                Credentials verified against active `auth-service` vault. Ready to merge and auto-deploy to production pod cluster.
              </p>
            </div>
          )}
        </Card>
      </section>

      {/* 7. EVIDENCE & CORRELATED TELEMETRY */}
      <section className="mb-8 animate-slide-up [animation-delay:300ms]">
        <SectionHeader
          title="Correlated Telemetry & Evidence"
          subtitle="Click any evidence card to inspect raw commit diffs and telemetry logs"
          action={<TrustTag category="observed" />}
        />
        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          {evidenceCards.map((evidence) => {
            const Icon = evidenceIconMap[evidence.id === 'github' ? 'Github' : evidence.id === 'monitoring' ? 'Activity' : 'BookOpen'];
            const isExpanded = expandedEvidence === evidence.id;
            const accent =
              evidence.status === 'critical'
                ? { icon: 'border border-rose-200/80 bg-rose-50/80 text-rose-600 dark:border-rose-800/80 dark:bg-rose-950/60 dark:text-rose-400', dot: 'bg-rose-500', text: 'text-rose-700 dark:text-rose-300' }
                : evidence.status === 'warning'
                ? { icon: 'border border-amber-200/80 bg-amber-50/80 text-amber-600 dark:border-amber-800/80 dark:bg-amber-950/60 dark:text-amber-400', dot: 'bg-amber-500', text: 'text-amber-700 dark:text-amber-300' }
                : { icon: 'border border-accent-200/80 bg-accent-50/80 text-accent-700 dark:border-accent-800/80 dark:bg-accent-950/60 dark:text-accent-300', dot: 'bg-accent-600 dark:bg-accent-400', text: 'text-accent-700 dark:text-accent-300' };

            return (
              <Card
                key={evidence.id}
                className="group flex flex-col p-5 transition-all duration-250 hover:-translate-y-1 hover:border-ink-300 hover:shadow-card dark:border-ink-800 dark:bg-ink-900 dark:hover:border-ink-700"
              >
                <div className="mb-5 flex items-start justify-between">
                  <div className={`grid h-10 w-10 place-items-center rounded-xl transition-transform duration-200 group-hover:scale-110 ${accent.icon}`}>
                    <Icon size={19} />
                  </div>
                  <span className={`flex items-center gap-1.5 text-[11px] font-semibold ${accent.text}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${accent.dot}`} />
                    {evidence.statusLabel}
                  </span>
                </div>
                <h4 className="text-sm font-semibold capitalize text-ink-900 group-hover:text-accent-600 dark:text-ink-100 dark:group-hover:text-accent-400 transition-colors">
                  {evidence.kind}
                </h4>
                <p className="mt-1 text-xs text-ink-400 dark:text-ink-500">{evidence.timestamp}</p>
                <ul className="mt-4 space-y-2.5 border-t border-ink-100 pt-4 dark:border-ink-800">
                  {evidence.points.map((point) => (
                    <li key={point} className="flex items-start gap-2.5 text-xs leading-5 text-ink-600 dark:text-ink-300">
                      <Check size={14} className="mt-0.5 shrink-0 text-emerald-500" />
                      {point}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => setExpandedEvidence(isExpanded ? null : evidence.id)}
                  className="mt-5 flex items-center justify-between rounded-lg border border-ink-200 bg-ink-50/50 px-3 py-2 text-xs font-semibold text-ink-700 transition hover:bg-white dark:border-ink-800 dark:bg-ink-950/60 dark:text-ink-300 dark:hover:bg-ink-900"
                >
                  <span>{isExpanded ? 'Hide raw evidence' : 'Inspect raw telemetry'}</span>
                  {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>

                {isExpanded && (
                  <div className="mt-3 rounded-lg border border-ink-200 bg-ink-950 p-3 font-mono text-[11px] leading-5 text-ink-200 animate-slide-up dark:border-ink-800">
                    {evidence.id === 'github' && (
                      <p className="text-emerald-400">+ AUTH_SECRET_KEY = "v2_secret_9981a"<br />- AUTH_SECRET_KEY = "v1_secret_4421b"<br /><span className="text-ink-500">commit #a3f892 (auth-service)</span></p>
                    )}
                    {evidence.id === 'monitoring' && (
                      <p className="text-rose-400">[14:24:15 UTC] POST /v2/charges 401 Unauthorized<br />InvalidSignatureError: JWT signature verification failed<br /><span className="text-ink-500">rate: 142.8 req/sec</span></p>
                    )}
                    {evidence.id === 'knowledge' && (
                      <p className="text-accent-300">Runbook RB-104: Authentication secret key rotation standard procedure.<br /><span className="text-ink-500">Match score: 94%</span></p>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </section>

      {/* FOOTER METRICS SUMMARY */}
      <div className="grid gap-4 sm:grid-cols-3 animate-slide-up [animation-delay:350ms]">
        <Card className="group flex items-center gap-3 p-4 transition-all duration-250 hover:-translate-y-1 hover:border-ink-300 hover:shadow-card dark:border-ink-800 dark:bg-ink-900 dark:hover:border-ink-700">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-ink-100 text-ink-600 transition-transform duration-200 group-hover:scale-110 dark:bg-ink-800 dark:text-ink-300">
            <GitCommit size={17} />
          </div>
          <div>
            <p className="text-xs font-semibold text-ink-800 group-hover:text-accent-600 dark:text-ink-100 dark:group-hover:text-accent-400 transition-colors">3 commits correlated</p>
            <p className="mt-0.5 text-[11px] text-ink-400 dark:text-ink-500">github.com/traceiq/payments</p>
          </div>
        </Card>
        <Card className="group flex items-center gap-3 p-4 transition-all duration-250 hover:-translate-y-1 hover:border-ink-300 hover:shadow-card dark:border-ink-800 dark:bg-ink-900 dark:hover:border-ink-700">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-ink-100 text-ink-600 transition-transform duration-200 group-hover:scale-110 dark:bg-ink-800 dark:text-ink-300">
            <Terminal size={17} />
          </div>
          <div>
            <p className="text-xs font-semibold text-ink-800 group-hover:text-accent-600 dark:text-ink-100 dark:group-hover:text-accent-400 transition-colors">1 runbook matched</p>
            <p className="mt-0.5 text-[11px] text-ink-400 dark:text-ink-500">RB-104 Payment auth</p>
          </div>
        </Card>
        <Card className="group flex items-center gap-3 p-4 transition-all duration-250 hover:-translate-y-1 hover:border-ink-300 hover:shadow-card dark:border-ink-800 dark:bg-ink-900 dark:hover:border-ink-700">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-ink-100 text-ink-600 transition-transform duration-200 group-hover:scale-110 dark:bg-ink-800 dark:text-ink-300">
            <FileText size={17} />
          </div>
          <div>
            <p className="text-xs font-semibold text-ink-800 group-hover:text-accent-600 dark:text-ink-100 dark:group-hover:text-accent-400 transition-colors">2 postmortems found</p>
            <p className="mt-0.5 text-[11px] text-ink-400 dark:text-ink-500">Similar credential issues</p>
          </div>
        </Card>
      </div>
    </div>
  );
}
