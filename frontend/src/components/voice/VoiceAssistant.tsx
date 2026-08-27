import { useEffect, useState } from 'react';
import { Bot, ChevronRight, LoaderCircle, Mic, Send, Square, Terminal, X } from 'lucide-react';
import { demoVoicePrompts, voiceDemoResponse, voiceDemoTranscript } from '@/data/mockData';
import type { DemoVoicePrompt } from '@/data/mockData';
import { useTypewriter } from '@/components/common/useTypewriter';

type VoiceState = 'idle' | 'listening' | 'thinking' | 'response';

interface VoiceAssistantProps {
  open: boolean;
  onClose: () => void;
}

const waveformBars = [22, 36, 52, 29, 44, 64, 34, 56, 28, 48, 36, 60, 30, 46, 24, 38, 55, 28, 42, 32, 50, 24, 40, 30];

export function VoiceAssistant({ open, onClose }: VoiceAssistantProps) {
  const [state, setState] = useState<VoiceState>('idle');
  const [selectedPrompt, setSelectedPrompt] = useState<DemoVoicePrompt | null>(null);
  const activeResponse = selectedPrompt ? selectedPrompt.response : voiceDemoResponse;
  const responseText = useTypewriter(activeResponse, state === 'response', 12);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        onClose();
      }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (open) onClose();
        else onClose(); // handled upstream
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  useEffect(() => {
    if (!open) {
      const reset = window.setTimeout(() => setState('idle'), 200);
      return () => window.clearTimeout(reset);
    }
  }, [open]);

  useEffect(() => {
    if (state !== 'listening') return;
    const timer = window.setTimeout(() => setState('thinking'), 2200);
    return () => window.clearTimeout(timer);
  }, [state]);

  useEffect(() => {
    if (state !== 'thinking') return;
    const timer = window.setTimeout(() => setState('response'), 1200);
    return () => window.clearTimeout(timer);
  }, [state]);

  if (!open) return null;

  const startListening = () => setState('listening');

  return (
    <>
      <button aria-label="Close voice assistant overlay" onClick={onClose} className="fixed inset-0 z-40 bg-ink-950/50 backdrop-blur-sm transition-opacity" />
      <div className="fixed bottom-5 right-5 z-50 w-[calc(100vw-40px)] max-w-[410px] animate-scale-in overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-elevated dark:border-ink-800 dark:bg-ink-900 sm:bottom-8 sm:right-8">
        {/* Contextual Header */}
        <div className="flex items-center justify-between border-b border-ink-100 px-5 py-4 dark:border-ink-800/80">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-ink-900 text-white shadow-soft dark:bg-accent-600">
              <Bot size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-bold text-ink-950 dark:text-ink-50">Ask TraceIQ</p>
                <span className="rounded-md border border-accent-200 bg-accent-50 px-1.5 py-0.5 font-mono text-[10px] font-bold uppercase tracking-wider text-accent-700 dark:border-accent-800 dark:bg-accent-950 dark:text-accent-300">
                  payments-v2
                </span>
              </div>
              <p className="text-[11px] text-ink-400 dark:text-ink-500">Contextual incident assistant</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="hidden rounded border border-ink-200 bg-ink-50 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-ink-400 dark:border-ink-800 dark:bg-ink-950 dark:text-ink-500 sm:inline-block">
              ESC
            </span>
            <button
              aria-label="Close modal"
              onClick={onClose}
              className="grid h-8 w-8 place-items-center rounded-lg text-ink-400 transition hover:bg-ink-100 hover:text-ink-800 active:scale-95 dark:hover:bg-ink-800 dark:hover:text-ink-200"
            >
              <X size={17} />
            </button>
          </div>
        </div>

        <div className="px-5 pb-5 pt-5">
          {state === 'idle' && (
            <div className="py-4 text-center animate-fade-in">
              <div className="mx-auto mb-3 grid h-14 w-14 place-items-center rounded-full border border-accent-200 bg-accent-50/80 text-accent-600 dark:border-accent-800/80 dark:bg-accent-950/60 dark:text-accent-300">
                <Mic size={24} />
              </div>
              <h3 className="text-base font-bold tracking-tight text-ink-900 dark:text-ink-100">How can I help investigate?</h3>
              <p className="mt-1 text-xs leading-5 text-ink-500 dark:text-ink-400">Ask a question or select an incident suggestion below:</p>

              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {demoVoicePrompts.map((promptItem) => (
                  <button
                    key={promptItem.id}
                    onClick={() => {
                      setSelectedPrompt(promptItem);
                      setState('thinking');
                    }}
                    className="group flex items-center justify-between rounded-xl border border-ink-200 bg-ink-50/60 p-2.5 text-left text-xs font-semibold text-ink-800 transition-all hover:-translate-y-0.5 hover:border-accent-300 hover:bg-white hover:shadow-soft active:scale-[0.98] dark:border-ink-800 dark:bg-ink-950/50 dark:text-ink-200 dark:hover:border-accent-700 dark:hover:bg-ink-900"
                  >
                    <span className="truncate pr-1 group-hover:text-accent-600 dark:group-hover:text-accent-400">{promptItem.label}</span>
                    <Terminal size={13} className="shrink-0 text-accent-600 dark:text-accent-400" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {state === 'listening' && (
            <div className="py-5 text-center animate-fade-in">
              <div className="relative mx-auto mb-5 flex h-16 w-16 items-center justify-center">
                <span className="absolute h-16 w-16 animate-pulse-ring rounded-full bg-accent-400/30 dark:bg-accent-500/25" />
                <span className="absolute h-14 w-14 rounded-full bg-accent-100 dark:bg-accent-950/60" />
                <Mic className="relative text-accent-600 dark:text-accent-400" size={25} />
              </div>
              <p className="text-xs font-bold uppercase tracking-wider text-accent-700 dark:text-accent-300">Listening to Voice Input...</p>
              <div className="mt-5 flex h-10 items-center justify-center gap-1.5">
                {waveformBars.slice(0, 18).map((height, i) => (
                  <span key={i} className="w-1 rounded-full bg-accent-600 animate-wave dark:bg-accent-400" style={{ height: `${height * 0.55}px`, animationDelay: `${i * 0.05}s` }} />
                ))}
              </div>
              <p className="mt-4 text-xs italic leading-5 text-ink-600 dark:text-ink-300">“{selectedPrompt ? selectedPrompt.transcript : voiceDemoTranscript}”</p>
            </div>
          )}

          {state === 'thinking' && (
            <div className="py-7 text-center animate-fade-in">
              <div className="relative mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-ink-950 text-white dark:bg-accent-600 shadow-soft">
                <LoaderCircle size={24} className="animate-spin" />
              </div>
              <p className="text-sm font-bold text-ink-900 dark:text-ink-100">Correlating Signals...</p>
              <p className="mt-1 text-xs text-ink-500 dark:text-ink-400">Analyzing payments-v2 telemetry against commit #a3f892</p>
              <div className="mx-auto mt-4 h-1.5 w-48 overflow-hidden rounded-full bg-ink-100 dark:bg-ink-800">
                <div className="h-full w-3/4 animate-shimmer rounded-full bg-accent-600 dark:bg-accent-500" />
              </div>
            </div>
          )}

          {state === 'response' && (
            <div className="animate-fade-in">
              <div className="rounded-xl border border-accent-200/90 bg-accent-50/70 p-4 dark:border-accent-800/80 dark:bg-accent-950/50">
                <div className="mb-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="grid h-6 w-6 place-items-center rounded-md bg-accent-600 text-white shadow-soft">
                      <Bot size={13} />
                    </span>
                    <p className="text-xs font-bold uppercase tracking-wider text-accent-700 dark:text-accent-300">
                      {selectedPrompt ? selectedPrompt.label : 'TraceIQ Assistant Response'}
                    </p>
                  </div>
                  <span className="font-mono text-[10px] text-ink-400 dark:text-ink-500">89.4% confidence</span>
                </div>
                <p className="text-xs leading-6 text-ink-800 dark:text-ink-100">
                  {responseText}
                  <span className="ml-0.5 inline-block h-3.5 w-0.5 animate-pulse bg-accent-600 align-middle" />
                </p>
              </div>
              <button
                onClick={() => {
                  setSelectedPrompt(null);
                  setState('idle');
                }}
                className="mt-3.5 flex w-full items-center justify-center gap-2 rounded-xl border border-ink-200 bg-white py-2.5 text-xs font-semibold text-ink-700 shadow-soft transition-all hover:bg-ink-50 active:scale-[0.98] dark:border-ink-700 dark:bg-ink-900 dark:text-ink-200 dark:hover:bg-ink-800"
              >
                Ask another question <ChevronRight size={14} />
              </button>
            </div>
          )}

          <div className="mt-3.5 flex items-center gap-2 border-t border-ink-100 pt-3 dark:border-ink-800">
            <button
              aria-label={state === 'listening' ? 'Stop listening' : 'Start listening'}
              onClick={state === 'listening' ? () => setState('thinking') : startListening}
              className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl transition-all active:scale-95 ${
                state === 'listening'
                  ? 'bg-rose-600 text-white hover:bg-rose-700 shadow-soft'
                  : 'bg-ink-950 text-white hover:bg-ink-800 shadow-soft dark:bg-accent-600 dark:hover:bg-accent-500'
              }`}
            >
              {state === 'listening' ? <Square size={16} fill="currentColor" /> : <Mic size={17} />}
            </button>
            <div className="flex h-10 flex-1 items-center justify-between rounded-xl border border-ink-200 bg-ink-50 px-3.5 text-xs text-ink-400 dark:border-ink-800 dark:bg-ink-950 dark:text-ink-500">
              <span>{state === 'response' ? 'Ask a follow-up question...' : 'Tap the mic to speak...'}</span>
              <Send size={14} className="text-ink-300 dark:text-ink-600" />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export function AskTraceButton({ onClick, className = '' }: { onClick: () => void; className?: string }) {
  return (
    <button
      onClick={onClick}
      className={`group flex items-center gap-2 rounded-xl bg-ink-950 px-4 py-2.5 text-xs font-semibold text-white shadow-soft transition-all hover:-translate-y-0.5 hover:bg-ink-800 hover:shadow-card active:scale-[0.97] dark:bg-accent-600 dark:hover:bg-accent-500 ${className}`}
    >
      <span className="grid h-5 w-5 place-items-center rounded-md bg-white/10 transition-transform group-hover:scale-110">
        <Mic size={13} />
      </span>
      <span>Ask TraceIQ</span>
      <span className="ml-1 rounded border border-white/20 px-1 py-0.2 font-mono text-[10px] font-medium text-white/70">
        ⌘K
      </span>
    </button>
  );
}
