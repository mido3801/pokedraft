import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Home() {
  const { isAuthenticated } = useAuth()

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-pokemon-red to-red-700 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl font-bold mb-6">
            Pokemon Draft League
          </h1>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            Create and manage Pokemon draft leagues with friends. Draft your team,
            compete in matches, and climb the standings.
          </p>
          <div className="flex justify-center space-x-4">
            <Link to="/draft/create" className="btn btn-primary bg-white text-pokemon-red hover:bg-gray-100">
              Start a Draft
            </Link>
            {!isAuthenticated && (
              <Link to="/login" className="btn btn-outline border-white text-white hover:bg-white hover:text-pokemon-red">
                Sign In
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">Features</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              title="Multiple Draft Formats"
              description="Snake, linear, or auction drafts. With or without salary caps and point budgets."
            />
            <FeatureCard
              title="Real-time Drafting"
              description="Live drafts with timers, mobile support, and seamless reconnection."
            />
            <FeatureCard
              title="Full League Management"
              description="Schedules, standings, trades, and multi-season support."
            />
            <FeatureCard
              title="No Account Required"
              description="Create quick drafts with friends without signing up. Accounts unlock persistent features."
            />
            <FeatureCard
              title="Discord Integration"
              description="Get notified when it's your turn, trades are proposed, and matches are scheduled."
            />
            <FeatureCard
              title="Team Export"
              description="Export your team directly to Pokemon Showdown format."
            />
          </div>
        </div>
      </section>

      {/* Quick Start Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">Get Started in Seconds</h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <Step number={1} title="Create a Draft" description="Configure your draft format, roster size, and Pokemon pool." />
            <Step number={2} title="Share the Link" description="Send the unique link to your friends." />
            <Step number={3} title="Draft!" description="Take turns picking Pokemon in real-time." />
          </div>
        </div>
      </section>

      {/* Join Draft Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-6">Have a Rejoin Code?</h2>
          <p className="text-gray-600 mb-8">
            Enter your code to rejoin an active draft session.
          </p>
          <Link to="/draft/join" className="btn btn-primary">
            Rejoin Draft
          </Link>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="card">
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

function Step({ number, title, description }: { number: number; title: string; description: string }) {
  return (
    <div className="text-center">
      <div className="w-12 h-12 rounded-full bg-pokemon-red text-white flex items-center justify-center text-xl font-bold mx-auto mb-4">
        {number}
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}
