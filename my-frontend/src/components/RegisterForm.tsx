import { useState } from "react";
import { apiFetch } from "../lib/api";

type RegisterOut = { id: number; email: string; first_name?: string | null; last_name?: string | null };

type RegisterFormProps = {
  onRegistered: () => void;
};

export default function RegisterForm({ onRegistered }: RegisterFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    let shouldRedirect = false;
    const payload = {
      email: email.trim(),
      password,
      first_name: firstName.trim(),
      last_name: lastName.trim(),
    };

    try {
      const res = await apiFetch<RegisterOut>("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      shouldRedirect = Boolean(res?.email);
    } catch (error: any) {
      setErr(error.message);
    } finally {
      setLoading(false);
    }

    if (shouldRedirect) {
      onRegistered();
    }
  }

  return (
    <form className="auth-card" onSubmit={handleSubmit} noValidate>
      <header className="auth-card-header">
        <h2 className="auth-title">Créer un compte</h2>
        <p className="auth-subtitle">Rejoignez la plateforme et personnalisez votre expérience.</p>
      </header>

      <div className="auth-fields">
        <div className="auth-field-row">
          <div className="auth-field">
            <label htmlFor="register-first-name" className="auth-label">
              Prénom
            </label>
            <input
              id="register-first-name"
              type="text"
              className="auth-input"
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
              autoComplete="given-name"
              required
            />
          </div>

          <div className="auth-field">
            <label htmlFor="register-last-name" className="auth-label">
              Nom
            </label>
            <input
              id="register-last-name"
              type="text"
              className="auth-input"
              value={lastName}
              onChange={(event) => setLastName(event.target.value)}
              autoComplete="family-name"
              required
            />
          </div>
        </div>

        <div className="auth-field">
          <label htmlFor="register-email" className="auth-label">
            Email
          </label>
          <input
            id="register-email"
            type="email"
            className="auth-input"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
          />
        </div>

        <div className="auth-field">
          <label htmlFor="register-password" className="auth-label">
            Mot de passe (min. 4 caractères)
          </label>
          <input
            id="register-password"
            type="password"
            className="auth-input"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="new-password"
            minLength={8}
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
        {loading ? "Création en cours…" : "S'inscrire"}
      </button>
    </form>
  );
}
