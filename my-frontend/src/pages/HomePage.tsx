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
        </div>
      </header>
      <HomeTable />
    </section>
  );
}
