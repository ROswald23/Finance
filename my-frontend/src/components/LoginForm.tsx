// src/components/LoginForm.tsx
import { useState } from "react";
import { apiFetch } from "../lib/api";
import { useAuth } from "../store/auth";

type TokenOut = { access_token: string; refresh_token: string; token_type: string };

export default function LoginForm({ onLoggedIn }: { onLoggedIn: () => void }) {
  const { setTokens } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const res = await apiFetch<TokenOut>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setTokens(res.access_token, res.refresh_token);
      onLoggedIn();
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Connexion</h2>

        <div className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Mot de passe
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {err && (
            <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-md">
              {err}
            </p>
          )}

          <button
            onClick={handleSubmit}
            disabled={loading}
            type="button"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "..." : "Se connecter"}
          </button>
        </div>
      </div>
    </div>
  );
}

<div className="p-4 bg-indigo-600 text-white rounded-xl">
  Hello Tailwind 🚀
</div>

