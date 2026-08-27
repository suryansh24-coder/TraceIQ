import { Radar } from 'lucide-react';

export function Logo({ size = 'md', showWordmark = true }: { size?: 'sm' | 'md' | 'lg'; showWordmark?: boolean }) {
  const dim = size === 'sm' ? 'h-7 w-7' : size === 'lg' ? 'h-10 w-10' : 'h-8 w-8';
  const iconSize = size === 'sm' ? 16 : size === 'lg' ? 22 : 18;
  const text = size === 'sm' ? 'text-sm' : size === 'lg' ? 'text-xl' : 'text-base';

  return (
    <div className="flex items-center gap-2.5">
      <div
        className={`${dim} grid place-items-center rounded-xl bg-gradient-to-br from-ink-900 to-ink-800 text-white shadow-soft`}
      >
        <Radar size={iconSize} strokeWidth={2.25} />
      </div>
      {showWordmark && (
        <span className={`${text} font-semibold tracking-tight text-ink-900`}>
          Trace<span className="text-accent-600">IQ</span>
        </span>
      )}
    </div>
  );
}
