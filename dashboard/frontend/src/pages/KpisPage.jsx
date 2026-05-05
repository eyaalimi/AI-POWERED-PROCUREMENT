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

  const attentionItems = MOCK_ATTENTION;
  const alertCount = attentionItems.length;

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
