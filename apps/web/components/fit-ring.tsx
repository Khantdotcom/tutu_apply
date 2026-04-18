export function FitRing({ score }: { score: number }) {
  const normalized = Math.max(0, Math.min(100, score));
  return (
    <div
      className="grid h-12 w-12 place-items-center rounded-full text-xs font-semibold"
      style={{
        background: `conic-gradient(#4F46E5 ${normalized * 3.6}deg, #E2E8F0 0deg)`
      }}
      aria-label={`Fit score ${normalized}`}
    >
      <span className="grid h-9 w-9 place-items-center rounded-full bg-white">{normalized}</span>
    </div>
  );
}
