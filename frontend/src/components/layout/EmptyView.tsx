import { Construction } from 'lucide-react';
import { Card } from '@/components/common/Card';

export function EmptyView({ title }: { title: string }) {
  return (
    <div className="mx-auto flex min-h-[calc(100vh-72px)] max-w-5xl items-center justify-center px-5 py-10">
      <Card className="flex max-w-md flex-col items-center px-8 py-12 text-center">
        <div className="mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-accent-50 text-accent-600"><Construction size={24} /></div>
        <h2 className="text-lg font-semibold text-ink-900">{title}</h2>
        <p className="mt-2 text-sm leading-6 text-ink-500">This workspace is ready for your team's engineering knowledge. Use Investigate to begin with a live incident.</p>
      </Card>
    </div>
  );
}
