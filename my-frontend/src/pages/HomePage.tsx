// src/pages/HomePage.tsx
import HomeTable from "../components/HomeTable";

type HomePageProps = {
  onLoginClick: () => void;
};

export default function HomePage({ onLoginClick }: HomePageProps) {
  return (
    <section className="home-overview" aria-labelledby="home-overview-heading">
      <header className="home-overview-header">
        <div className="home-overview-copy">
          <p className="home-overview-kicker">Découvrir la plateforme</p>
          <h2 id="home-overview-heading">Indices principaux</h2>
          <p>
            Surveillez les mouvements clés du marché avant de vous connecter. Les valeurs sont
            formatées pour une lecture rapide et enrichies d’un sparkline.
          </p>
        </div>
        <button type="button" className="home-login-button" onClick={onLoginClick}>
          Se connecter
        </button>
      </header>

      <HomeTable />
    </section>
  );
}
