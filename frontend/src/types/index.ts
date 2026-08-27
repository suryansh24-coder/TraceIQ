export type Severity = 'critical' | 'warning' | 'info';
export type InvestigationStatus = 'investigated' | 'resolved' | 'investigating';

export interface RecentInvestigation {
  id: string;
  service: string;
  title: string;
  severity: Severity;
  timeAgo: string;
  status: InvestigationStatus;
}

export interface SystemStat {
  label: string;
  value: string;
  hint: string;
}

export interface NavItem {
  id: string;
  label: string;
  icon: string;
}

export interface ProgressStage {
  id: number;
  label: string;
  status: 'complete' | 'active' | 'pending';
  detail?: string;
}

export interface InvestigationStep {
  id: string;
  label: string;
}

export interface DemoVoicePrompt {
  id: string;
  label: string;
  transcript: string;
  response: string;
}

export interface EvidenceCard {
  id: 'github' | 'monitoring' | 'knowledge';
  kind: 'GitHub Activity' | 'Monitoring Signals' | 'Historical Knowledge';
  icon: string;
  status: 'success' | 'warning' | 'info' | 'critical';
  statusLabel: string;
  timestamp: string;
  points: string[];
}

export interface VoiceStateContent {
  idle: { title: string };
  listening: { title: string; transcript: string };
  thinking: { title: string };
  response: { title: string; response: string };
}

export interface FailureChainEvent {
  id: string;
  time: string;
  type: 'normal' | 'warning' | 'root_cause' | 'failure';
  typeLabel: string;
  service: string;
  title: string;
  description: string;
}