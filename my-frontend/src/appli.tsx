// src/App.tsx
import { useState } from "react";
import { useAuth } from "./store/auth";
import LoginForm from "./components/LoginForm";
import RegisterForm from "./components/RegisterForm";
import WalletTable from "./components/WalletTable";
import HomePage from "./pages/HomePage";

type View = "home" | "login" | "register" | "wallet";

export default function App() {
  const token = useAuth((s) => s.accessToken);
  const clear = useAuth((s) => s.clear);

  // Si déjà connecté => on ouvre directement le wallet, sinon page d'accueil
  const [view, setView] = useState<View>(token ? "wallet" : "home");

  const handleLogout = () => {
    clear();
    setView("home");
  };

  const goHome = () => setView("home");
  const goLogin = () => setView("login");
  const goRegister = () => setView("register");
  const goWallet = () => setView("wallet");

  function renderContent() {
    // 1) Page d'accueil publique : indices (Apple Bourse) + bouton Se connecter
    if (view === "home") {
      return <HomePage onLoginClick={goLogin} />;
    }

    // 2) Écrans d'authentification (login / register)
    if (view === "login" || view === "register") {
      return (
        <div className="flex-1 flex items-center justify-center py-10 px-4">
          <div className="w-full max-w-md">
            <div className="flex justify-center gap-2 mb-4">
              <button
                onClick={goLogin}
                className={
                  "px-3 py-1.5 rounded-lg text-sm " +
                  (view === "login"
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-100 text-gray-800 hover:bg-gray-200")
                }
              >
                Se connecter
              </button>
              <button
                onClick={goRegister}
                className={
                  "px-3 py-1.5 rounded-lg text-sm " +
                  (view === "register"
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-100 text-gray-800 hover:bg-gray-200")
                }
              >
                Créer un compte
              </button>
            </div>

            {view === "login" && (
              <LoginForm onLoggedIn={() => setView("wallet")} />
            )}
            {view === "register" && (
              <RegisterForm onRegistered={goLogin} />
            )}
          </div>
        </div>
      );
    }

    // 3) Dashboard / Wallet (protégé)
    if (view === "wallet") {
      // Si pas de token, on renvoie vers un écran de login
      if (!token) {
        return (
          <div className="flex-1 flex items-center justify-center py-10 px-4">
            <div className="w-full max-w-md">
              <LoginForm onLoggedIn={() => setView("wallet")} />
            </div>
          </div>
        );
      }

      return (
        <main className="flex-1 max-w-6xl mx-auto px-4 py-6 w-full">
          <h2 className="text-xl font-semibold mb-4">Mon portefeuille</h2>
          <WalletTable />
        </main>
      );
    }

    return null;
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header / Nav */}
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-lg font-semibold">Portfolio App</span>
            <nav className="flex items-center gap-2 text-sm">
              <button
                onClick={goHome}
                className={
                  "px-2 py-1 rounded-md " +
                  (view === "home"
                    ? "bg-gray-100 font-medium"
                    : "text-gray-600 hover:bg-gray-50")
                }
              >
                Accueil
              </button>
              <button
                onClick={goWallet}
                className={
                  "px-2 py-1 rounded-md " +
                  (view === "wallet"
                    ? "bg-gray-100 font-medium"
                    : "text-gray-600 hover:bg-gray-50")
                }
              >
                Mon portefeuille
              </button>
            </nav>
          </div>

          <div className="flex items-center gap-2">
            {!token && (
              <>
                <button
                  onClick={goLogin}
                  className="px-3 py-1.5 rounded-lg text-sm bg-indigo-600 text-white hover:bg-indigo-700"
                >
                  Se connecter
                </button>
                <button
                  onClick={goRegister}
                  className="px-3 py-1.5 rounded-lg text-sm bg-gray-100 text-gray-800 hover:bg-gray-200"
                >
                  Créer un compte
                </button>
              </>
            )}
            {token && (
              <button
                onClick={handleLogout}
                className="px-3 py-1.5 rounded-lg text-sm bg-gray-100 text-gray-800 hover:bg-gray-200"
              >
                Se déconnecter
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Contenu */}
      {renderContent()}
    </div>
  );
}
