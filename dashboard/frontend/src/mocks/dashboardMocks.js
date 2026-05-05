/**
 * Client-side mocks for dashboard data not yet exposed by the backend.
 * Plan B replaces these by real endpoints and deletes this file.
 */

function buildSparkline(start, drift, noise) {
  const out = [];
  let v = start;
  for (let i = 0; i < 30; i++) {
    v = Math.max(0, v + drift + (Math.random() - 0.5) * noise);
    out.push(Number(v.toFixed(1)));
  }
  return out;
}

export const MOCK_SPARKLINES = {
  savings: buildSparkline(2000, 150, 800),
  cycle: buildSparkline(8, -0.05, 1.2),
  success: buildSparkline(72, 0.4, 4),
};

export const MOCK_DELTAS = {
  savings: 18,
  cycle: -32,
  success: 4,
};

export const MOCK_ATTENTION = [
  {
    id: 'att-1',
    category: 'APPROVAL',
    severity: 'warning',
    title: 'Office chairs · 12,500 TND',
    subtitle: 'Best supplier: ErgoTunis · score 92/100',
    actionLabel: 'Review',
    actionHref: '/request/example-1',
  },
  {
    id: 'att-2',
    category: 'STUCK',
    severity: 'danger',
    title: 'Industrial sensors',
    subtitle: '3 of 5 suppliers haven’t responded for 48h+',
    actionLabel: 'Relaunch',
    actionHref: '/request/example-2',
  },
  {
    id: 'att-3',
    category: 'BUDGET',
    severity: 'danger',
    title: 'Q2 IT Equipment · 87% used',
    subtitle: '14,200 TND remaining, 3 active requests',
    actionLabel: 'View',
    actionHref: '/budget',
  },
];

function buildTrend(days, baseline, drift, noise) {
  const out = [];
  const now = new Date();
  let v = baseline;
  for (let i = days - 1; i >= 0; i--) {
    v = Math.max(0, v + drift + (Math.random() - 0.5) * noise);
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    out.push({
      date: d.toISOString().slice(0, 10),
      value: Number(v.toFixed(1)),
      requests: Math.round(2 + Math.random() * 8),
    });
  }
  return out;
}

export const MOCK_TREND = {
  savings: {
    '7d': buildTrend(7, 1500, 100, 600),
    '30d': buildTrend(30, 1200, 60, 700),
    '90d': buildTrend(90, 900, 30, 800),
  },
  cycle: {
    '7d': buildTrend(7, 5, -0.05, 1.2),
    '30d': buildTrend(30, 6, -0.03, 1.3),
    '90d': buildTrend(90, 7, -0.02, 1.5),
  },
  volume: {
    '7d': buildTrend(7, 8000, 500, 3000),
    '30d': buildTrend(30, 6000, 200, 3500),
    '90d': buildTrend(90, 4500, 80, 4000),
  },
};

export const MOCK_TREND_PREVIOUS = {
  savings: { '7d': 9800, '30d': 38000, '90d': 105000 },
  cycle:   { '7d': 7.2,  '30d': 8.1,   '90d': 9.0   },
  volume:  { '7d': 52000, '30d': 180000, '90d': 510000 },
};

export const MOCK_CATEGORY_SPEND = [
  { category: 'IT Equipment',     amount: 84300 },
  { category: 'Office Supplies',  amount: 42100 },
  { category: 'Industrial Tools', amount: 31800 },
  { category: 'Logistics',        amount: 19400 },
  { category: 'Consumables',      amount: 12200 },
  { category: 'Maintenance',      amount: 8500 },
];

export const MOCK_TOP_SUPPLIERS = [
  { id: 'sup-1', name: 'ErgoTunis', email: 'sales@ergotunis.tn', category: 'Office Supplies',  responseRate: 92, avgScore: 91.4, lastInteractionDays: 1 },
  { id: 'sup-2', name: 'TechBureau', email: 'contact@techbureau.tn', category: 'IT Equipment',     responseRate: 88, avgScore: 88.1, lastInteractionDays: 3 },
  { id: 'sup-3', name: 'IndusPlus',  email: 'info@indusplus.tn',     category: 'Industrial Tools', responseRate: 81, avgScore: 84.6, lastInteractionDays: 4 },
  { id: 'sup-4', name: 'LogiMed',    email: 'rfq@logimed.tn',        category: 'Logistics',        responseRate: 76, avgScore: 80.2, lastInteractionDays: 6 },
  { id: 'sup-5', name: 'ConsoTN',    email: 'commercial@consotn.tn', category: 'Consumables',      responseRate: 70, avgScore: 77.5, lastInteractionDays: 9 },
];

export const MOCK_AGENT_ACTIVITY = {
  agents: [
    { name: 'Analysis',      key: 'analysis',      activeCount: 4,  p95Ms: 820,  tokensPerMin: 4100 },
    { name: 'Sourcing',      key: 'sourcing',      activeCount: 7,  p95Ms: 3400, tokensPerMin: 8200 },
    { name: 'Communication', key: 'communication', activeCount: 12, p95Ms: 1900, tokensPerMin: 6500, isCurrentlyActive: true },
    { name: 'Evaluation',    key: 'evaluation',    activeCount: 2,  p95Ms: 240,  tokensPerMin: 0    },
    { name: 'Storage',       key: 'storage',       activeCount: 18, p95Ms: 110,  tokensPerMin: 0    },
  ],
  status: 'operational',
};
