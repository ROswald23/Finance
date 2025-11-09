import './App.css'

const endpoints = [
  {
    label: 'Accueil',
    endpoint: '/home',
    description: 'Vue globale des principaux indices et mouvements du marché.',
  },
  {
    label: 'Portefeuille',
    endpoint: '/api/me/wallet',
    description: 'Composition détaillée du portefeuille et dernière mise à jour.',
  },
  {
    label: 'Indicateurs',
    endpoint: '/ticker/{ticker}',
    description: 'Indicateurs avancés pour un titre spécifique, calculés en temps réel.',
  },
  {
    label: 'Actualités',
    endpoint: '/news',
    description: 'Flux d’actualités financières pour éclairer vos décisions.',
  },
]

function App() {
  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-pill">Portefeuille</span>
          <h1>Finance Monitor</h1>
          <p>Intégrez ici vos composants de navigation ou de filtres.</p>
        </div>

        <nav className="sidebar-nav">
          {endpoints.map((item) => (
            <a key={item.endpoint} href={item.endpoint} className="nav-item">
              <span className="nav-label">{item.label}</span>
              <span className="nav-endpoint">{item.endpoint}</span>
              <span className="nav-description">{item.description}</span>
            </a>
          ))}
        </nav>

        <div className="sidebar-footer">
          <p>
            Cette barre latérale reste visible pour accueillir le contenu spécifique à chaque
            endpoint (menus, résumés, graphiques ou formulaires).
          </p>
        </div>
      </aside>

      <main className="content-area">
        <header className="content-header">
          <h2>Bienvenue sur votre tableau de bord</h2>
          <p>
            Sélectionnez une route dans la barre latérale pour charger dynamiquement les vues et
            widgets associés. Ce canevas fournit la structure principale de votre application.
          </p>
        </header>

        <section className="content-panels">
          <article className="panel highlight">
            <h3>Vision rapide</h3>
            <p>
              Utilisez cette zone pour afficher un résumé global de vos performances : valeur du
              portefeuille, variation journalière et alertes importantes.
            </p>
          </article>

          <article className="panel">
            <h3>Contenu dynamique</h3>
            <p>
              Remplacez ce texte par les composants correspondant aux données d’un endpoint, comme
              les indicateurs d’un ticker ou la liste de vos transactions récentes.
            </p>
          </article>

          <article className="panel">
            <h3>À faire ensuite</h3>
            <ul>
              <li>Connecter les endpoints de l’API à vos composants React.</li>
              <li>Ajouter l’état global (Redux, Zustand, etc.) pour partager les données.</li>
              <li>Mettre en place la navigation (React Router) pour basculer de vue en vue.</li>
            </ul>
          </article>
        </section>
      </main>
    </div>
  )
}

export default App
