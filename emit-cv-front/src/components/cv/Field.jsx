const base =
  "w-full rounded-xl border border-slate-300 bg-transparent px-4 py-2.5 text-sm outline-none transition placeholder:text-slate-400 focus:border-brand dark:border-night-line dark:placeholder:text-slate-500 dark:[&_option]:bg-night-card";

export default function Field({ label, as: Tag = "input", className = "", children, ...props }) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-1.5 block text-xs font-medium text-slate-500 dark:text-slate-400">{label}</span>
      <Tag className={base} {...props}>
        {children}
      </Tag>
    </label>
  );
}