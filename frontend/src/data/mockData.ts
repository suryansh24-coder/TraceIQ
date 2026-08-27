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

export const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: 'LayoutDashboard' },
  { id: 'investigate', label: 'Investigate', icon: 'Search' },
  { id: 'incidents', label: 'Incidents', icon: 'AlertTriangle' },
  { id: 'knowledge', label: 'Knowledge', icon: 'BookOpen' },
  { id: 'runbooks', label: 'Runbooks', icon: 'Terminal' },
  { id: 'voice', label: 'Voice', icon: 'Mic' },
  { id: 'settings', label: 'Settings', icon: 'Settings' },
];

export const recentInvestigations: RecentInvestigation[] = [
  {
    id: 'inv-001',
    service: 'payments-v2',
    title: 'HTTP 401 Token Signature Mismatch',
    severity: 'critical',
    timeAgo: '12 minutes ago',
    status: 'investigated',
  },
  {
    id: 'inv-002',
    service: 'orders-service',
    title: 'HTTP 504 Database Connection Pool Exhaustion',
    severity: 'warning',
    timeAgo: '1 hour ago',
    status: 'resolved',
  },
  {
    id: 'inv-003',
    service: 'notification-worker',
    title: 'HTTP 429 SendGrid API Throttling Spike',
    severity: 'info',
    timeAgo: '3 hours ago',
    status: 'investigated',
  },
];

export const systemStats: SystemStat[] = [
  { label: 'Monitored APIs', value: '24', hint: 'across 8 clusters' },
  { label: 'Active Incidents', value: '2', hint: '1 critical' },
  { label: 'Investigations Today', value: '18', hint: '+4 vs yesterday' },
  { label: 'Model Confidence', value: '89.4%', hint: '7-day rolling avg' },
];

export const examplePrompt = 'Why is payments-v2 returning HTTP 401 authentication errors on POST /v2/charges?';

export interface ProgressStage {
  id: number;
  label: string;
  status: 'complete' | 'active' | 'pending';
  detail?: string;
}

export const initialProgressStages: ProgressStage[] = [
  { id: 1, label: 'Collecting signals', status: 'complete', detail: 'GitHub, Datadog' },
  { id: 2, label: 'Analyzing logs', status: 'active', detail: 'HTTP 401 stack' },
  { id: 3, label: 'Tracing dependencies', status: 'pending', detail: 'payments → auth' },
  { id: 4, label: 'Correlating failures', status: 'pending', detail: 'Secret handshake' },
  { id: 5, label: 'Identifying root cause', status: 'pending', detail: 'Commit #a3f892' },
  { id: 6, label: 'Generating recommendation', status: 'pending', detail: 'Config fix ready' },
];

export interface InvestigationStep {
  id: string;
  label: string;
}

export const investigationSteps: InvestigationStep[] = [
  { id: 'signals', label: 'Collecting telemetry signals from GitHub and Datadog APM...' },
  { id: 'logs', label: 'Analyzing HTTP 401 exception stack traces for POST /v2/charges...' },
  { id: 'dependencies', label: 'Tracing RPC calls from payments-v2 to auth-service...' },
  { id: 'correlate', label: 'Correlating deployment commit #a3f892 with token signature failures...' },
  { id: 'root_cause', label: 'Identifying root cause mismatch in JWT signing secret key...' },
  { id: 'recommendation', label: 'Generating actionable Kubernetes secret deployment fix preview...' },
];

export interface DemoVoicePrompt {
  id: string;
  label: string;
  transcript: string;
  response: string;
}

export const demoVoicePrompts: DemoVoicePrompt[] = [
  {
    id: 'why_fail',
    label: 'Why did this API fail?',
    transcript: 'Why is payments-v2 returning HTTP 401 Unauthorized errors on POST /v2/charges?',
    response:
      'The payments-v2 service is rejecting API requests because auth-service rotated its JWT signing key in commit #a3f892, but payments-v2 environment secrets were not updated in sync.',
  },
  {
    id: 'root_cause',
    label: 'Explain the root cause.',
    transcript: 'Explain the technical root cause of this secret mismatch.',
    response:
      'Commit #a3f892 deployed new RSA public/private key pairs to auth-service vault at 14:22:04 UTC. Because payments-v2 pod environment maps contain stale secret key v1_legacy_secret_44012, incoming token signatures fail validation.',
  },
  {
    id: 'fix_first',
    label: 'What should I fix first?',
    transcript: 'What is the immediate recommended resolution step?',
    response:
      'Update AUTH_SECRET_KEY in payments-v2 deployment config to "v2_secret_key_9981a_rotated", then execute a rolling restart (kubectl rollout restart deployment/payments-v2). TraceIQ queued fix PR #PR-3841.',
  },
  {
    id: 'evidence',
    label: 'What evidence supports this conclusion?',
    transcript: 'What evidence signals correlated this root cause?',
    response:
      'TraceIQ correlated 7 signals: 1) GitHub commit #a3f892 18m ago, 2) Datadog HTTP 401 surge to 142.8 err/sec, 3) 94% match against Runbook RB-104 (Service Secret Key Sync).',
  },
];

export interface EvidenceCard {
  id: 'github' | 'monitoring' | 'knowledge';
  kind: 'GitHub Activity' | 'Monitoring Signals' | 'Historical Knowledge';
  icon: string;
  status: 'success' | 'warning' | 'info' | 'critical';
  statusLabel: string;
  timestamp: string;
  points: string[];
}

export const evidenceCards: EvidenceCard[] = [
  {
    id: 'github',
    kind: 'GitHub Activity',
    icon: 'Github',
    status: 'warning',
    statusLabel: 'Secret Key Rotated',
    timestamp: 'Commit #a3f892 deployed 18m ago',
    points: [
      'auth-service / config/jwt_keys.pem updated',
      'Commit #a3f892: "rotate RSA JWT signing keys"',
      'payments-v2 deployment secrets untouched',
    ],
  },
  {
    id: 'monitoring',
    kind: 'Monitoring Signals',
    icon: 'Activity',
    status: 'critical',
    statusLabel: 'HTTP 401 Anomaly',
    timestamp: 'Spike started at 14:24:15 UTC',
    points: [
      'HTTP 401 Unauthorized rate spiked 340%',
      '142.8 error responses/sec on POST /v2/charges',
      'Latency baseline p95 unchanged at 42ms',
    ],
  },
  {
    id: 'knowledge',
    kind: 'Historical Knowledge',
    icon: 'BookOpen',
    status: 'info',
    statusLabel: '3 Matched Runbooks',
    timestamp: 'Last incident 9 days ago',
    points: [
      'Runbook RB-104: Service Secret Key Sync',
      'Incident #INC-7210: Auth Secret Rotation Skew',
      'Postmortem PM-412: Dual-Key Rotation Protocol',
    ],
  },
];

export const rootCause =
  'The auth-service rotated its RSA/JWT signing secret key in commit #a3f892 (deployed 18 minutes ago). However, the payments-v2 service environment secret AUTH_SECRET_KEY was not updated simultaneously. Consequently, payments-v2 validates incoming bearer tokens using the deprecated key, resulting in HTTP 401 Unauthorized failures on all POST /v2/charges API calls.';

export const rootCauseConfidence = 87;

export const rootCauseReasons: string[] = [
  'auth-service rotated RSA signing key pair in commit #a3f892 (14:22:04 UTC)',
  'payments-v2 pod environment map contains stale secret key v1_legacy_secret_44012',
  'HTTP 401 Unauthorized error rate spiked 340% immediately following auth-service deployment',
];

export const recommendedSteps: string[] = [
  'Update AUTH_SECRET_KEY in payments-v2 deployment secrets to "v2_secret_key_9981a_rotated".',
  'Execute a zero-downtime rolling update for payments-v2 (kubectl rollout restart deployment/payments-v2).',
  'Verify POST /v2/charges health check returns HTTP 200 OK and signature error rate drops below 0.01%.',
  'Adopt dual-key grace period policy per Runbook RB-104 to prevent secret synchronization skew.',
];

export interface VoiceStateContent {
  idle: { title: string };
  listening: { title: string; transcript: string };
  thinking: { title: string };
  response: { title: string; response: string };
}

export const voiceDemoTranscript = 'Why is payments-v2 returning HTTP 401 authentication errors on POST /v2/charges?';

export const voiceDemoResponse =
  'TraceIQ correlated 7 telemetry signals across GitHub and Datadog. The root cause is a secret key rotation mismatch: auth-service updated its JWT signing key in commit #a3f892 18 minutes ago, but payments-v2 environment configuration was not updated in sync. Updating AUTH_SECRET_KEY in payments-v2 and triggering a pod rollout resolves the 401 error spike.';

export interface FailureChainEvent {
  id: string;
  time: string;
  type: 'normal' | 'warning' | 'root_cause' | 'failure';
  typeLabel: string;
  service: string;
  title: string;
  description: string;
}

export const failureChainEvents: FailureChainEvent[] = [
  {
    id: 'fc-1',
    time: '14:20:12 UTC',
    type: 'normal',
    typeLabel: 'Normal Baseline',
    service: 'payments-v2',
    title: 'Baseline API operations',
    description: 'POST /v2/charges processing 1,240 req/min with 99.98% success rate and 42ms p95 latency.',
  },
  {
    id: 'fc-2',
    time: '14:22:04 UTC',
    type: 'root_cause',
    typeLabel: 'Root Cause Origin',
    service: 'auth-service',
    title: 'Commit #a3f892 key rotation deployed',
    description: 'auth-service deployed RSA_PUB_KEY_V2 secret rotation to production vault without updating payments-v2 secret map.',
  },
  {
    id: 'fc-3',
    time: '14:23:40 UTC',
    type: 'warning',
    typeLabel: 'Warning Signal',
    service: 'payments-v2',
    title: 'Token signature retry escalation',
    description: 'Auth client retry handler triggered on 14% of incoming checkout requests attempting legacy secret verification fallback.',
  },
  {
    id: 'fc-4',
    time: '14:24:15 UTC',
    type: 'failure',
    typeLabel: 'Critical Outage',
    service: 'payments-v2',
    title: '340% spike in HTTP 401 Unauthorized',
    description: 'POST /v2/charges rejecting 142.8 checkout requests/sec due to InvalidSignatureError on authorization bearer token.',
  },
];

export const humanExplanation =
  'In developer terms: auth-service began signing JWT tokens with a new cryptographic secret key 18 minutes ago, but payments-v2 was never updated with the new key. When payments-v2 receives a customer checkout request, it attempts to verify the authorization signature using its old secret key, fails validation, and returns an HTTP 401 Unauthorized error. Updating the payments-v2 environment secret restores normal payment processing immediately.';

