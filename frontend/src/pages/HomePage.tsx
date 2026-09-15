import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <section className="space-y-4">
      <h1 className="text-3xl font-bold text-emerald-400">
        Greenhouse Dashboard
      </h1>

      <p className="text-slate-300">
        This Phase 1 project connects a React frontend, a FastAPI backend,
        and a PostgreSQL database.
      </p>

      <p className="text-slate-400">
        The dashboard contains placeholder sections for future greenhouse
        features.
      </p>

      <Link
        to="/dashboard"
        className="inline-block rounded-lg bg-emerald-700 px-4 py-2 text-white hover:bg-emerald-600"
      >
        Open dashboard
      </Link>
    </section>
  );
}
