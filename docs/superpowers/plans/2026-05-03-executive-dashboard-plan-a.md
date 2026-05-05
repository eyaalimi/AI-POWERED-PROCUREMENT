# Executive Dashboard — Plan A (Visual Redesign + Phase 1 Mocks)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the full executive dashboard redesign described in `docs/superpowers/specs/2026-05-03-executive-dashboard-design.md` using only existing endpoints + client-side mocks for data not yet exposed by the backend. Plan B (later) will swap the mocks for real endpoints.

**Architecture:** Introduce a parallel design-token layer (`dashboard.css`) scoped to a single `.dash` wrapper on the dashboard route, leaving the existing `App.css` untouched so other pages remain unchanged. Decompose the dashboard into one component per visual zone, each in its own file under `dashboard/frontend/src/components/dashboard/`. Mocked endpoints live in `dashboard/frontend/src/mocks/dashboardMocks.js` so Plan B can delete the file in one PR.

**Tech Stack:** React 19, Vite 8, Recharts 3.8, lucide-react, react-router-dom 7. No new dependencies.

---

## File Structure

**Create:**
- `dashboard/frontend/src/styles/dashboard.css` — design tokens + all dashboard-only styles
- `dashboard/frontend/src/mocks/dashboardMocks.js` — client-side stand-in data for unbuilt endpoints
- `dashboard/frontend/src/components/dashboard/HeroHeader.jsx` — greeting + period selector + "updated Xs ago" pill
- `dashboard/frontend/src/components/dashboard/ScoreboardCard.jsx` — one of the 4 hero cards
- `dashboard/frontend/src/components/dashboard/Sparkline.jsx` — pure SVG sparkline (no Recharts overhead)
- `dashboard/frontend/src/components/dashboard/DotScale.jsx` — 9-dot capacity gauge for card 4
- `dashboard/frontend/src/components/dashboard/LiveAIStrip.jsx` — animated 5-agent activity strip
- `dashboard/frontend/src/components/dashboard/AttentionPanel.jsx` — "Needs your attention" list
- `dashboard/frontend/src/components/dashboard/RecommendationsCard.jsx` — top-3 recommendations
- `dashboard/frontend/src/components/dashboard/TrendChart.jsx` — multi-metric, multi-period area chart
- `dashboard/frontend/src/components/dashboard/CategoryBreakdown.jsx` — horizontal bar list
- `dashboard/frontend/src/components/dashboard/PipelineFlow.jsx` — horizontal 7-stage pipeline with bottleneck callout
- `dashboard/frontend/src/components/dashboard/SuppliersLeaderboard.jsx` — top-5 suppliers table
- `dashboard/frontend/src/components/dashboard/Skeleton.jsx` — reusable loading skeleton primitives

**Modify:**
- `dashboard/frontend/src/pages/KpisPage.jsx` — full rewrite as a thin orchestrator that composes the new components
- `dashboard/frontend/src/main.jsx` — import `dashboard.css` so tokens are available

**Untouched (deliberately):** `App.css`, sidebar, top header chrome, all other pages.

---

## Conventions used by every task

- **Imports:** named imports from `lucide-react`, default for components, `import './dashboard.css'` only in `main.jsx`.
- **CSS class prefix:** every new class starts with `dash-` to avoid colliding with existing `App.css` rules.
- **All components are functional + exports a single default.** No PropTypes, no TypeScript.
- **Mocked data** is imported from `mocks/dashboardMocks.js` and clearly marked. Plan B replaces these imports with `useApi` calls.
- **Manual visual verification** replaces unit tests for layout-only components. Each task ends with a `npm run dev` check + a checklist of what to look for in the browser. The codebase has no frontend test runner installed, so adding one is out of scope here.
- **Commit messages** use Conventional Commits prefixes (`feat:`, `style:`, `refactor:`, `chore:`).

---

## Task 1: Establish design tokens and `.dash` scope

**Files:**
- Create: `dashboard/frontend/src/styles/dashboard.css`
- Modify: `dashboard/frontend/src/main.jsx`

- [ ] **Step 1: Create `dashboard.css` with the full token set**

Write `dashboard/frontend/src/styles/dashboard.css`:

```css
/* ============================================================
   Executive Dashboard — Design Tokens (scoped to .dash)
   See docs/superpowers/specs/2026-05-03-executive-dashboard-design.md
   ============================================================ */

.dash {
  /* Surface */
  --dash-bg-base:        #0B0E14;
  --dash-bg-elevated:    #131722;
  --dash-bg-raised:      #1A1F2E;
  --dash-border-subtle:  #1F2533;
  --dash-border-strong:  #2A3142;

  /* Text */
  --dash-text-primary:   #E8ECF4;
  --dash-text-secondary: #8B93A7;
  --dash-text-muted:     #5A6275;

  /* Semantic accents */
  --dash-accent-primary: #6366F1;
  --dash-accent-success: #10B981;
  --dash-accent-warning: #F59E0B;
  --dash-accent-danger:  #EF4444;
  --dash-accent-ai:      #A78BFA;

  /* Gradients */
  --dash-gradient-hero: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(167,139,250,0.06));
  --dash-gradient-glow: radial-gradient(circle at top right, rgba(167,139,250,0.15), transparent 70%);

  /* Spacing scale */
  --dash-s-1: 4px;
  --dash-s-2: 8px;
  --dash-s-3: 12px;
  --dash-s-4: 16px;
  --dash-s-6: 24px;
  --dash-s-8: 32px;
  --dash-s-12: 48px;

  /* Radius */
  --dash-radius: 12px;

  background: var(--dash-bg-base);
  color: var(--dash-text-primary);
  min-height: 100vh;
  padding: var(--dash-s-8);
  font-family: 'Inter', system-ui, 'Segoe UI', Roboto, sans-serif;
  font-feature-settings: "ss01", "cv11";
}

.dash *,
.dash *::before,
.dash *::after {
  box-sizing: border-box;
}

.dash h1, .dash h2, .dash h3, .dash h4 {
  margin: 0;
  color: var(--dash-text-primary);
  font-weight: 600;
}

.dash p { margin: 0; }

.dash .num,
.dash .dash-num {
  font-variant-numeric: tabular-nums;
}

/* Section spacing */
.dash-tier {
  margin-bottom: var(--dash-s-8);
}

.dash-tier:last-child {
  margin-bottom: 0;
}

/* Card primitive */
.dash-card {
  background: var(--dash-bg-elevated);
  border: 1px solid var(--dash-border-subtle);
  border-radius: var(--dash-radius);
  padding: var(--dash-s-6);
}

.dash-card[data-interactive="true"] {
  cursor: pointer;
  transition: border-color 120ms ease;
}

.dash-card[data-interactive="true"]:hover {
  border-color: var(--dash-border-strong);
  box-shadow: inset 0 0 0 1px var(--dash-border-strong);
}

/* Uppercase label */
.dash-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--dash-text-muted);
}

/* Focus rings */
.dash a:focus-visible,
.dash button:focus-visible,
.dash [tabindex]:focus-visible {
  outline: 2px solid var(--dash-accent-primary);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .dash *,
  .dash *::before,
  .dash *::after {
    animation-duration: 0ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0ms !important;
  }
}

/* Print stylesheet — minimal light-mode export */
@media print {
  .dash {
    background: #fff;
    color: #000;
  }
  .dash-card {
    background: #fff;
    border-color: #ccc;
  }
  .dash-live-strip {
    display: none !important;
  }
}

/* Below 1024px: desktop-only message */
.dash-too-narrow {
  display: none;
}

@media (max-width: 1023px) {
  .dash > *:not(.dash-too-narrow) {
    display: none !important;
  }
  .dash-too-narrow {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    text-align: center;
    color: var(--dash-text-secondary);
    gap: var(--dash-s-4);
  }
}
```

- [ ] **Step 2: Wire the stylesheet into the app**

Edit `dashboard/frontend/src/main.jsx`. Find the existing import of `App.css` (or wherever styles are loaded) and add the new import directly after it:

```jsx
import './styles/dashboard.css';
```

If `main.jsx` does not currently import any CSS at the top, add the import after the React imports.

- [ ] **Step 3: Verify build still passes**

Run: `cd dashboard/frontend && npm run dev`
Expected: dev server starts without errors. Open `http://localhost:5173/` — the existing dashboard renders unchanged (because no element has the `.dash` class yet).

- [ ] **Step 4: Commit**

```bash
git add dashboard/frontend/src/styles/dashboard.css dashboard/frontend/src/main.jsx
git commit -m "feat(dashboard): add design tokens scoped to .dash"
```

---

## Task 2: Create the mocks module

**Files:**
- Create: `dashboard/frontend/src/mocks/dashboardMocks.js`

This single file holds all mocked data. Plan B deletes this file in one commit.

- [ ] **Step 1: Write the mocks**

Create `dashboard/frontend/src/mocks/dashboardMocks.js`:

```js
/**
 * Client-side mocks for dashboard data not yet exposed by the backend.
 * Plan B replaces these by real endpoints and deletes this file.
 */

// 30-day sparklines: arrays of 30 numbers
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

// MoM deltas (percent)
export const MOCK_DELTAS = {
  savings: 18,    // +18% MoM
  cycle: -32,    // -32% MoM (improvement for "lower is better")
  success: 4,     // +4 percentage points
};

// "Needs your attention" rows
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

// Trend chart data — keyed by metric + period
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

// Spend by category
export const MOCK_CATEGORY_SPEND = [
  { category: 'IT Equipment',     amount: 84300 },
  { category: 'Office Supplies',  amount: 42100 },
  { category: 'Industrial Tools', amount: 31800 },
  { category: 'Logistics',        amount: 19400 },
  { category: 'Consumables',      amount: 12200 },
  { category: 'Maintenance',      amount: 8500 },
];

// Top-5 suppliers leaderboard
export const MOCK_TOP_SUPPLIERS = [
  { id: 'sup-1', name: 'ErgoTunis', email: 'sales@ergotunis.tn', category: 'Office Supplies',  responseRate: 92, avgScore: 91.4, lastInteractionDays: 1 },
  { id: 'sup-2', name: 'TechBureau', email: 'contact@techbureau.tn', category: 'IT Equipment',     responseRate: 88, avgScore: 88.1, lastInteractionDays: 3 },
  { id: 'sup-3', name: 'IndusPlus',  email: 'info@indusplus.tn',     category: 'Industrial Tools', responseRate: 81, avgScore: 84.6, lastInteractionDays: 4 },
  { id: 'sup-4', name: 'LogiMed',    email: 'rfq@logimed.tn',        category: 'Logistics',        responseRate: 76, avgScore: 80.2, lastInteractionDays: 6 },
  { id: 'sup-5', name: 'ConsoTN',    email: 'commercial@consotn.tn', category: 'Consumables',      responseRate: 70, avgScore: 77.5, lastInteractionDays: 9 },
];

// Per-agent live activity for the AI strip
export const MOCK_AGENT_ACTIVITY = {
  agents: [
    { name: 'Analysis',      key: 'analysis',      activeCount: 4,  p95Ms: 820,  tokensPerMin: 4100 },
    { name: 'Sourcing',      key: 'sourcing',      activeCount: 7,  p95Ms: 3400, tokensPerMin: 8200 },
    { name: 'Communication', key: 'communication', activeCount: 12, p95Ms: 1900, tokensPerMin: 6500, isCurrentlyActive: true },
    { name: 'Evaluation',    key: 'evaluation',    activeCount: 2,  p95Ms: 240,  tokensPerMin: 0    },
    { name: 'Storage',       key: 'storage',       activeCount: 18, p95Ms: 110,  tokensPerMin: 0    },
  ],
  status: 'operational', // 'operational' | 'degraded'
};
```

- [ ] **Step 2: Commit**

```bash
git add dashboard/frontend/src/mocks/dashboardMocks.js
git commit -m "chore(dashboard): add mock data module for unbuilt endpoints"
```

---

## Task 3: Skeleton primitives

**Files:**
- Create: `dashboard/frontend/src/components/dashboard/Skeleton.jsx`
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Create the component**

Create `dashboard/frontend/src/components/dashboard/Skeleton.jsx`:

```jsx
export function SkeletonBlock({ height = 16, width = '100%', radius = 6, style }) {
  return (
    <span
      className="dash-skeleton"
      style={{ height, width, borderRadius: radius, ...style }}
      aria-hidden="true"
    />
  );
}

export function SkeletonCard({ height = 140 }) {
  return (
    <div className="dash-card" style={{ minHeight: height }}>
      <SkeletonBlock width="40%" height={11} style={{ marginBottom: 16 }} />
      <SkeletonBlock width="60%" height={28} style={{ marginBottom: 12 }} />
      <SkeletonBlock width="100%" height={60} radius={8} />
    </div>
  );
}
```

- [ ] **Step 2: Add the skeleton animation CSS**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
.dash-skeleton {
  display: inline-block;
  background: linear-gradient(
    90deg,
    var(--dash-bg-raised) 0%,
    var(--dash-border-strong) 50%,
    var(--dash-bg-raised) 100%
  );
  background-size: 200% 100%;
  animation: dash-skeleton-sweep 1.4s ease-in-out infinite;
}

@keyframes dash-skeleton-sweep {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/components/dashboard/Skeleton.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): add skeleton loading primitives"
```

---

## Task 4: Sparkline + DotScale primitives

**Files:**
- Create: `dashboard/frontend/src/components/dashboard/Sparkline.jsx`
- Create: `dashboard/frontend/src/components/dashboard/DotScale.jsx`
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Create `Sparkline.jsx`**

Pure SVG sparkline — small enough to inline without Recharts overhead.

```jsx
export default function Sparkline({ data, color = '#6366F1', width = 220, height = 60, ariaLabel }) {
  if (!data || data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const stepX = width / (data.length - 1);

  const coords = data.map((v, i) =>
    `${i * stepX},${height - ((v - min) / range) * height}`
  );
  const points = coords.join(' ');
  const area = `M0,${height} L${coords.join(' L')} L${width},${height} Z`;

  return (
    <svg
      width="100%"
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      role="img"
      aria-label={ariaLabel}
    >
      <defs>
        <linearGradient id={`spark-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#spark-${color.replace('#', '')})`} />
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
```

- [ ] **Step 2: Create `DotScale.jsx`**

```jsx
export default function DotScale({ filled = 0, total = 9, alertFrom = total + 1, ariaLabel }) {
  const dots = Array.from({ length: total }, (_, i) => {
    if (i >= filled) return 'empty';
    return i + 1 >= alertFrom ? 'alert' : 'filled';
  });

  return (
    <div className="dash-dotscale" role="img" aria-label={ariaLabel}>
      {dots.map((state, i) => (
        <span key={i} className={`dash-dot dash-dot--${state}`} />
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Add dot styles**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
.dash-dotscale {
  display: flex;
  gap: 6px;
  align-items: center;
  height: 60px;
}

.dash-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--dash-bg-raised);
  border: 1px solid var(--dash-border-strong);
}

.dash-dot--filled {
  background: var(--dash-accent-primary);
  border-color: var(--dash-accent-primary);
}

.dash-dot--alert {
  background: var(--dash-accent-warning);
  border-color: var(--dash-accent-warning);
}
```

- [ ] **Step 4: Commit**

```bash
git add dashboard/frontend/src/components/dashboard/Sparkline.jsx dashboard/frontend/src/components/dashboard/DotScale.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): add Sparkline and DotScale primitives"
```

---

## Task 5: ScoreboardCard component

**Files:**
- Create: `dashboard/frontend/src/components/dashboard/ScoreboardCard.jsx`
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Create the component**

Create `dashboard/frontend/src/components/dashboard/ScoreboardCard.jsx`:

```jsx
import { ArrowUp, ArrowDown } from 'lucide-react';
import Sparkline from './Sparkline';

const ACCENT_HEX = {
  primary: '#6366F1',
  success: '#10B981',
  warning: '#F59E0B',
  danger:  '#EF4444',
};

/**
 * @param {object} props
 * @param {string} props.label                e.g. "SAVINGS"
 * @param {string} props.value                e.g. "142,380 TND"
 * @param {number|null} props.delta           percentage change vs previous period
 * @param {'higher'|'lower'} props.improvementDirection  which direction means "good"
 * @param {string} props.deltaSuffix          e.g. "% MoM" or " pts"
 * @param {string} props.accent               'primary' | 'success' | 'warning' | 'danger'
 * @param {React.ReactNode} props.visual      slot below the metric (Sparkline | DotScale)
 */
export default function ScoreboardCard({
  label,
  value,
  delta,
  improvementDirection = 'higher',
  deltaSuffix = '%',
  accent = 'primary',
  visual,
  alertText,
}) {
  const accentColor = ACCENT_HEX[accent] || ACCENT_HEX.primary;
  const goingUp = (delta ?? 0) >= 0;
  const isImprovement = improvementDirection === 'higher' ? goingUp : !goingUp;
  const deltaColor = delta == null
    ? 'var(--dash-text-muted)'
    : isImprovement ? 'var(--dash-accent-success)' : 'var(--dash-accent-danger)';

  return (
    <div className="dash-card dash-scorecard" style={{ '--dash-card-accent': accentColor }}>
      <div className="dash-scorecard-accent-line" />
      <div className="dash-label">{label}</div>
      <div className="dash-scorecard-value dash-num">{value}</div>
      <div className="dash-scorecard-delta" style={{ color: deltaColor }}>
        {delta != null && (
          <>
            {goingUp ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
            <span className="dash-num">{Math.abs(delta)}{deltaSuffix}</span>
          </>
        )}
        {alertText && <span style={{ marginLeft: 8 }}>{alertText}</span>}
      </div>
      <div className="dash-scorecard-visual">{visual}</div>
    </div>
  );
}
```

- [ ] **Step 2: Add scoreboard styles**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
/* Scoreboard cards */
.dash-scoreboard {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--dash-s-4);
  margin-bottom: var(--dash-s-4);
}

.dash-scorecard {
  position: relative;
  background: var(--dash-bg-elevated);
  background-image: var(--dash-gradient-hero);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.32);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: var(--dash-s-2);
  min-height: 180px;
}

.dash-scorecard-accent-line {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--dash-card-accent, var(--dash-accent-primary));
}

.dash-scorecard-value {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--dash-text-primary);
  line-height: 1.1;
  margin-top: 4px;
}

.dash-scorecard-delta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: var(--dash-s-2);
}

.dash-scorecard-visual {
  margin-top: auto;
}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/components/dashboard/ScoreboardCard.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): add ScoreboardCard component"
```

---

## Task 6: HeroHeader (greeting + period selector + live pill)

**Files:**
- Create: `dashboard/frontend/src/components/dashboard/HeroHeader.jsx`
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Create the component**

Create `dashboard/frontend/src/components/dashboard/HeroHeader.jsx`:

```jsx
import { useEffect, useState } from 'react';
import { RotateCw, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const PERIODS = [
  { id: '7d',  label: 'Last 7 days' },
  { id: '30d', label: 'Last 30 days' },
  { id: '90d', label: 'Last 90 days' },
];

function formatRelative(date) {
  const seconds = Math.max(0, Math.round((Date.now() - date) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

export default function HeroHeader({ period, onPeriodChange, lastUpdated }) {
  const { user } = useAuth();
  const [, setTick] = useState(0);
  const [open, setOpen] = useState(false);

  // Tick once a second so "Updated Xs ago" stays accurate
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const monthLabel = new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const currentPeriod = PERIODS.find(p => p.id === period) || PERIODS[1];

  return (
    <div className="dash-hero-header">
      <div className="dash-hero-header-left">
        <div className="dash-hero-greeting">
          Welcome back{user?.name ? `, ${user.name}` : ''}
          <span className="dash-hero-month"> · {monthLabel}</span>
        </div>
      </div>
      <div className="dash-hero-header-right">
        <div className="dash-period-selector">
          <button
            className="dash-period-btn"
            onClick={() => setOpen(o => !o)}
            aria-haspopup="listbox"
            aria-expanded={open}
          >
            {currentPeriod.label}
            <ChevronDown size={14} />
          </button>
          {open && (
            <ul className="dash-period-menu" role="listbox">
              {PERIODS.map(p => (
                <li
                  key={p.id}
                  role="option"
                  aria-selected={p.id === period}
                  className={`dash-period-option ${p.id === period ? 'is-active' : ''}`}
                  onClick={() => { onPeriodChange?.(p.id); setOpen(false); }}
                >
                  {p.label}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="dash-live-pill" title="Auto-refresh">
          <RotateCw size={12} className="dash-live-icon" />
          Updated {lastUpdated ? formatRelative(lastUpdated) : '—'}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add hero header styles**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
.dash-hero-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--dash-s-4);
}

.dash-hero-greeting {
  font-size: 15px;
  color: var(--dash-text-secondary);
}

.dash-hero-month {
  color: var(--dash-text-muted);
}

.dash-hero-header-right {
  display: flex;
  align-items: center;
  gap: var(--dash-s-3);
}

.dash-period-selector { position: relative; }

.dash-period-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--dash-bg-elevated);
  border: 1px solid var(--dash-border-subtle);
  color: var(--dash-text-primary);
  border-radius: 8px;
  padding: 8px 12px;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.dash-period-btn:hover { border-color: var(--dash-border-strong); }

.dash-period-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: var(--dash-bg-elevated);
  border: 1px solid var(--dash-border-strong);
  border-radius: 8px;
  list-style: none;
  padding: 4px;
  min-width: 160px;
  z-index: 10;
}

.dash-period-option {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  color: var(--dash-text-primary);
}

.dash-period-option:hover { background: var(--dash-bg-raised); }
.dash-period-option.is-active { color: var(--dash-accent-primary); }

.dash-live-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--dash-bg-elevated);
  border: 1px solid var(--dash-border-subtle);
  color: var(--dash-text-secondary);
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
}

.dash-live-icon {
  animation: dash-live-pulse 4s ease-in-out infinite;
}

@keyframes dash-live-pulse {
  0%, 90%, 100% { opacity: 1; transform: rotate(0deg); }
  95%           { opacity: 0.4; transform: rotate(180deg); }
}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/components/dashboard/HeroHeader.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): add HeroHeader with period selector and live pill"
```

---

## Task 7: LiveAIStrip

**Files:**
- Create: `dashboard/frontend/src/components/dashboard/LiveAIStrip.jsx`
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Create the component**

Create `dashboard/frontend/src/components/dashboard/LiveAIStrip.jsx`:

```jsx
import { useState } from 'react';

export default function LiveAIStrip({ agents = [], status = 'operational' }) {
  const [hoverKey, setHoverKey] = useState(null);
  const statusLabel = status === 'operational' ? 'Operational' : 'Degraded';
  const statusClass = status === 'operational' ? 'is-ok' : 'is-degraded';

  return (
    <div className="dash-live-strip" aria-hidden="true">
      <div className="dash-live-strip-label">LIVE AI</div>

      <div className="dash-live-flow">
        {agents.map((agent, idx) => (
          <div key={agent.key} className="dash-live-node-wrap">
            <div
              className={`dash-live-node ${agent.isCurrentlyActive ? 'is-active' : ''}`}
              onMouseEnter={() => setHoverKey(agent.key)}
              onMouseLeave={() => setHoverKey(null)}
            >
              <span className="dash-live-count dash-num">{agent.activeCount}</span>
              <span className="dash-live-name">{agent.name}</span>
              {hoverKey === agent.key && (
                <div className="dash-live-tooltip" role="tooltip">
                  p95 {agent.p95Ms}ms
                  <br />
                  {agent.tokensPerMin.toLocaleString()} tok/min
                </div>
              )}
            </div>
            {idx < agents.length - 1 && <div className="dash-live-link" />}
          </div>
        ))}
      </div>

      <div className={`dash-live-status ${statusClass}`}>
        <span className="dash-live-status-dot" />
        {statusLabel}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add the live-strip styles**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
/* Live AI strip */
.dash-live-strip {
  position: relative;
  background: var(--dash-bg-elevated);
  background-image: var(--dash-gradient-glow);
  border: 1px solid var(--dash-border-subtle);
  border-radius: var(--dash-radius);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 24px;
  min-height: 64px;
  overflow: hidden;
}

.dash-live-strip-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--dash-text-muted);
  white-space: nowrap;
}

.dash-live-flow {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 12px;
}

.dash-live-node-wrap {
  display: flex;
  align-items: center;
  flex: 1;
}

.dash-live-node {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 8px;
  border-radius: 8px;
  background: var(--dash-bg-raised);
  border: 1px solid var(--dash-border-strong);
  min-width: 96px;
}

.dash-live-node.is-active {
  border-color: var(--dash-accent-ai);
  box-shadow: 0 0 0 0 rgba(167, 139, 250, 0.6);
  animation: dash-ai-pulse 2s ease-in-out infinite;
}

@keyframes dash-ai-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(167, 139, 250, 0.55); }
  50%      { box-shadow: 0 0 0 8px rgba(167, 139, 250, 0); }
}

.dash-live-count {
  font-size: 16px;
  font-weight: 700;
  color: var(--dash-text-primary);
}

.dash-live-name {
  font-size: 11px;
  color: var(--dash-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dash-live-link {
  flex: 1;
  height: 2px;
  margin: 0 8px;
  background-image: linear-gradient(
    to right,
    var(--dash-accent-ai) 0,
    var(--dash-accent-ai) 6px,
    transparent 6px,
    transparent 12px
  );
  background-size: 12px 2px;
  background-repeat: repeat-x;
  animation: dash-flow 3s linear infinite;
}

@keyframes dash-flow {
  from { background-position: 0 0; }
  to   { background-position: 24px 0; }
}

.dash-live-tooltip {
  position: absolute;
  top: -52px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--dash-bg-base);
  border: 1px solid var(--dash-border-strong);
  color: var(--dash-text-primary);
  font-size: 11px;
  padding: 6px 10px;
  border-radius: 6px;
  white-space: nowrap;
  z-index: 5;
}

.dash-live-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
}

.dash-live-status.is-ok       { color: var(--dash-accent-success); }
.dash-live-status.is-degraded { color: var(--dash-accent-warning); }

.dash-live-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 6px currentColor;
}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/components/dashboard/LiveAIStrip.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): add LiveAIStrip with animated agent flow"
```

---

## Task 8: AttentionPanel

**Files:**
- Create: `dashboard/frontend/src/components/dashboard/AttentionPanel.jsx`
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Create the component**

Create `dashboard/frontend/src/components/dashboard/AttentionPanel.jsx`:

```jsx
import { AlertTriangle, Clock, DollarSign, RefreshCw, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const CATEGORY_META = {
  APPROVAL:  { Icon: AlertTriangle, severityClass: 'is-warning' },
  STUCK:     { Icon: Clock,         severityClass: 'is-danger'  },
  BUDGET:    { Icon: DollarSign,    severityClass: 'is-danger'  },
  RELAUNCH:  { Icon: RefreshCw,     severityClass: 'is-warning' },
};

export default function AttentionPanel({ items = [] }) {
  const navigate = useNavigate();

  return (
    <div className="dash-card dash-attention">
      <div className="dash-card-header">
        <span className="dash-label">Needs your attention</span>
        <span className="dash-pill">{items.length} {items.length === 1 ? 'item' : 'items'}</span>
      </div>

      {items.length === 0 ? (
        <div className="dash-attention-empty">
          <CheckCircle size={28} color="var(--dash-accent-success)" />
          <p>Everything is on track. Nothing requires your attention.</p>
        </div>
      ) : (
        <ul className="dash-attention-list">
          {items.map(item => {
            const meta = CATEGORY_META[item.category] || CATEGORY_META.APPROVAL;
            const { Icon } = meta;
            return (
              <li key={item.id} className={`dash-attention-row ${meta.severityClass}`}>
                <div className="dash-attention-tag">
                  <Icon size={14} />
                  <span>{item.category}</span>
                </div>
                <div className="dash-attention-body">
                  <div className="dash-attention-title">{item.title}</div>
                  <div className="dash-attention-sub">{item.subtitle}</div>
                </div>
                <button
                  className="dash-attention-action"
                  onClick={() => navigate(item.actionHref)}
                >
                  {item.actionLabel} →
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add styles**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
.dash-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--dash-s-4);
}

.dash-pill {
  font-size: 11px;
  font-weight: 600;
  color: var(--dash-text-secondary);
  background: var(--dash-bg-raised);
  padding: 2px 10px;
  border-radius: 999px;
}

.dash-attention-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dash-attention-row {
  display: flex;
  align-items: center;
  gap: var(--dash-s-3);
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--dash-bg-raised);
  border-left: 3px solid var(--dash-border-strong);
  transition: background 120ms ease;
}

.dash-attention-row:hover { background: #20263A; }
.dash-attention-row.is-warning { border-left-color: var(--dash-accent-warning); }
.dash-attention-row.is-danger  { border-left-color: var(--dash-accent-danger); }

.dash-attention-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--dash-text-secondary);
  width: 110px;
  flex-shrink: 0;
}

.dash-attention-row.is-warning .dash-attention-tag { color: var(--dash-accent-warning); }
.dash-attention-row.is-danger  .dash-attention-tag { color: var(--dash-accent-danger); }

.dash-attention-body { flex: 1; min-width: 0; }
.dash-attention-title {
  color: var(--dash-text-primary);
  font-size: 14px;
  font-weight: 500;
}
.dash-attention-sub {
  color: var(--dash-text-secondary);
  font-size: 12px;
  margin-top: 2px;
}

.dash-attention-action {
  background: transparent;
  border: 1px solid var(--dash-border-strong);
  color: var(--dash-text-primary);
  padding: 6px 12px;
  border-radius: 8px;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.dash-attention-action:hover {
  background: var(--dash-accent-primary);
  border-color: var(--dash-accent-primary);
}

.dash-attention-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 28px 16px;
  text-align: center;
}

.dash-attention-empty p {
  color: var(--dash-text-secondary);
  font-size: 14px;
}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/components/dashboard/AttentionPanel.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): add AttentionPanel with empty state"
```

---

## Task 9: RecommendationsCard

**Files:**
- Create: `dashboard/frontend/src/components/dashboard/RecommendationsCard.jsx`
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Create the component**

```jsx
import { useNavigate } from 'react-router-dom';
import { Award } from 'lucide-react';

function scoreColor(score) {
  if (score >= 80) return 'var(--dash-accent-success)';
  if (score >= 60) return 'var(--dash-accent-warning)';
  return 'var(--dash-accent-danger)';
}

export default function RecommendationsCard({ recommendations = [] }) {
  const navigate = useNavigate();
  const top3 = recommendations.slice(0, 3);

  return (
    <div className="dash-card dash-recos">
      <div className="dash-card-header">
        <span className="dash-label"><Award size={12} style={{ marginRight: 4, verticalAlign: -1 }} />Top recommendations · this week</span>
      </div>

      {top3.length === 0 ? (
        <div className="dash-attention-empty">
          <p style={{ color: 'var(--dash-text-secondary)', fontSize: 13 }}>No evaluations yet.</p>
        </div>
      ) : (
        <ul className="dash-recos-list">
          {top3.map((r, idx) => (
            <li
              key={r.request_id || idx}
              className="dash-recos-row"
              onClick={() => navigate(`/request/${r.request_id}`)}
              tabIndex={0}
              role="button"
              onKeyDown={(e) => { if (e.key === 'Enter') navigate(`/request/${r.request_id}`); }}
            >
              <span className="dash-recos-rank">{idx + 1}</span>
              <div className="dash-recos-body">
                <div className="dash-recos-supplier">{r.supplier_name}</div>
                <div className="dash-recos-product">{r.product}</div>
              </div>
              <div className="dash-recos-score dash-num" style={{ color: scoreColor(r.overall_score || 0) }}>
                {(r.overall_score ?? 0).toFixed(0)}
                <span className="dash-recos-score-suffix">/100</span>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="dash-card-footer">
        <a className="dash-link" onClick={(e) => { e.preventDefault(); navigate('/reports'); }} href="/reports">
          View all evaluations →
        </a>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add styles**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
.dash-recos-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dash-recos-row {
  display: flex;
  align-items: center;
  gap: var(--dash-s-3);
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  background: transparent;
  transition: background 120ms ease;
}

.dash-recos-row:hover { background: var(--dash-bg-raised); }

.dash-recos-rank {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  border-radius: 6px;
  background: var(--dash-accent-primary);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.dash-recos-body { flex: 1; min-width: 0; }
.dash-recos-supplier {
  font-size: 13px;
  font-weight: 600;
  color: var(--dash-text-primary);
}
.dash-recos-product {
  font-size: 11px;
  color: var(--dash-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-recos-score {
  font-size: 20px;
  font-weight: 700;
}
.dash-recos-score-suffix {
  font-size: 11px;
  color: var(--dash-text-muted);
  margin-left: 2px;
  font-weight: 500;
}

.dash-card-footer {
  margin-top: var(--dash-s-3);
  padding-top: var(--dash-s-3);
  border-top: 1px solid var(--dash-border-subtle);
}

.dash-link {
  font-size: 12px;
  color: var(--dash-accent-primary);
  text-decoration: none;
  font-weight: 600;
  cursor: pointer;
}
.dash-link:hover { text-decoration: underline; }
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/components/dashboard/RecommendationsCard.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): add RecommendationsCard"
```

---

## Task 10: TrendChart

**Files:**
- Create: `dashboard/frontend/src/components/dashboard/TrendChart.jsx`
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Create the component**

```jsx
import { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Bar, ComposedChart } from 'recharts';
import { MOCK_TREND, MOCK_TREND_PREVIOUS } from '../../mocks/dashboardMocks';

const METRICS = [
  { id: 'savings', label: 'Savings',    suffix: ' TND', color: '#10B981' },
  { id: 'cycle',   label: 'Cycle time', suffix: 'h',    color: '#6366F1' },
  { id: 'volume',  label: 'Volume',     suffix: ' TND', color: '#A78BFA' },
];

const PERIODS = [
  { id: '7d',  label: '7d' },
  { id: '30d', label: '30d' },
  { id: '90d', label: '90d' },
];

function formatNumber(v) {
  if (v == null) return '—';
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000)     return `${(v / 1_000).toFixed(1)}K`;
  return v.toFixed(1);
}

function CustomTooltip({ active, payload, suffix }) {
  if (!active || !payload || !payload.length) return null;
  const p = payload[0].payload;
  return (
    <div className="dash-trend-tooltip">
      <div className="dash-trend-tooltip-date">{p.date}</div>
      <div className="dash-trend-tooltip-value dash-num">
        {formatNumber(p.value)}{suffix}
      </div>
      <div className="dash-trend-tooltip-meta dash-num">
        {p.requests} requests
      </div>
    </div>
  );
}

export default function TrendChart() {
  const [metricId, setMetricId] = useState('savings');
  const [periodId, setPeriodId] = useState('30d');

  const metric = METRICS.find(m => m.id === metricId);
  const data = MOCK_TREND[metricId][periodId];
  const previous = MOCK_TREND_PREVIOUS[metricId][periodId];
  const current = data.reduce((acc, p) => acc + p.value, 0);
  const deltaPct = previous ? Math.round((current - previous) / previous * 100) : 0;

  return (
    <div className="dash-card dash-trend">
      <div className="dash-trend-header">
        <span className="dash-label">Performance trend</span>
        <div className="dash-trend-tabs" role="tablist">
          {METRICS.map(m => (
            <button
              key={m.id}
              role="tab"
              aria-selected={m.id === metricId}
              className={`dash-trend-tab ${m.id === metricId ? 'is-active' : ''}`}
              onClick={() => setMetricId(m.id)}
            >
              {m.label}
            </button>
          ))}
        </div>
        <div className="dash-trend-periods" role="tablist">
          {PERIODS.map(p => (
            <button
              key={p.id}
              role="tab"
              aria-selected={p.id === periodId}
              className={`dash-trend-period ${p.id === periodId ? 'is-active' : ''}`}
              onClick={() => setPeriodId(p.id)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="dash-trend-summary">
        <span className="dash-trend-summary-value dash-num">{formatNumber(current)}{metric.suffix}</span>
        <span className="dash-trend-summary-delta dash-num" style={{ color: deltaPct >= 0 ? 'var(--dash-accent-success)' : 'var(--dash-accent-danger)' }}>
          {deltaPct >= 0 ? '▲' : '▼'} {Math.abs(deltaPct)}% vs previous {periodId}
        </span>
      </div>

      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer>
          <ComposedChart data={data} margin={{ top: 10, right: 16, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={metric.color} stopOpacity={0.4} />
                <stop offset="100%" stopColor={metric.color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#1F2533" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: '#5A6275' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(d) => d.slice(5)}
            />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11, fill: '#5A6275' }}
              axisLine={false}
              tickLine={false}
              width={40}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11, fill: '#5A6275' }}
              axisLine={false}
              tickLine={false}
              width={30}
            />
            <Tooltip content={<CustomTooltip suffix={metric.suffix} />} cursor={{ stroke: '#2A3142', strokeWidth: 1 }} />
            <Bar yAxisId="right" dataKey="requests" fill="#1F2533" barSize={6} radius={[2,2,0,0]} />
            <Area yAxisId="left" type="monotone" dataKey="value" stroke={metric.color} strokeWidth={2} fill="url(#trendGradient)" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add styles**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
.dash-trend-header {
  display: flex;
  align-items: center;
  gap: var(--dash-s-4);
  margin-bottom: var(--dash-s-3);
  flex-wrap: wrap;
}

.dash-trend-tabs,
.dash-trend-periods {
  display: inline-flex;
  background: var(--dash-bg-raised);
  border-radius: 8px;
  padding: 3px;
  gap: 2px;
}

.dash-trend-tabs { margin-right: auto; }

.dash-trend-tab,
.dash-trend-period {
  background: transparent;
  border: none;
  color: var(--dash-text-secondary);
  padding: 6px 12px;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
}

.dash-trend-tab.is-active,
.dash-trend-period.is-active {
  background: var(--dash-bg-elevated);
  color: var(--dash-text-primary);
  box-shadow: inset 0 0 0 1px var(--dash-border-strong);
}

.dash-trend-summary {
  display: flex;
  align-items: baseline;
  gap: var(--dash-s-3);
  margin-bottom: var(--dash-s-3);
}

.dash-trend-summary-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--dash-text-primary);
}

.dash-trend-summary-delta {
  font-size: 12px;
  font-weight: 600;
}

.dash-trend-tooltip {
  background: var(--dash-bg-base);
  border: 1px solid var(--dash-border-strong);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 12px;
  color: var(--dash-text-primary);
}

.dash-trend-tooltip-date {
  color: var(--dash-text-muted);
  font-size: 11px;
  margin-bottom: 2px;
}

.dash-trend-tooltip-value {
  font-size: 16px;
  font-weight: 700;
}

.dash-trend-tooltip-meta {
  color: var(--dash-text-secondary);
  font-size: 11px;
  margin-top: 2px;
}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/components/dashboard/TrendChart.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): add TrendChart with metric/period toggles"
```

---

## Task 11: CategoryBreakdown

**Files:**
- Create: `dashboard/frontend/src/components/dashboard/CategoryBreakdown.jsx`
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Create the component**

```jsx
import { MOCK_CATEGORY_SPEND } from '../../mocks/dashboardMocks';

function formatTND(n) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M TND`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K TND`;
  return `${n} TND`;
}

export default function CategoryBreakdown({ rows = MOCK_CATEGORY_SPEND }) {
  const max = Math.max(...rows.map(r => r.amount), 1);
  return (
    <div className="dash-card dash-cats">
      <div className="dash-card-header">
        <span className="dash-label">Spend by category</span>
      </div>
      <ul className="dash-cats-list">
        {rows.map(r => {
          const pct = (r.amount / max) * 100;
          return (
            <li key={r.category} className="dash-cats-row">
              <span className="dash-cats-name">{r.category}</span>
              <span className="dash-cats-bar-track">
                <span className="dash-cats-bar-fill" style={{ width: `${pct}%` }} />
              </span>
              <span className="dash-cats-amount dash-num">{formatTND(r.amount)}</span>
            </li>
          );
        })}
      </ul>
      <div className="dash-card-footer">
        <a className="dash-link" href="#" onClick={e => e.preventDefault()}>View all categories →</a>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add styles**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
.dash-cats-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dash-cats-row {
  display: grid;
  grid-template-columns: 130px 1fr 90px;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}

.dash-cats-name {
  color: var(--dash-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-cats-bar-track {
  display: block;
  height: 6px;
  background: var(--dash-bg-raised);
  border-radius: 4px;
  overflow: hidden;
}

.dash-cats-bar-fill {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--dash-accent-primary), #8B91F4);
  border-radius: 4px;
}

.dash-cats-amount {
  text-align: right;
  color: var(--dash-text-primary);
  font-weight: 600;
}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/components/dashboard/CategoryBreakdown.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): add CategoryBreakdown horizontal bar list"
```

---

## Task 12: PipelineFlow

**Files:**
- Create: `dashboard/frontend/src/components/dashboard/PipelineFlow.jsx`
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Create the component**

```jsx
import { useNavigate } from 'react-router-dom';

const STAGES = [
  { key: 'received',           label: 'Received',  statuses: ['pending'] },
  { key: 'analyzing',          label: 'Analysis',  statuses: ['analyzing'] },
  { key: 'sourcing',           label: 'Sourcing',  statuses: ['sourcing'] },
  { key: 'rfqs_sent',          label: 'RFQs',      statuses: ['rfqs_sent'] },
  { key: 'awaiting_responses', label: 'Awaiting',  statuses: ['awaiting_responses', 'offers_received'] },
  { key: 'evaluated',          label: 'Evaluated', statuses: ['evaluated', 'evaluation_sent'] },
  { key: 'completed',          label: 'Done',      statuses: ['completed', 'po_generated'] },
];

export default function PipelineFlow({ statusBreakdown = {} }) {
  const navigate = useNavigate();
  const counts = STAGES.map(s => ({
    ...s,
    count: s.statuses.reduce((sum, st) => sum + (statusBreakdown[st] || 0), 0),
  }));

  const total = counts.reduce((sum, s) => sum + s.count, 0);
  const bottleneck = counts.reduce((max, s) => (s.count > max.count ? s : max), counts[0]);

  return (
    <div className="dash-card dash-pipeline">
      <div className="dash-card-header">
        <span className="dash-label">Procurement pipeline</span>
        <span className="dash-pill">{total} active flows</span>
      </div>

      <div className="dash-pipeline-flow">
        {counts.map((stage, idx) => {
          const isBottleneck = stage.count > 0 && stage.key === bottleneck.key;
          return (
            <div key={stage.key} className="dash-pipeline-stage-wrap">
              <button
                className={`dash-pipeline-stage ${isBottleneck ? 'is-bottleneck' : ''}`}
                onClick={() => navigate(`/pipelines?status=${stage.key}`)}
              >
                <span className="dash-pipeline-stage-count dash-num">{stage.count}</span>
                <span className="dash-pipeline-stage-label">{stage.label}</span>
              </button>
              {idx < counts.length - 1 && <div className="dash-pipeline-track" />}
            </div>
          );
        })}
      </div>

      {bottleneck.count > 0 && total > 0 && (
        <div className="dash-pipeline-callout">
          ↑ bottleneck: <strong>{bottleneck.label}</strong> ({bottleneck.count} pending)
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add styles**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
.dash-pipeline-flow {
  display: flex;
  align-items: center;
  margin: 8px 0 4px;
}

.dash-pipeline-stage-wrap {
  display: flex;
  align-items: center;
  flex: 1;
}

.dash-pipeline-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--dash-bg-raised);
  border: 1px solid var(--dash-border-strong);
  border-radius: 10px;
  padding: 10px 14px;
  min-width: 86px;
  cursor: pointer;
  font: inherit;
  color: inherit;
}

.dash-pipeline-stage:hover {
  border-color: var(--dash-accent-primary);
}

.dash-pipeline-stage.is-bottleneck {
  border-color: var(--dash-accent-warning);
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.15);
}

.dash-pipeline-stage-count {
  font-size: 18px;
  font-weight: 700;
  color: var(--dash-text-primary);
}

.dash-pipeline-stage-label {
  font-size: 11px;
  color: var(--dash-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 2px;
}

.dash-pipeline-track {
  flex: 1;
  height: 2px;
  background: var(--dash-border-subtle);
  margin: 0 6px;
}

.dash-pipeline-callout {
  margin-top: 12px;
  font-size: 12px;
  color: var(--dash-accent-warning);
}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/components/dashboard/PipelineFlow.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): add horizontal PipelineFlow with bottleneck callout"
```

---

## Task 13: SuppliersLeaderboard

**Files:**
- Create: `dashboard/frontend/src/components/dashboard/SuppliersLeaderboard.jsx`
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Create the component**

```jsx
import { useNavigate } from 'react-router-dom';
import { MOCK_TOP_SUPPLIERS } from '../../mocks/dashboardMocks';

function scoreColor(score) {
  if (score >= 80) return 'var(--dash-accent-success)';
  if (score >= 60) return 'var(--dash-accent-warning)';
  return 'var(--dash-accent-danger)';
}

function relativeDays(days) {
  if (days === 0) return 'today';
  if (days === 1) return 'yesterday';
  return `${days}d ago`;
}

export default function SuppliersLeaderboard({ rows = MOCK_TOP_SUPPLIERS }) {
  const navigate = useNavigate();
  return (
    <div className="dash-card dash-suppliers">
      <div className="dash-card-header">
        <span className="dash-label">Top suppliers · last 30 days</span>
        <a className="dash-link" href="/suppliers" onClick={(e) => { e.preventDefault(); navigate('/suppliers'); }}>
          View all →
        </a>
      </div>

      <table className="dash-suppliers-table">
        <thead>
          <tr>
            <th style={{ width: 36 }}>#</th>
            <th>Supplier</th>
            <th style={{ width: 140 }}>Category</th>
            <th style={{ width: 140 }}>Response rate</th>
            <th style={{ width: 80, textAlign: 'right' }}>Score</th>
            <th style={{ width: 100 }}>Last seen</th>
            <th style={{ width: 32 }}></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((s, i) => (
            <tr key={s.id}>
              <td className="dash-num">{i + 1}</td>
              <td>
                <div className="dash-suppliers-name">{s.name}</div>
                <div className="dash-suppliers-email">{s.email}</div>
              </td>
              <td>
                <span className="dash-tag">{s.category}</span>
              </td>
              <td>
                <div className="dash-suppliers-bar-track">
                  <div className="dash-suppliers-bar-fill" style={{ width: `${s.responseRate}%` }} />
                </div>
                <div className="dash-suppliers-bar-label dash-num">{s.responseRate}%</div>
              </td>
              <td className="dash-num" style={{ textAlign: 'right', fontSize: 16, fontWeight: 700, color: scoreColor(s.avgScore) }}>
                {s.avgScore.toFixed(1)}
              </td>
              <td className="dash-suppliers-last">{relativeDays(s.lastInteractionDays)}</td>
              <td>
                <button className="dash-suppliers-chev" onClick={() => navigate('/suppliers')} aria-label="Open supplier">→</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Add styles**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
.dash-suppliers-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.dash-suppliers-table th {
  text-align: left;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--dash-text-muted);
  padding: 8px 10px;
  border-bottom: 1px solid var(--dash-border-subtle);
}

.dash-suppliers-table td {
  padding: 12px 10px;
  border-bottom: 1px solid var(--dash-border-subtle);
  color: var(--dash-text-primary);
  vertical-align: middle;
}

.dash-suppliers-table tr:last-child td {
  border-bottom: none;
}

.dash-suppliers-name {
  font-weight: 600;
}

.dash-suppliers-email {
  font-size: 11px;
  color: var(--dash-text-muted);
  margin-top: 2px;
}

.dash-tag {
  display: inline-block;
  background: var(--dash-bg-raised);
  border: 1px solid var(--dash-border-strong);
  color: var(--dash-text-secondary);
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
}

.dash-suppliers-bar-track {
  height: 5px;
  background: var(--dash-bg-raised);
  border-radius: 3px;
  overflow: hidden;
}

.dash-suppliers-bar-fill {
  height: 100%;
  background: var(--dash-accent-primary);
}

.dash-suppliers-bar-label {
  font-size: 11px;
  color: var(--dash-text-secondary);
  margin-top: 4px;
}

.dash-suppliers-last {
  color: var(--dash-text-secondary);
  font-size: 12px;
}

.dash-suppliers-chev {
  background: transparent;
  border: 1px solid var(--dash-border-strong);
  color: var(--dash-text-secondary);
  width: 28px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.dash-suppliers-chev:hover {
  background: var(--dash-accent-primary);
  border-color: var(--dash-accent-primary);
  color: white;
}
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/components/dashboard/SuppliersLeaderboard.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): add SuppliersLeaderboard table"
```

---

## Task 14: Compose the new KpisPage

**Files:**
- Modify: `dashboard/frontend/src/pages/KpisPage.jsx` (full rewrite)
- Modify: `dashboard/frontend/src/styles/dashboard.css`

- [ ] **Step 1: Rewrite `KpisPage.jsx`**

Replace the entire content of `dashboard/frontend/src/pages/KpisPage.jsx`:

```jsx
import { useEffect, useMemo, useState } from 'react';
import { useApi } from '../hooks/useApi';
import HeroHeader from '../components/dashboard/HeroHeader';
import ScoreboardCard from '../components/dashboard/ScoreboardCard';
import Sparkline from '../components/dashboard/Sparkline';
import DotScale from '../components/dashboard/DotScale';
import LiveAIStrip from '../components/dashboard/LiveAIStrip';
import AttentionPanel from '../components/dashboard/AttentionPanel';
import RecommendationsCard from '../components/dashboard/RecommendationsCard';
import TrendChart from '../components/dashboard/TrendChart';
import CategoryBreakdown from '../components/dashboard/CategoryBreakdown';
import PipelineFlow from '../components/dashboard/PipelineFlow';
import SuppliersLeaderboard from '../components/dashboard/SuppliersLeaderboard';
import { SkeletonCard } from '../components/dashboard/Skeleton';
import {
  MOCK_SPARKLINES, MOCK_DELTAS, MOCK_ATTENTION, MOCK_AGENT_ACTIVITY,
} from '../mocks/dashboardMocks';

function formatNumber(n) {
  if (!n && n !== 0) return '0';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

const ACTIVE_STATUSES = [
  'pending', 'analyzing', 'sourcing', 'rfqs_sent', 'awaiting_responses', 'offers_received',
];

export default function KpisPage() {
  const [period, setPeriod] = useState('30d');
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const { data: kpis, loading, error } = useApi('/dashboard/kpis', { interval: 15000 });
  const { data: recsData } = useApi('/dashboard/recommendations', { interval: 30000 });

  useEffect(() => {
    if (kpis) setLastUpdated(new Date());
  }, [kpis]);

  const activeCount = useMemo(() => {
    if (!kpis?.status_breakdown) return 0;
    return ACTIVE_STATUSES.reduce((s, st) => s + (kpis.status_breakdown[st] || 0), 0);
  }, [kpis]);

  const attentionItems = MOCK_ATTENTION; // Plan B: replace with useApi('/dashboard/attention')
  const alertCount = attentionItems.length;

  // Map active count (0..n) to a 0..9 dot scale
  const dotsFilled = Math.min(9, activeCount);
  const dotsAlertFrom = Math.max(1, dotsFilled - alertCount + 1);

  if (loading) {
    return (
      <div className="dash">
        <div className="dash-too-narrow">
          <strong>This dashboard is best viewed on a desktop.</strong>
          <span>Please switch to a screen at least 1024px wide.</span>
        </div>
        <div className="dash-tier">
          <div className="dash-scoreboard">
            <SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard />
          </div>
        </div>
        <div className="dash-tier"><SkeletonCard height={64} /></div>
        <div className="dash-tier dash-grid-2-1">
          <SkeletonCard height={260} /><SkeletonCard height={260} />
        </div>
        <div className="dash-tier dash-grid-3-2">
          <SkeletonCard height={400} /><SkeletonCard height={400} />
        </div>
        <div className="dash-tier"><SkeletonCard height={140} /></div>
        <div className="dash-tier"><SkeletonCard height={300} /></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dash">
        <div className="dash-card" style={{ color: 'var(--dash-accent-danger)' }}>
          Failed to load dashboard: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="dash">
      <div className="dash-too-narrow">
        <strong>This dashboard is best viewed on a desktop.</strong>
        <span>Please switch to a screen at least 1024px wide.</span>
      </div>

      {/* Tier 1: Hero */}
      <div className="dash-tier">
        <HeroHeader period={period} onPeriodChange={setPeriod} lastUpdated={lastUpdated} />

        <div className="dash-scoreboard">
          <ScoreboardCard
            label="Savings"
            value={`${formatNumber(kpis.savings_tnd || 0)} TND`}
            delta={MOCK_DELTAS.savings}
            deltaSuffix="% MoM"
            improvementDirection="higher"
            accent="success"
            visual={<Sparkline data={MOCK_SPARKLINES.savings} color="#10B981" ariaLabel="Savings trend last 30 days" />}
          />
          <ScoreboardCard
            label="Cycle time"
            value={`${kpis.avg_cycle_hours?.toFixed(1) || '—'}h`}
            delta={MOCK_DELTAS.cycle}
            deltaSuffix="% MoM"
            improvementDirection="lower"
            accent="primary"
            visual={<Sparkline data={MOCK_SPARKLINES.cycle} color="#6366F1" ariaLabel="Cycle time trend" />}
          />
          <ScoreboardCard
            label="Success rate"
            value={`${kpis.success_rate ?? 0}%`}
            delta={MOCK_DELTAS.success}
            deltaSuffix=" pts"
            improvementDirection="higher"
            accent="primary"
            visual={<Sparkline data={MOCK_SPARKLINES.success} color="#6366F1" ariaLabel="Success rate trend" />}
          />
          <ScoreboardCard
            label="Active pipelines"
            value={activeCount}
            delta={null}
            accent={alertCount > 0 ? 'warning' : 'primary'}
            alertText={alertCount > 0 ? `${alertCount} need you` : null}
            visual={<DotScale filled={dotsFilled} alertFrom={dotsAlertFrom} ariaLabel={`${activeCount} active pipelines`} />}
          />
        </div>

        <LiveAIStrip agents={MOCK_AGENT_ACTIVITY.agents} status={MOCK_AGENT_ACTIVITY.status} />
      </div>

      {/* Tier 2: Action zone */}
      <div className="dash-tier dash-grid-2-1">
        <AttentionPanel items={attentionItems} />
        <RecommendationsCard recommendations={recsData?.recommendations || []} />
      </div>

      {/* Tier 3: Insight zone */}
      <div className="dash-tier dash-grid-3-2">
        <TrendChart />
        <CategoryBreakdown />
      </div>

      {/* Tier 4: Operational zone */}
      <div className="dash-tier">
        <PipelineFlow statusBreakdown={kpis.status_breakdown || {}} />
      </div>
      <div className="dash-tier">
        <SuppliersLeaderboard />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add layout grid styles**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
.dash-grid-2-1 {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--dash-s-6);
}

.dash-grid-3-2 {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: var(--dash-s-6);
}
```

- [ ] **Step 3: Verify in the browser**

Run: `cd dashboard/frontend && npm run dev`

Open `http://localhost:5173/`. Visual checklist:

- [ ] Page background is deep navy (`#0B0E14`).
- [ ] Greeting + month + period selector + "Updated Xs ago" pill appear at the top.
- [ ] 4 scoreboard cards in a row, each with a colored top accent line, big number, delta with arrow, and a sparkline (cards 1–3) or 9 dots (card 4).
- [ ] Below the cards, a single live-AI strip with 5 agent nodes connected by animated dashes; one node has a pulsing purple halo; right side shows a green "Operational" pill.
- [ ] Below: "Needs your attention" card on the left (3 rows) + "Top recommendations" on the right.
- [ ] Below: trend chart (left, ~280px tall, with metric tabs and period toggle) + Spend by category (right).
- [ ] Below: full-width pipeline with 7 stages + bottleneck callout.
- [ ] Bottom: top-5 suppliers table.
- [ ] Page must NOT have any leftover light-mode styling from the old layout.
- [ ] Resize the window below 1024px → the "best viewed on desktop" message replaces everything.
- [ ] Open browser dev tools → toggle "Emulate prefers-reduced-motion: reduce" → all animations stop.

If any check fails, fix it before committing. Common issues:
- Recharts colors not picking up the theme → check the `metric.color` literals in `TrendChart.jsx`.
- Sparkline blank → confirm `MOCK_SPARKLINES.{savings,cycle,success}` are arrays of 30 numbers.

- [ ] **Step 4: Commit**

```bash
git add dashboard/frontend/src/pages/KpisPage.jsx dashboard/frontend/src/styles/dashboard.css
git commit -m "feat(dashboard): rewrite KpisPage as four-tier executive dashboard"
```

---

## Task 15: Final polish — top header live dot color

**Files:**
- Modify: `dashboard/frontend/src/styles/dashboard.css`

The existing `top-header` (in `App.css`) sits above `.dash` in the layout. Its `live-dot` color uses the old turquoise theme; we tint it to match the new accent without touching `App.css`.

- [ ] **Step 1: Override the top-header styles for the dashboard route only**

Append to `dashboard/frontend/src/styles/dashboard.css`:

```css
/* Tint the top header's live dot to match the dashboard accent
   when the dashboard is mounted (uses :has, supported in modern browsers). */
body:has(.dash) .top-header {
  background: var(--dash-bg-base);
  border-bottom: 1px solid var(--dash-border-subtle);
}

body:has(.dash) .top-header h1 {
  color: var(--dash-text-primary);
}

body:has(.dash) .live-dot {
  background: var(--dash-accent-success);
  box-shadow: 0 0 6px var(--dash-accent-success);
}

/* Eliminate the page-content padding around the dashboard,
   since .dash provides its own padding. */
body:has(.dash) .page-content {
  padding: 0;
}
```

- [ ] **Step 2: Verify visually**

Run: `cd dashboard/frontend && npm run dev`. The top header above the dashboard should now seamlessly extend the dark theme; the live dot should be green; no extra padding around the dashboard.

- [ ] **Step 3: Commit**

```bash
git add dashboard/frontend/src/styles/dashboard.css
git commit -m "style(dashboard): align top-header chrome with dashboard tokens"
```

---

## Task 16: Acceptance walkthrough

This task contains no code — it is the explicit acceptance gate from spec §12.

- [ ] **Step 1: Run through every acceptance criterion in the spec**

Open the spec at `docs/superpowers/specs/2026-05-03-executive-dashboard-design.md` §12 and verify each item in the running app:

- [ ] (1) The four tiers render exactly as described.
- [ ] (2) Design tokens are used consistently (no inline hex codes for tokenized colors in JSX). Spot-check `KpisPage.jsx` and the components.
- [ ] (3) Live AI strip animates and shows the mock per-agent counts. Hover a node → tooltip shows p95 latency and tokens/min.
- [ ] (4) `AttentionPanel` renders the 3 mock rows. Temporarily comment out `MOCK_ATTENTION` and pass `[]` to verify the empty state.
- [ ] (5) Trend chart switches between 3 metrics and 3 periods without page reload.
- [ ] (6) Skeleton loading states render during the initial load (force a slow network in dev tools to see them).
- [ ] (7) Tab through the page with the keyboard — every interactive element shows a visible focus ring.
- [ ] (8) Toggle `prefers-reduced-motion: reduce` in dev tools → all animations stop.
- [ ] (9) `Ctrl+P` (print preview) → light-mode export, live-AI strip hidden.
- [ ] (10) The top KPI numbers still match the values the old dashboard showed (compare `kpis.total_requests`, `kpis.success_rate`, `kpis.savings_tnd`).

- [ ] **Step 2: If any acceptance check fails, file follow-up tasks in this plan and fix before declaring done.**

- [ ] **Step 3: Commit (if any fixes were needed)**

```bash
git add -A
git commit -m "chore(dashboard): fixes from acceptance walkthrough"
```

---

## What Plan B will do (for context, not part of this plan)

1. Delete `dashboard/frontend/src/mocks/dashboardMocks.js`.
2. Add backend endpoints `/dashboard/attention`, `/dashboard/trend`, `/dashboard/top-suppliers`.
3. Extend `/dashboard/kpis` with `sparkline.{savings,cycle,success}`, `spend_by_category`, and per-agent live activity.
4. In each component currently importing from `dashboardMocks`, replace the import with a `useApi(...)` call. The component shapes stay identical, so no other code changes are needed.
