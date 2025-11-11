// src/components/HomeTable.tsx
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api";
import { useAuth } from "../store/auth";
import type { Indice } from "../types";

const priceFormatter = new Intl.NumberFormat("fr-FR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const performanceFormatter = new Intl.NumberFormat("fr-FR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

type SparklineProps = {
  ticker: string;
  performance: number;
};

const SPARKLINE_POINTS = 16;
const SPARKLINE_WIDTH = 120;
const SPARKLINE_HEIGHT = 40;
const SPARKLINE_PADDING = 4;

function seededValue(seed: number) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function buildSeries(ticker: string, performance: number) {
  const points: number[] = [];
  const base = 1 + performance / 100;
  const volatility = Math.min(Math.abs(performance) / 100, 0.35);

  for (let i = 0; i < SPARKLINE_POINTS; i++) {
    const seed = ticker.charCodeAt(i % ticker.length) * (i + 1);
    const drift = (i / (SPARKLINE_POINTS - 1)) * (base - 1);
    const noise = (seededValue(seed) - 0.5) * volatility;
    const value = 1 + drift + noise;
    points.push(value);
  }

  return points;
}

function Sparkline({ ticker, performance }: SparklineProps) {
  const series = useMemo(() => buildSeries(ticker, performance), [ticker, performance]);
  const min = Math.min(...series);
  const max = Math.max(...series);
  const range = max - min || 1;
  const strokeColor = performance >= 0 ? "var(--color-olive)" : "var(--color-steel)";
  const fillColor = performance >= 0
    ? "rgba(168, 167, 136, 0.2)"
    : "rgba(113, 133, 151, 0.2)";

  const path = series
    .map((value, index) => {
      const x =
        (index / (SPARKLINE_POINTS - 1)) * (SPARKLINE_WIDTH - SPARKLINE_PADDING * 2) +
        SPARKLINE_PADDING;
      const y =
        SPARKLINE_HEIGHT -
        ((value - min) / range) * (SPARKLINE_HEIGHT - SPARKLINE_PADDING * 2) -
        SPARKLINE_PADDING;
      return `${index === 0 ? "M" : "L"}${x},${y}`;
    })
    .join(" ");

  const fillPath = `${path} L${SPARKLINE_WIDTH - SPARKLINE_PADDING},${
    SPARKLINE_HEIGHT - SPARKLINE_PADDING
  } L${SPARKLINE_PADDING},${SPARKLINE_HEIGHT - SPARKLINE_PADDING} Z`;

  return (
    <svg
      className="sparkline"
      viewBox={`0 0 ${SPARKLINE_WIDTH} ${SPARKLINE_HEIGHT}`}
      width={SPARKLINE_WIDTH}
      height={SPARKLINE_HEIGHT}
      role="img"
      aria-label={`Mini graphique pour ${ticker}`}
    >
      <path d={fillPath} fill={fillColor} stroke="none" />
      <path d={path} fill="none" stroke={strokeColor} strokeWidth={2} strokeLinecap="round" />
    </svg>
  );
}

export default function HomeTable() {
  const token = useAuth((s) => s.accessToken);
  const [rows, setRows] = useState<Indice[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    async function load() {
      try {
        const data = await apiFetch<Indice[]>("/home", {}, token || undefined);
        if (!ignore) setRows(data);
      } catch (e: any) {
        if (!ignore) setErr(e.message);
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    load();
    return () => {
      ignore = true;
    };
  }, [token]);

  if (loading) {
    return <p>Chargement…</p>;
  }

  if (err) {
    return <p style={{ color: "crimson" }}>{err}</p>;
  }

  return (
    <section className="home-table-container" aria-label="Indices de marché">
      <header className="home-table-header">
        <div>
          <h3>Indices &amp; valeurs suivies</h3>
          <p>Vue instantanée des titres clés et de leur dynamique récente.</p>
        </div>
      </header>
      <div className="home-table-shell">
        <table className="home-table">
          <thead>
            <tr>
              <th scope="col">Indice</th>
              <th scope="col" className="sparkline-col">
                Tendance
              </th>
              <th scope="col" className="pricing-col">
                Valorisation
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const perf = row.performance ?? 0;
              const perfClass = perf >= 0 ? "perf-positive" : "perf-negative";
              const formattedPrice = priceFormatter.format(row.price);
              const formattedPerf = `${perf >= 0 ? "+" : ""}${performanceFormatter.format(perf)} %`;

              return (
                <tr key={row.ticker}>
                  <th scope="row">
                    <span className="ticker-symbol">{row.ticker}</span>
                    <span className="ticker-name">{row.full_name}</span>
                  </th>
                  <td>
                    <Sparkline ticker={row.ticker} performance={perf} />
                  </td>
                  <td>
                    <div className={`pricing-stack ${perfClass}`}>
                      <span className="price-value">{formattedPrice} €</span>
                      <span className={`price-performance ${perfClass}`}>{formattedPerf}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
