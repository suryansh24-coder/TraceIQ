import { useEffect, useState } from 'react';
import { Bell, ChevronDown, Menu, Moon, Search, Sun, Terminal } from 'lucide-react';

interface TopNavProps {
  title: string;
  onMenuOpen: () => void;
  onAskTrace: () => void;
}

export function TopNav({ title, onMenuOpen, onAskTrace }: TopNavProps) {
  const [dark, setDark] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('traceiq-theme');
      if (saved) return saved === 'dark';
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('traceiq-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('traceiq-theme', 'light');
    }
  }, [dark]);

  const toggleTheme = () => setDark((prev) => !prev);

  return (
    <header className="sticky top-0 z-30 flex h-[72px] items-center justify-between border-b border-ink-200 bg-white/95 px-5 backdrop-blur-md transition-colors dark:border-ink-800 dark:bg-ink-950/90 sm:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <button
          aria-label="Open navigation"
          onClick={onMenuOpen}
          className="grid h-9 w-9 place-items-center rounded-lg text-ink-500 transition hover:bg-ink-100 focus-visible:ring-2 focus-visible:ring-accent-500/70 focus-visible:outline-none dark:text-ink-400 dark:hover:bg-ink-800 lg:hidden"
        >
          <Menu size={20} />
        </button>
        <div className="flex items-center gap-2">
          <h1 className="truncate text-sm font-semibold text-ink-800 dark:text-ink-100 sm:text-base">{title}</h1>
          <span className="hidden text-ink-300 dark:text-ink-700 sm:inline">/</span>
          <span className="hidden text-sm text-ink-400 dark:text-ink-500 sm:inline">Workspace</span>
        </div>
      </div>
      <div className="flex items-center gap-1.5 sm:gap-3">
        <button
          onClick={onAskTrace}
          className="hidden items-center gap-2 rounded-lg border border-accent-200/80 bg-accent-50/80 px-3 py-1.5 text-xs font-semibold text-accent-700 transition-all hover:border-accent-300 hover:bg-accent-100 focus-visible:ring-2 focus-visible:ring-accent-500/70 focus-visible:outline-none active:scale-[0.98] dark:border-accent-800/80 dark:bg-accent-950/50 dark:text-accent-300 dark:hover:bg-accent-900/60 sm:flex"
        >
          <Terminal size={14} className="text-accent-600 dark:text-accent-400" />
          Ask TraceIQ
          <span className="rounded border border-accent-200 bg-white px-1 py-0.5 text-[10px] font-medium text-accent-600 shadow-soft dark:border-accent-800 dark:bg-ink-900 dark:text-accent-300">⌘K</span>
        </button>
        <button
          aria-label="Search"
          className="grid h-9 w-9 place-items-center rounded-lg text-ink-500 transition hover:bg-ink-100/60 hover:text-ink-800 focus-visible:ring-2 focus-visible:ring-accent-500/70 focus-visible:outline-none dark:text-ink-400 dark:hover:bg-ink-800/60 dark:hover:text-ink-100"
        >
          <Search size={18} />
        </button>
        <button
          onClick={toggleTheme}
          title={dark ? 'Switch to Light theme' : 'Switch to Dark theme'}
          aria-label="Toggle theme"
          className="grid h-9 w-9 place-items-center rounded-lg text-ink-500 transition-all hover:bg-ink-100/70 hover:text-ink-900 focus-visible:ring-2 focus-visible:ring-accent-500/70 focus-visible:outline-none active:scale-90 dark:text-ink-400 dark:hover:bg-ink-800/70 dark:hover:text-ink-100"
        >
          {dark ? <Sun size={18} className="text-amber-400 transition-transform hover:rotate-45" /> : <Moon size={18} className="transition-transform hover:-rotate-12" />}
        </button>
        <button
          aria-label="Notifications"
          className="relative grid h-9 w-9 place-items-center rounded-lg text-ink-500 transition hover:bg-ink-100/60 hover:text-ink-800 focus-visible:ring-2 focus-visible:ring-accent-500/70 focus-visible:outline-none dark:text-ink-400 dark:hover:bg-ink-800/60 dark:hover:text-ink-100"
        >
          <Bell size={18} />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-accent-600 ring-2 ring-white dark:ring-ink-950" />
        </button>
        <button
          aria-label="Profile menu"
          className="ml-1 flex items-center gap-2 rounded-lg p-1 transition hover:bg-ink-100/60 focus-visible:ring-2 focus-visible:ring-accent-500/70 focus-visible:outline-none dark:hover:bg-ink-800/60"
        >
          <div className="grid h-8 w-8 place-items-center rounded-full border border-accent-200 bg-accent-100 text-[10px] font-bold text-accent-800 dark:border-accent-800 dark:bg-accent-950 dark:text-accent-200">RS</div>
          <ChevronDown size={14} className="hidden text-ink-400 dark:text-ink-500 sm:block" />
        </button>
      </div>
    </header>
  );
}
