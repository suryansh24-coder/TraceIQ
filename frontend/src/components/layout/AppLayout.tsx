import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { Sidebar, TopNav } from '@/components/layout';

interface AppLayoutProps {
  children: ReactNode;
  currentView: string;
  title: string;
  onNavigate: (view: string) => void;
  onAskTrace: () => void;
}

export function AppLayout({ children, currentView, title, onNavigate, onAskTrace }: AppLayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        onAskTrace();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onAskTrace]);

  return (
    <div className="flex min-h-screen bg-ink-50 transition-colors dark:bg-ink-950">
      <Sidebar currentView={currentView} onNavigate={onNavigate} mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopNav title={title} onMenuOpen={() => setMobileOpen(true)} onAskTrace={onAskTrace} />
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
