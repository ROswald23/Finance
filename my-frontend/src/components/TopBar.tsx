// src/components/TopBar.tsx
import { useAuth } from "../store/auth";

type TopBarProps = {
  currentView: "home" | "login" | "dashboard";
  onGoHome: () => void;
  onGoDashboard: () => void;
  onGoLogin: () => void;
};

export default function TopBar({
  currentView,
  onGoHome,
  onGoDashboard,
  onGoLogin,
}: TopBarProps) {
  const isAuth = !!useAuth((s) => s.accessToken);
  const clear = useAuth((s) => s.clear);

  return (
    <header className="bg-white border-b">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold">Portfolio App</span>
          <nav className="flex items-center gap-2 text-sm">
            <button
              onClick={onGoHome}
              className={
                "px-2 py-1 rounded-md " +
                (currentView === "home"
                  ? "bg-gray-100 font-medium"
                  : "text-gray-600 hover:bg-gray-50")
              }
            >
              Accueil
            </button>
            <button
              onClick={onGoDashboard}
              className={
                "px-2 py-1 rounded-md " +
                (currentView === "dashboard"
                  ? "bg-gray-100 font-medium"
                  : "text-gray-600 hover:bg-gray-50")
              }
            >
              Mon portefeuille
            </button>
          </nav>
        </div>

        <div className="flex items-center gap-2">
          {!isAuth && currentView !== "login" && (
            <button
              onClick={onGoLogin}
              className="px-3 py-1.5 rounded-lg text-sm bg-indigo-600 text-white hover:bg-indigo-700"
            >
              Se connecter
            </button>
          )}
          {isAuth && (
            <button
              onClick={clear}
              className="px-3 py-1.5 rounded-lg text-sm bg-gray-100 text-gray-800 hover:bg-gray-200"
            >
              Se déconnecter
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

