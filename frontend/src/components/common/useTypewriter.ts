import { useEffect, useState } from 'react';

export function useTypewriter(text: string, enabled = true, speed = 28): string {
  const [displayed, setDisplayed] = useState('');

  useEffect(() => {
    if (!enabled) {
      setDisplayed(text);
      return;
    }
    setDisplayed('');
    if (!text) return;
    let i = 0;
    const interval = window.setInterval(() => {
      i += 1;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) window.clearInterval(interval);
    }, speed);
    return () => window.clearInterval(interval);
  }, [text, enabled, speed]);

  return displayed;
}
