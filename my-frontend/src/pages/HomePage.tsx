// src/pages/HomePage.tsx
import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import type { Indice } from "../types";

type HomePageProps = {
  onLoginClick: () => void;
  className?: string;
};

export default function HomePage({ onLoginClick, className }: HomePageProps) {
  const [data, setData] = useState<Indice[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    async function load() {
      setLoading(true);
      try {
        const res = await apiFetch<Indice[]>("/home");
        if (!ignore) setData(res);
      } catch (e: any) {
        if (!ignore) setErr(e.message ?? "Erreur de chargement");
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    load();
    return () => {
      ignore = true;
    };
  }, []);

  const rootClass = [
    'home-page',
    'max-w-4xl mx-auto px-4 py-8',
    className ?? '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <section className={rootClass}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-semibold">Indices principaux</h2>
          <p className="text-sm text-gray-500">
            Vue d’ensemble du marché avant de vous connecter.
          </p>
        </div>
        <button
          onClick={onLoginClick}
          className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700"
        >
          Se connecter
        </button>
      </div>

      {loading && <p className="text-gray-600">Chargement…</p>}
      {err && <p className="text-red-600">{err}</p>}
      {!loading && !err && (
        <div className="bg-white rounded-xl shadow-sm border divide-y">
          {data.map((idx) => {
            const positive = idx.performance >= 0;
            const perfColor = positive ? "text-emerald-600" : "text-red-600";
            const sign = positive ? "+" : "";
            return (
              <div
                key={idx.ticker}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50"
              >
                {/* Nom + ticker */}
                <div>
                  <div className="text-sm font-semibold">{idx.full_name}</div>
                  <div className="text-xs text-gray-500">{idx.ticker}</div>
                </div>

                {/* Prix */}
                <div className="text-right">
                  <div className="text-sm font-medium tabular-nums">
                    {idx.price.toFixed(2)}
                  </div>
                </div>

                {/* Perf */}
                <div className="text-right w-24">
                  <span
                    className={
                      "inline-flex items-center justify-end text-sm font-semibold tabular-nums " +
                      perfColor
                    }
                  >
                    {sign}
                    {idx.performance.toFixed(2)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
