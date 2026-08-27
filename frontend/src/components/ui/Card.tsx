import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  as?: 'div' | 'section' | 'article';
}

export function Card({ children, className = '', as: Tag = 'div' }: CardProps) {
  return (
    <Tag
      className={`rounded-2xl border border-ink-200 bg-white shadow-soft transition-all duration-200 dark:border-ink-800 dark:bg-ink-900 ${className}`}
    >
      {children}
    </Tag>
  );
}

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
}

export function SectionHeader({ title, subtitle, action, className = '' }: SectionHeaderProps) {
  return (
    <div className={`flex items-end justify-between gap-4 ${className}`}>
      <div>
        <h2 className="text-base font-semibold tracking-tight text-ink-900 dark:text-ink-100">{title}</h2>
        {subtitle && <p className="mt-0.5 text-sm text-ink-500 dark:text-ink-400">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
