import { useState } from "react";
import { apiFetch } from "../lib/api";
import { useAuth } from "../store/auth";

type TokenOut = { access_token: string; refresh_token: string; token_type: string };

type LoginFormProps = {
  onLoggedIn: () => void;
};

export default function LoginForm({ onLoggedIn }: LoginFormProps) {
  const { setTokens } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const res = await apiFetch<TokenOut>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });
      setTokens(res.access_token, res.refresh_token);
      onLoggedIn();
    } catch (error: any) {
      setErr(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="auth-card" onSubmit={handleSubmit} noValidate>
      <header className="auth-card-header">
        <h2 className="auth-title">Connexion</h2>
        <p className="auth-subtitle">Accédez à votre tableau de bord personnalisé.</p>
      </header>

      <div className="auth-fields">
        <div className="auth-field">
          <label htmlFor="login-email" className="auth-label">
            Email
          </label>
          <input
            id="login-email"
            type="email"
            className="auth-input"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
          />
        </div>

        <div className="auth-field">
          <label htmlFor="login-password" className="auth-label">
            Mot de passe
          </label>
          <input
            id="login-password"
            type="password"
            className="auth-input"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </div>
      </div>

      {err && (
        <p className="auth-feedback auth-feedback-error" role="alert">
          {err}
        </p>
      )}

      <button type="submit" className="auth-submit" disabled={loading}>
        {loading ? "Connexion en cours…" : "Se connecter"}
      </button>
    </form>
  );
}
