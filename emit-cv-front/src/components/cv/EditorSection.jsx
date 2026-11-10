export default function EditorSection({ icon: Icon, title, children }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-night-line dark:bg-night-card">
      <h2 className="mb-5 flex items-center gap-3 text-lg font-semibold">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/15 text-brand">
          <Icon size={18} />
        </span>
        {title}
      </h2>
      <div className="space-y-4">{children}</div>
    </section>
  );
}