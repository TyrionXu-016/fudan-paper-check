export function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="card-surface p-5">
      <p className="font-[family-name:var(--font-sans)] text-xs font-medium uppercase tracking-wider text-ink-faint">
        {label}
      </p>
      <p className="stat-value mt-2">{value}</p>
    </div>
  );
}
