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
