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
