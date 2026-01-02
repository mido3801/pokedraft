import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { SpriteProvider } from './context/SpriteContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'
import AuthCallback from './pages/AuthCallback'
import Dashboard from './pages/Dashboard'
import LeagueList from './pages/LeagueList'
import LeagueDetail from './pages/LeagueDetail'
import LeagueSettings from './pages/LeagueSettings'
import JoinLeague from './pages/JoinLeague'
import SeasonDetail from './pages/SeasonDetail'
import DraftRoom from './pages/DraftRoom'
import CreateDraft from './pages/CreateDraft'
import JoinDraft from './pages/JoinDraft'
import UserSettings from './pages/UserSettings'
import NotFound from './pages/NotFound'

function App() {
  return (
    <AuthProvider>
      <SpriteProvider>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="login" element={<Login />} />
            <Route path="auth/callback" element={<AuthCallback />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="leagues" element={<LeagueList />} />
            <Route path="leagues/join" element={<JoinLeague />} />
            <Route path="leagues/:leagueId" element={<LeagueDetail />} />
            <Route path="leagues/:leagueId/join" element={<JoinLeague />} />
            <Route path="leagues/:leagueId/settings" element={<LeagueSettings />} />
            <Route path="seasons/:seasonId" element={<SeasonDetail />} />
            <Route path="draft/create" element={<CreateDraft />} />
            <Route path="draft/join" element={<JoinDraft />} />
            <Route path="d/:draftId" element={<DraftRoom />} />
            <Route path="settings" element={<UserSettings />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </SpriteProvider>
    </AuthProvider>
  )
}

export default App
