import { useEffect, useState } from 'react';
import { AppLayout, EmptyView } from '@/components/layout';
import { VoiceAssistant } from '@/components/voice';
import { Dashboard, Incident, Login } from '@/pages';

function App() {
  const [view, setView] = useState('dashboard');
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [signedIn, setSignedIn] = useState(true);

  useEffect(() => {
    const handleShortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setVoiceOpen(true);
      }
      if (event.key === 'Escape') setVoiceOpen(false);
    };
    window.addEventListener('keydown', handleShortcut);
    return () => window.removeEventListener('keydown', handleShortcut);
  }, []);

  if (!signedIn) return <Login onSignIn={() => { setSignedIn(true); setView('dashboard'); }} />;

  const pageTitle = view === 'dashboard' ? 'Overview' : view === 'investigate' ? 'Incident investigation' : view[0].toUpperCase() + view.slice(1);

  const content = view === 'dashboard' ? (
    <Dashboard onInvestigate={() => setView('investigate')} onAskTrace={() => setVoiceOpen(true)} />
  ) : view === 'investigate' ? (
    <Incident onBack={() => setView('dashboard')} onAskTrace={() => setVoiceOpen(true)} />
  ) : (
    <EmptyView title={pageTitle} />
  );

  return (
    <>
      <AppLayout currentView={view} title={pageTitle} onNavigate={setView} onAskTrace={() => setVoiceOpen(true)}>
        {content}
      </AppLayout>
      <VoiceAssistant open={voiceOpen} onClose={() => setVoiceOpen(false)} />
    </>
  );
}

export default App;
