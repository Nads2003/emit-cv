export default function SectionTitle({ title1, title2, children }) {
  return (
    <div className="mx-auto max-w-2xl text-center">
      <h2 className="text-3xl font-light tracking-tight sm:text-4xl">
        {title1} <span className="font-bold">{title2}</span>
      </h2>
      <div className="mt-4 flex justify-center gap-2" aria-hidden="true">
        <span className="h-2.5 w-2.5 rounded-full bg-brand" />
        <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
        <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
      </div>
      {children}
    </div>
  );
}