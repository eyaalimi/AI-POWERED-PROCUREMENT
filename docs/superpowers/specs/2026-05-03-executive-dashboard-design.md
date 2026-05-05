# Executive Procurement Dashboard — Design Spec

**Date:** 2026-05-03
**Owner:** Eya
**Scope:** Redesign of `dashboard/frontend/src/pages/KpisPage.jsx` (the main dashboard route `/`) and the supporting design system in `App.css` / `index.css`. Other pages (Inbox, Pipelines, Suppliers, etc.) inherit the new design tokens but their layouts are out of scope for this spec.
**Status:** Draft — awaiting user review

---

## 1. Goal

Transform the current main dashboard from a generic admin template into an **executive control tower** that earns the trust of supervisors across four personas in a single view:

- **Procurement Director** — wants ROI, supplier performance, cycle times.
- **CFO** — wants budget burn, savings, audit-grade clean numbers.
- **COO** — wants pipeline health, bottlenecks, what is stuck.
- **CEO / Board demo** — wants the wow effect: AI agents working live, modernity.

The dashboard must communicate three things in the first 3 seconds: **(1) money saved**, **(2) the system is alive and working**, **(3) here is what needs your attention**.

## 2. Non-goals

- No redesign of secondary pages (Inbox, Pipelines, Suppliers, Reports, etc.) — they inherit the tokens but keep their current layouts.
- No mobile-first redesign. Target viewport is **≥ 1280px** (desktop, supervisors). Reasonable degradation down to 1024px is required; below that we show a "best viewed on desktop" message.
- No marketing copy, illustrations, or onboarding flow.
- New backend endpoints required by the redesign are enumerated in §7 but their implementation belongs in the plan, not this spec.

## 3. Visual system

### 3.1 Color tokens (CSS variables on `:root`)

```
/* Surface */
--bg-base:        #0B0E14
--bg-elevated:    #131722
--bg-raised:      #1A1F2E
--border-subtle:  #1F2533
--border-strong:  #2A3142

/* Text */
--text-primary:   #E8ECF4
--text-secondary: #8B93A7
--text-muted:     #5A6275

/* Semantic accents */
--accent-primary: #6366F1   /* indigo — primary actions, primary KPI */
--accent-success: #10B981   /* savings, completed, positive deltas */
--accent-warning: #F59E0B   /* needs attention, pending */
--accent-danger:  #EF4444   /* blocked, over budget, negative critical */
--accent-ai:      #A78BFA   /* reserved for live AI activity ONLY */

/* Gradients (used sparingly) */
--gradient-hero:  linear-gradient(135deg, rgba(99,102,241,0.12), rgba(167,139,250,0.06))
--gradient-glow:  radial-gradient(circle at top right, rgba(167,139,250,0.15), transparent 70%)
```

**Rules:**
- `--accent-ai` (purple) is used **exclusively** in the Live AI strip and the sidebar badge counters. Using it elsewhere dilutes the "agentic" signal.
- Deltas use **directional shapes** (▲ ▼) in addition to color so they remain readable for color-blind users.
- All foreground/background combinations meet **WCAG AA** contrast (verified during implementation).

### 3.2 Typography

- Family: **Inter**, fallback `system-ui, 'Segoe UI', Roboto, sans-serif`.
- All numerals use `font-variant-numeric: tabular-nums` globally — non-negotiable for trust.
- Optical adjustments: `font-feature-settings: "ss01", "cv11"` on body to enable Inter's modern numerals where supported.

| Role           | Size | Weight | Letter-spacing |
|----------------|------|--------|----------------|
| Hero metric    | 48px | 600    | -0.02em        |
| Card metric    | 28px | 600    | -0.01em        |
| Section title  | 14px | 600    | 0              |
| Body           | 14px | 400    | 0              |
| Uppercase label| 11px | 600    | +0.08em        |
| Micro / table  | 12px | 500    | 0              |

### 3.3 Spacing scale

`4 / 8 / 12 / 16 / 24 / 32 / 48` px.
- Card internal padding: **24px**.
- Card-to-card gap: **16px**.
- Section-to-section gap: **32px**.

### 3.4 Card shell (the building block)

```
background:    var(--bg-elevated)
border:        1px solid var(--border-subtle)
border-radius: 12px
padding:       24px
```

- Interactive cards on hover: `border-color: var(--border-strong)` + 1px inner ring (`box-shadow: inset 0 0 0 1px var(--border-strong)`).
- **No drop shadows** anywhere except inside the hero zone, where one soft shadow `0 8px 32px rgba(0,0,0,0.32)` is allowed on the four scoreboard cards.
- Borders, not shadows, give the "professional, not playful" feel.

### 3.5 Motion

Motion is rationed deliberately. The dashboard has **only three** moving things:
1. The Live AI strip (animated dashes between agent nodes, `animation: 3s linear infinite`).
2. The active agent's halo pulse (`box-shadow` pulse, 2s ease-in-out infinite).
3. The "Updated Xs ago" pill (tiny opacity pulse on each refresh).

Nothing else animates. No card hover transforms, no chart entry animations, no parallax. Restraint is the design.

`prefers-reduced-motion: reduce` disables all three.

## 4. Layout — Tier-by-tier

The dashboard is composed of four vertical tiers separated by 32px gaps. All tiers occupy the full content width.

### 4.1 Tier 1 — Hero zone (~360px tall)

**Sub-header row** (above the cards, 48px tall):
- Left: greeting + month — `Welcome back, {user.name} · {Month YYYY}` in `--text-secondary`.
- Right: period selector dropdown `[Last 30 days ▾]` (also drives the Tier 3 trend chart's default period).
- Far right (small): live status pill `↻ Updated Xs ago` — pulses on each polling refresh (the `useApi` hook already polls every 15s).

**Four scoreboard cards** (4-column grid, 16px gap):

| # | Title             | Value source                               | Delta source                       | Visual under value         |
|---|-------------------|--------------------------------------------|------------------------------------|----------------------------|
| 1 | SAVINGS           | `kpis.savings_tnd` (formatted "142,380")  | MoM % change                       | Sparkline (60px tall)      |
| 2 | CYCLE TIME        | `kpis.avg_cycle_hours` ("4.2h")           | MoM % change (lower is better)     | Sparkline (60px tall)      |
| 3 | SUCCESS RATE      | `kpis.success_rate` ("87%")               | Delta in percentage points         | Sparkline (60px tall)      |
| 4 | ACTIVE PIPELINES  | Sum of in-flight statuses                 | "{n} need you" if any need attention | Dot scale (9 dots)       |

- Each card has a **3px top accent line** in its semantic color (savings=success, cycle=primary, success=primary, pipelines=warning if alerts else primary).
- Card body uses the `--gradient-hero` overlay at low opacity for premium feel.
- Delta badge color follows **direction of improvement**, not direction of the number: improvements are always `--accent-success`, regressions are always `--accent-danger`. For "lower is better" metrics (cycle time), `▼ -32%` is success-colored; for "higher is better" metrics (savings, success rate), `▲ +X%` is success-colored. The arrow always reflects the raw direction of the number.
- Sparkline data: comes from a new field `kpis.sparkline.{savings|cycle|success}` returning an array of 30 numbers. **If the field is missing, the sparkline is omitted** (the card still works — sparkline is enhancement, not requirement).
- Card 4's dot scale: 9 dots representing capacity buckets. Dots filled in `--accent-primary` for healthy load, last filled dots in `--accent-warning` if any pipelines need supervisor attention.

**Live AI activity strip** (below the cards, ~64px tall, full width):
- Background: `var(--bg-elevated)` with `--gradient-glow` painted in the top-right corner.
- Left: small uppercase label `LIVE AI` in `--text-muted`.
- Center: 5 agent nodes — `Analysis → Sourcing → Communication → Evaluation → Storage` — connected by thin animated dashed lines (`stroke-dasharray` animation, 3s loop). Each node is a 36px circle with the agent name below (12px, `--text-secondary`) and a count pill above (number of items currently in that stage).
- The agent currently executing shows a soft pulsing halo in `--accent-ai`.
- Right: status pill — `● Operational` (green dot + label), turns `● Degraded` (amber) if any agent reported errors in the last 5 minutes.
- Hover on a node: tooltip with the agent's p95 latency and tokens/min over the last 15 minutes.

**Data dependency:** the strip needs per-agent live counts and a last-error timestamp. The implementation plan must decide whether to extend `/dashboard/kpis` or add a new endpoint `/dashboard/agent-activity`. **Default position: extend the existing endpoint** to avoid a second polling loop.

### 4.2 Tier 2 — Action zone

Two-column grid: **2fr / 1fr**, 24px gap.

#### Left (2fr): "Needs your attention"

- Card header: `NEEDS YOUR ATTENTION` (uppercase label) + a count pill on the right (`5 items`).
- Body: list of action rows (max 5, scrollable beyond — if list exceeds 5, show "View N more →" link).
- Each row layout:
  - Left (80px): icon + category tag in row's urgency color.
  - Middle (flex-1): title (14px primary) + sub-line (12px secondary).
  - Right (~110px): primary action button.
- Row urgency categories (each gets one color from §3.1):
  - `APPROVAL` — amber — request awaiting supervisor approval.
  - `STUCK` — red — pipeline blocked > 48h with no supplier reply.
  - `BUDGET` — red — category > 80% of allocated budget.
  - `RELAUNCH` — amber — sourcing returned < 3 suppliers and may need rerun.
- Hover: row background shifts to `--bg-raised`.
- **Empty state**: `✓ Everything is on track. Nothing requires your attention.` centered, in `--text-secondary`. Empty states are designed, not blank.

**Data dependency:** this needs a new endpoint `/dashboard/attention` that returns the action items above. The implementation plan must spec this endpoint. For the first iteration, a minimal version returning `[]` is acceptable so the section ships with the empty state.

#### Right (1fr): "Top recommendations"

- Card header: `TOP RECOMMENDATIONS · this week`.
- Body: 3 ranked rows.
- Each row: rank badge (1, 2, 3) + supplier name (14px primary, bold) + product (12px secondary, single line truncated) + score on the right (large 20px tabular, color-coded: 0–60 danger, 60–80 warning, 80–100 success).
- Footer: link `View all evaluations →` to `/reports`.
- Data source: existing `useApi('/dashboard/recommendations')`.

### 4.3 Tier 3 — Insight zone

Two-column grid: **3fr / 2fr**, 24px gap.

#### Left (3fr): Performance trend chart

- Header row: `PERFORMANCE TREND` (left) + metric tab pills `[Savings] [Cycle time] [Volume]` (center) + period toggle `[7d] [30d] [90d]` (right).
- Chart: Recharts `AreaChart` (300px tall). Gradient fill at `fillOpacity: 0.2` under a smooth line in `--accent-primary`. Faded gray bars in the background show request count (secondary y-axis).
- Custom tooltip: vertical guide line on hover; tooltip shows the selected metric value, request count, and delta vs. the previous equivalent period (e.g., previous 30 days).
- X-axis ticks: 11px, `--text-muted`, tabular-nums, formatted as `MMM DD`.
- Y-axis: subtle, no axis line.

**Data dependency:** needs `/dashboard/trend?metric=savings|cycle|volume&period=7d|30d|90d` returning `{ points: [{date, value, requests}], previous_period_value }`. New endpoint, spec'd in the implementation plan.

#### Right (2fr): Spend by category

- Header: `SPEND BY CATEGORY`.
- Body: 5–7 horizontal bar rows, sorted descending by amount.
- Each row: category name (left, 13px) + horizontal bar (filled proportional to max, gradient from `--accent-primary` to lighter shade) + amount (right, 13px tabular).
- Footer: link `View all categories →`.

**Data dependency:** needs `kpis.spend_by_category` field on the existing endpoint, or a new `/dashboard/spend-by-category`. The implementation plan decides.

### 4.4 Tier 4 — Operational zone

#### Top: Procurement pipeline (full width)

Replaces the current 3-card workflow block. Single horizontal pipeline:

- Header: `PROCUREMENT PIPELINE` + count pill on the right (`47 active flows`).
- Body: 7 stage nodes connected by a continuous track:
  `Received → Analysis → Sourcing → RFQs → Awaiting → Evaluated → Done`
- Each node: stage label (12px secondary) + count pill (16px tabular primary) + dot.
- The stage with the highest active count is auto-highlighted as the bottleneck: subtle amber underline + a single line below the pipeline reading `↑ bottleneck: {stage} ({n} pending)`.
- Click a stage node: navigate to `/pipelines?status={stage}` (filter applied).
- Data source: existing `kpis.status_breakdown` (already mapped through `WORKFLOW_PHASES` in current code — re-flatten to 7 stages).

#### Bottom: Suppliers leaderboard (full width)

- Header: `TOP SUPPLIERS · last 30 days` + link `View all →` to `/suppliers`.
- Compact table, 5 rows:

| Col              | Width | Content                                  |
|------------------|-------|------------------------------------------|
| Rank             | 40    | Numeric badge (1–5)                      |
| Supplier         | flex  | Name (bold) + email (muted, 12px)        |
| Category         | 140   | Tag                                      |
| Response rate    | 120   | Mini progress bar + percentage           |
| Avg score        | 80    | Big tabular number, color-coded          |
| Last interaction | 100   | Relative date ("3d ago")                 |
| Action           | 40    | `→` chevron link to supplier detail      |

**Data dependency:** needs `/dashboard/top-suppliers?limit=5&period=30d`. New endpoint, spec'd in the implementation plan.

## 5. Top header & sidebar adjustments

Out of scope for the layout redesign but small refinements ride along:

- **Top header**: keep the title + live indicator pattern, but add a subtle `⌘K` global search trigger pill on the right of the header (placeholder action — opens a stub modal if not yet implemented). This signals "modern SaaS" to supervisors immediately.
- **Sidebar**: tighten vertical spacing between nav items from current value to 12px, add a 4px-wide left accent border on the active item in `--accent-primary`, switch the inbox `nav-badge` color to `--accent-ai` (the "agentic" purple), keep section labels.

## 6. Loading, empty, error & live states

- **Loading**: each section renders **skeleton cards** matching its final layout (animated subtle gradient sweep, respects `prefers-reduced-motion`). Never the current `Loading dashboard...` text.
- **Empty**: every section has a designed empty state (icon + 1 line of copy + optional action). Listed per section above.
- **Error**: section renders a small inline error card with retry link. The whole dashboard never goes blank because of one failing endpoint.
- **Live refresh signal**: `↻ Updated Xs ago` pill in the hero sub-header. The "Xs" updates every second client-side; the pill briefly pulses at each successful poll.

## 7. New backend endpoints (deferred to implementation plan)

The redesign introduces dependencies on new data not currently exposed. The implementation plan must decide whether to ship these as part of the same milestone or in phases. Listed here for visibility:

| Endpoint                              | Purpose                                  | Tier  | Phase |
|---------------------------------------|------------------------------------------|-------|-------|
| Extend `/dashboard/kpis`              | Add `sparkline.{savings,cycle,success}`, `spend_by_category`, per-agent live counts, last-error timestamps | 1, 3, 4 | 1 |
| `/dashboard/attention`                | Action queue items                       | 2     | 1 (can return `[]` initially) |
| `/dashboard/trend`                    | Time-series for trend chart              | 3     | 2 |
| `/dashboard/top-suppliers`            | Leaderboard data                         | 4     | 2 |

Phase 1 endpoints are required for the redesign to feel complete. Phase 2 endpoints can ship after the visual layout if needed.

## 8. Accessibility

- All color combinations meet WCAG AA contrast.
- All interactive elements (cards, rows, buttons, nav items) are keyboard-focusable with a visible focus ring: `outline: 2px solid var(--accent-primary); outline-offset: 2px`.
- All decorative icons have `aria-hidden="true"`. Functional icons have `aria-label`.
- Sparklines and the dot scale include `aria-label` summarizing the trend ("Savings up 18% over last 30 days").
- The Live AI strip is informative-only and is marked `aria-hidden="true"` for screen readers (the underlying data is reachable via the agent activity log page).
- All animations honor `prefers-reduced-motion: reduce`.

## 9. Print stylesheet

A minimal `@media print` rule converts the dashboard to a clean light-mode export:
- `--bg-base: #fff`, `--text-primary: #000`, borders darken.
- Live AI strip is hidden in print.
- Charts retain their data with high-contrast colors.

This is small but matters: CFOs print dashboards for board packs.

## 10. What changes vs. today

| Today                                              | New                                                                |
|----------------------------------------------------|--------------------------------------------------------------------|
| 7 small flat KPI cards in a row                    | 4 premium scoreboard cards with sparklines + deltas                |
| No real-time signal                                | Slim live AI activity strip (the only motion on the page)          |
| Charts-first layout                                | Action-first layout (decisions waiting on top)                     |
| Workflow as 3 vertical cards                       | Workflow as a horizontal 7-stage pipeline with bottleneck callout  |
| No supervisor-action surface                       | Dedicated "Needs your attention" with 1-click actions              |
| Generic dark theme (`#16171d`)                     | Cohesive design system: deep navy + indigo + restrained AI purple  |
| Static feel                                        | Live "Updated Xs ago" indicator + subtle polling pulses            |
| No category breakdown on dashboard                 | Spend-by-category bar chart in the insight zone                    |
| No suppliers visibility on dashboard               | Top-5 suppliers leaderboard at the bottom                          |
| `Loading dashboard...` text                        | Per-section skeleton cards                                         |

## 11. Out of scope (explicit deferrals)

- Mobile / tablet layout (anything below 1024px shows a desktop-only message).
- Customizable dashboard (drag-drop widgets, user preferences). Future iteration.
- Real `⌘K` global search behavior — the trigger pill is added but the modal is a stub.
- Redesign of pages other than the main dashboard (`/`).
- Dashboard data export (CSV/PDF). Deferred.
- Multi-tenancy or org-switching UI.

## 12. Acceptance criteria

The redesign is considered complete when:

1. The main dashboard route (`/`) renders the four tiers exactly as described.
2. All design tokens from §3.1 and §3.2 are defined as CSS variables and used consistently across the dashboard page (no hex codes inline in JSX for colors covered by tokens).
3. The Live AI strip animates and shows accurate per-agent counts. Hover tooltips show p95 latency.
4. The "Needs your attention" panel renders rows when the endpoint returns data, and the designed empty state when it returns `[]`.
5. The trend chart switches between 3 metrics and 3 periods without page reload.
6. Skeleton loading states render in every section while data loads.
7. Keyboard navigation works through all interactive elements with visible focus rings.
8. `prefers-reduced-motion: reduce` disables all motion.
9. Print stylesheet produces a readable light-mode export.
10. All chart and KPI numbers continue to match the values returned by `/dashboard/kpis` (no regressions in current functionality).
