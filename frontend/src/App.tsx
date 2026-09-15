import {
  BrowserRouter,
  NavLink,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import HealthStatus from "./components/HealthStatus";
import HomePage from "./pages/HomePage";
import DashboardPage from "./pages/DashboardPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <header className="border-b border-slate-700 bg-slate-900">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
            <span className="text-xl font-bold">Greenhouse</span>

            <nav aria-label="Main navigation" className="flex gap-4">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  isActive ? "text-emerald-400 underline" : "text-slate-300"
                }
              >
                Home
              </NavLink>

              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  isActive ? "text-emerald-400 underline" : "text-slate-300"
                }
              >
                Dashboard
              </NavLink>
            </nav>

            <HealthStatus />
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-6 py-10">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
