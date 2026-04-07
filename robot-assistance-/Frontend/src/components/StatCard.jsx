export default function StatCard({ label, value, hint, tone = "violet" }) {
  return (
    <article className={`stat stat-${tone}`}>
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
      {hint ? <p className="stat-hint">{hint}</p> : null}
    </article>
  );
}
