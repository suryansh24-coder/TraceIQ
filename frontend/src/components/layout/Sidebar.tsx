import { useState } from 'react';
import {
  AlertTriangle,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Mic,
  Search,
  Settings,
  Terminal,
  X,
} from 'lucide-react';
import { navItems } from '@/data/mockData';
import { Logo } from '@/components/ui';

const iconMap = {
  LayoutDashboard,
  Search,
  AlertTriangle,
  BookOpen,
  Terminal,
  Mic,
  Settings,
};

type IconName = keyof typeof iconMap;

interface SidebarProps {
  currentView: string;
  onNavigate: (view: string) => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({ currentView, onNavigate, mobileOpen, onMobileClose }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  const handleNavigate = (view: string) => {
    onNavigate(view);
    onMobileClose();
  };

  return (
    <>
      {mobileOpen && <button aria-label="Close navigation" className="fixed inset-0 z-40 bg-ink-950/30 lg:hidden" onClick={onMobileClose} />}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-ink-200 bg-white transition-all duration-200 dark:border-ink-800 dark:bg-ink-950 lg:static lg:z-auto lg:translate-x-0 ${
          collapsed ? 'lg:w-[76px]' : 'lg:w-64'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className={`flex h-[72px] items-center border-b border-ink-100 dark:border-ink-800/80 ${collapsed ? 'justify-center px-3' : 'justify-between px-5'}`}>
          <Logo showWordmark={!collapsed} />
          <button
            className="grid h-8 w-8 place-items-center rounded-lg text-ink-400 transition hover:bg-ink-100 hover:text-ink-700 dark:hover:bg-ink-800 dark:hover:text-ink-200 lg:hidden"
            aria-label="Close navigation"
            onClick={onMobileClose}
          >
            <X size={18} />
          </button>
          <button
            className="hidden h-7 w-7 place-items-center rounded-md text-ink-400 transition hover:bg-ink-100 hover:text-ink-700 dark:hover:bg-ink-800 dark:hover:text-ink-200 lg:grid"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={() => setCollapsed((value) => !value)}
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        <nav className={`flex-1 space-y-1 py-5 ${collapsed ? 'px-3' : 'px-3'}`}>
          <p className={`mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-400 dark:text-ink-500 ${collapsed ? 'text-center' : ''}`}>
            {collapsed ? '·' : 'Workspace'}
          </p>
          {navItems.map((item) => {
            const Icon = iconMap[item.icon as IconName];
            const active = currentView === item.id || (item.id === 'overview' && currentView === 'dashboard');
            return (
              <button
                key={item.id}
                onClick={() => handleNavigate(item.id === 'overview' ? 'dashboard' : item.id)}
                title={collapsed ? item.label : undefined}
                className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium transition-all duration-200 ${
                  active
                    ? 'bg-accent-50 text-accent-700 border border-accent-200/70 font-semibold shadow-soft dark:bg-accent-950/60 dark:text-accent-300 dark:border-accent-800/80'
                    : 'border border-transparent text-ink-600 hover:bg-ink-100/60 hover:text-ink-900 hover:translate-x-0.5 dark:text-ink-400 dark:hover:bg-ink-900/60 dark:hover:text-ink-100'
                } ${collapsed ? 'justify-center px-0' : ''}`}
              >
                <Icon size={18} strokeWidth={active ? 2.2 : 1.8} className={active ? 'text-accent-600 dark:text-accent-400' : 'text-ink-400 dark:text-ink-500 group-hover:text-ink-600 dark:group-hover:text-ink-300'} />
                {!collapsed && <span>{item.label}</span>}
                {!collapsed && item.id === 'incidents' && <span className="ml-auto rounded-md border border-rose-200/80 bg-rose-50 px-1.5 py-0.5 text-[10px] font-semibold text-rose-700 dark:border-rose-800/80 dark:bg-rose-950/60 dark:text-rose-300">2</span>}
              </button>
            );
          })}
        </nav>

        <div className={`border-t border-ink-100 dark:border-ink-800/80 p-3 ${collapsed ? 'flex justify-center' : ''}`}>
          <button className={`flex w-full items-center gap-3 rounded-xl p-2 text-left transition hover:bg-ink-100/60 dark:hover:bg-ink-900/60 ${collapsed ? 'justify-center' : ''}`}>
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-accent-200 bg-accent-100 text-xs font-semibold text-accent-800 dark:border-accent-800 dark:bg-accent-950 dark:text-accent-200">RS</div>
            {!collapsed && (
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-ink-800 dark:text-ink-100">Raghav Sharma</p>
                <p className="truncate text-xs text-ink-400 dark:text-ink-500">Engineer</p>
              </div>
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
