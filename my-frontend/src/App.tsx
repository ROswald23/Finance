import { useMemo, useState } from 'react'
import './App.css'
import HomePage from './pages/HomePage'
import LoginForm from './components/LoginForm'
import RegisterForm from './components/RegisterForm'
import WalletTable from './components/WalletTable'
import { useAuth } from './store/auth'

type NavView = 'home' | 'wallet' | 'indicators' | 'news'
type View = NavView | 'login' | 'register'

const navItems: Array<{
  view: NavView
  label: string
  endpoint: string
  description: string
}> = [
  {
    view: 'home',
    label: 'Accueil',
    endpoint: '/home',
    description: 'Vue globale des principaux indices et mouvements du marché.',
  },
  {
    view: 'wallet',
    label: 'Portefeuille',
    endpoint: '/api/me/wallet',
    description: 'Composition détaillée du portefeuille et dernière mise à jour.',
  },
  {
    view: 'indicators',
    label: 'Indicateurs',
    endpoint: '/ticker/{ticker}',
    description: 'Indicateurs avancés pour un titre spécifique, calculés en temps réel.',
  },
  {
    view: 'news',
    label: 'Actualités',
    endpoint: '/news',
    description: 'Flux d’actualités financières pour éclairer vos décisions.',
  },
]

function App() {
  const token = useAuth((state) => state.accessToken)
  const clear = useAuth((state) => state.clear)
  const [view, setView] = useState<View>(token ? 'wallet' : 'home')
  const isAuthView = view === 'login' || view === 'register'

  const activeNav = useMemo<NavView>(() => {
    if (view === 'login' || view === 'register') {
      return 'home'
    }
    return view
  }, [view])

  const goTo = (next: View) => setView(next)
  const handleLogout = () => {
    clear()
    setView('home')
  }

  const renderHomePanels = () => (
    <section className="content-panels home-side-panels">
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
          Remplacez ce texte par les composants correspondant aux données d’un endpoint, comme les
          indicateurs d’un ticker ou la liste de vos transactions récentes.
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
  )

  const renderContent = () => {
    switch (view) {
      case 'home':
        return (
          <>
            <header className="content-header">
              <h2>Bienvenue sur votre tableau de bord</h2>

            </header>
            <div className="home-split">
              <article className="panel seamless home-table-panel">
                <HomePage onLoginClick={() => goTo('login')} />
              </article>
              <div className="home-panels-stack">{renderHomePanels()}</div>
            </div>
          </>
        )
      case 'wallet':
        if (!token) {
          return (
            <section className="panel">
              <h3>Connectez-vous pour accéder à votre portefeuille</h3>
              <p>
                Authentifiez-vous pour synchroniser vos positions, suivre vos performances et mettre à
                jour vos transactions.
              </p>
              <div className="panel-actions">
                <button className="primary-action" onClick={() => goTo('login')}>
                  Se connecter
                </button>
                <button className="secondary-action" onClick={() => goTo('register')}>
                  Créer un compte
                </button>
              </div>
            </section>
          )
        }

        return (
          <>
            <header className="content-header">
              <h2>Mon portefeuille</h2>
              <p>Retrouvez vos lignes, valeurs liquidatives et performances actualisées.</p>
            </header>
            <section className="panel seamless">
              <WalletTable />
            </section>
          </>
        )
      case 'indicators':
        return (
          <section className="panel">
            <h3>Indicateurs personnalisés</h3>
            <p>
              Connectez cet écran à l’endpoint <code>/ticker/&lt;ticker&gt;</code> pour afficher vos ratios
              fondamentaux, mesures de risque et comparaisons avec le benchmark.
            </p>
            <p>
              Vous pouvez y intégrer des graphiques (courbes de performance, chandeliers) ou des
              tableaux d’indicateurs clés.
            </p>
          </section>
        )
      case 'news':
        return (
          <section className="panel">
            <h3>Fil d’actualités</h3>
            <p>
              Branchez cet espace sur l’endpoint <code>/news</code> pour centraliser les informations
              de marché et les alertes sectorielles utiles à vos décisions d’investissement.
            </p>
            <p>
              Ajoutez ensuite des filtres (pays, secteur, importance) ou un flux temps réel selon vos
              besoins.
            </p>
          </section>
        )
      case 'login':
      case 'register':
        return (
          <div className="auth-frame">
            <div className="auth-tabs">
              <button
                className={view === 'login' ? 'auth-tab active' : 'auth-tab'}
                onClick={() => goTo('login')}
                type="button"
              >
                Se connecter
              </button>
              <button
                className={view === 'register' ? 'auth-tab active' : 'auth-tab'}
                onClick={() => goTo('register')}
                type="button"
              >
                Créer un compte
              </button>
            </div>
            {view === 'login' ? (
              <LoginForm onLoggedIn={() => goTo('wallet')} />
            ) : (
              <RegisterForm onRegistered={() => goTo('login')} />
            )}
          </div>
        )
      default:
        return null
    }
  }

  const mainClassName = isAuthView ? 'content-area auth-view' : 'content-area'

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-pill">Portefeuille</span>
          <h1>Finance Monitor</h1>
          <p>
            Naviguez entre vos différentes vues.
          </p>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <button
              key={item.view}
              type="button"
              className={item.view === activeNav ? 'nav-item active' : 'nav-item'}
              onClick={() => goTo(item.view)}
            >
              <span className="nav-label">{item.label}</span>
              <span className="nav-endpoint">{item.endpoint}</span>
              <span className="nav-description">{item.description}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          {!token ? (
            <div className="sidebar-actions">
              <button className="primary-action" onClick={() => goTo('login')}>
                Se connecter
              </button>
              <button className="secondary-action" onClick={() => goTo('register')}>
                Créer un compte
              </button>
            </div>
          ) : (
            <div className="sidebar-actions">
              <p>Connecté à votre espace personnel.</p>
              <button className="secondary-action" onClick={handleLogout}>
                Se déconnecter
              </button>
            </div>
          )}
        </div>
      </aside>

      <main className={mainClassName}>
        <div className="content-scroll">{renderContent()}</div>
      </main>
    </div>
  )
}

export default App
