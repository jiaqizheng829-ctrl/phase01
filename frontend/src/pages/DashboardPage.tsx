const sections = [
  { id: "sensors", title: "Sensors" },
  { id: "configuration", title: "Configuration" },
  { id: "automation", title: "Automation" },
  { id: "overview", title: "Overview" },
  { id: "controls", title: "Controls" },
  { id: "events", title: "Events" },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-emerald-400">
          Dashboard
        </h1>
        <p className="mt-2 text-slate-400">
          These sections are placeholders for later phases.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sections.map((section) => (
          <section
            key={section.id}
            id={section.id}
            className="rounded-xl border border-slate-700 bg-slate-900 p-5"
          >
            <h2 className="text-xl font-semibold text-slate-100">
              {section.title}
            </h2>
            <p className="mt-3 text-slate-400">
              This feature is not implemented in Phase 1.
            </p>
          </section>
        ))}
      </div>
    </div>
  );
}
