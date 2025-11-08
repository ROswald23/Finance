// src/components/HomeTable.tsx
import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import { useAuth } from "../store/auth";


export default function HomeTable() {
  const token = useAuth((s) => s.accessToken);
  const [rows, setRows] = useState<WalletRow[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    async function load() {
      try {
        const data = await apiFetch<WalletRow[]>("/home", {}, token || undefined);
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