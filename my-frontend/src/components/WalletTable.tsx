// src/components/WalletTable.tsx
import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import { useAuth } from "../store/auth";

type WalletRow = { id: number; ticker: string; quantity: number; created_at: string };

export default function WalletTable() {
  const token = useAuth((s) => s.accessToken);
  const [rows, setRows] = useState<WalletRow[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    async function load() {
      try {
        const data = await apiFetch<WalletRow[]>("/api/me/wallet", {}, token || undefined);
        if (!ignore) setRows(data);
      } catch (e: any) {
        if (!ignore) setErr(e.message);
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    load();
    return () => { ignore = true; };
  }, [token]);

  if (loading) return <p>Chargement…</p>;
  if (err) return <p style={{ color: "crimson" }}>{err}</p>;

  return (
    <div>
      <h2>Mon portefeuille</h2>
      <table border={1} cellPadding={6}>
        <thead>
          <tr>
            <th>ID</th><th>Ticker</th><th>Quantité</th><th>Créé le</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.ticker}</td>
              <td>{r.quantity}</td>
              <td>{new Date(r.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
