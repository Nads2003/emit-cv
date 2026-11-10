const color = (score) => (score >= 80 ? "#10b981" : score >= 60 ? "#4f6df5" : "#f59e0b");

export default function ScoreBadge({ score }) {
  return (
    <div
      className="flex h-[72px] w-[72px] shrink-0 items-center justify-center rounded-full"
      style={{ background: `conic-gradient(${color(score)} ${score * 3.6}deg, rgba(148,163,184,0.25) 0deg)` }}
      aria-label={`${score}%`}
    >
      <div className="flex h-[58px] w-[58px] items-center justify-center rounded-full bg-white text-sm font-bold dark:bg-night-card">
        {score}%
      </div>
    </div>
  );
}