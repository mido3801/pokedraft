import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  Shuffle,
  Zap,
  Trophy,
  UserCircle,
  MessageCircle,
  Download,
  Settings,
  Share2,
  Play,
  ArrowRight,
  Sparkles,
} from 'lucide-react'

export default function Home() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="overflow-hidden">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-pokemon-red via-red-600 to-pokemon-red text-white py-24 overflow-hidden">
        {/* Decorative pokeball patterns */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-32 h-32 border-4 border-white rounded-full" />
          <div className="absolute top-10 left-10 w-32 h-16 bg-white rounded-t-full" />
          <div className="absolute top-24 left-10 w-32 h-1 bg-white" />
          <div className="absolute top-20 left-20 w-12 h-12 border-4 border-white rounded-full bg-pokemon-red" />

          <div className="absolute bottom-20 right-20 w-48 h-48 border-4 border-white rounded-full" />
          <div className="absolute bottom-20 right-20 w-48 h-24 bg-white rounded-t-full" />
          <div className="absolute bottom-32 right-20 w-48 h-1 bg-white" />
          <div className="absolute bottom-36 right-36 w-16 h-16 border-4 border-white rounded-full bg-pokemon-red" />

          <div className="absolute top-1/2 left-1/4 w-24 h-24 border-4 border-white rounded-full opacity-50" />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            The ultimate Pokémon draft experience
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold mb-6 tracking-tight">
            Pokémon Draft League
          </h1>
          <p className="text-xl md:text-2xl mb-10 max-w-2xl mx-auto text-white/90 leading-relaxed">
            Create and manage Pokémon draft leagues with friends. Draft your team,
            compete in matches, and climb the standings.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link
              to="/draft/create"
              className="group inline-flex items-center justify-center gap-2 bg-white text-pokemon-red px-8 py-4 rounded-xl font-bold text-lg shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200"
            >
              <Play className="w-5 h-5" />
              Start a Draft
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            {!isAuthenticated && (
              <Link
                to="/login"
                className="inline-flex items-center justify-center gap-2 border-2 border-white text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-white hover:text-pokemon-red transition-all duration-200"
              >
                <UserCircle className="w-5 h-5" />
                Sign In
              </Link>
            )}
          </div>
        </div>

        {/* Wave decoration */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full">
            <path d="M0 120L60 105C120 90 240 60 360 45C480 30 600 30 720 37.5C840 45 960 60 1080 67.5C1200 75 1320 75 1380 75L1440 75V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="white"/>
          </svg>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Everything You Need</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              A complete platform for running Pokémon draft leagues, from casual drafts to competitive seasons.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Shuffle className="w-7 h-7" />}
              color="bg-type-dragon"
              title="Multiple Draft Formats"
              description="Snake, linear, or auction drafts. With or without salary caps and point budgets."
            />
            <FeatureCard
              icon={<Zap className="w-7 h-7" />}
              color="bg-type-electric"
              title="Real-time Drafting"
              description="Live drafts with timers, mobile support, and seamless reconnection."
            />
            <FeatureCard
              icon={<Trophy className="w-7 h-7" />}
              color="bg-pokemon-yellow"
              title="Full League Management"
              description="Schedules, standings, trades, and multi-season support."
            />
            <FeatureCard
              icon={<UserCircle className="w-7 h-7" />}
              color="bg-type-water"
              title="No Account Required"
              description="Create quick drafts with friends without signing up. Accounts unlock persistent features."
            />
            <FeatureCard
              icon={<MessageCircle className="w-7 h-7" />}
              color="bg-type-psychic"
              title="Discord Integration"
              description="Get notified when it's your turn, trades are proposed, and matches are scheduled."
            />
            <FeatureCard
              icon={<Download className="w-7 h-7" />}
              color="bg-type-grass"
              title="Team Export"
              description="Export your team directly to Pokémon Showdown format."
            />
          </div>
        </div>
      </section>

      {/* Quick Start Section */}
      <section className="py-24 bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Get Started in Seconds</h2>
            <p className="text-xl text-gray-600">No setup required. Create a draft and start picking.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <Step
              number={1}
              icon={<Settings className="w-6 h-6" />}
              title="Create a Draft"
              description="Configure your draft format, roster size, and Pokémon pool."
              color="bg-pokemon-blue"
            />
            <Step
              number={2}
              icon={<Share2 className="w-6 h-6" />}
              title="Share the Link"
              description="Send the unique link to your friends."
              color="bg-pokemon-yellow"
            />
            <Step
              number={3}
              icon={<Play className="w-6 h-6" />}
              title="Draft!"
              description="Take turns picking Pokémon in real-time."
              color="bg-pokemon-green"
            />
          </div>

          {/* Connector lines for desktop */}
          <div className="hidden md:block max-w-4xl mx-auto relative -mt-32">
            <div className="absolute top-1/2 left-1/4 right-1/4 h-0.5 bg-gradient-to-r from-pokemon-blue via-pokemon-yellow to-pokemon-green opacity-30" />
          </div>
        </div>
      </section>

      {/* Join Draft Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="relative bg-gradient-to-br from-pokemon-blue to-blue-700 rounded-3xl p-12 text-center text-white overflow-hidden">
            {/* Decorative elements */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full translate-y-1/2 -translate-x-1/2" />

            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Have a Rejoin Code?</h2>
              <p className="text-xl text-white/80 mb-8 max-w-lg mx-auto">
                Enter your code to rejoin an active draft session and continue where you left off.
              </p>
              <Link
                to="/draft/join"
                className="inline-flex items-center gap-2 bg-white text-pokemon-blue px-8 py-4 rounded-xl font-bold text-lg shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200"
              >
                <ArrowRight className="w-5 h-5" />
                Rejoin Draft
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({
  icon,
  color,
  title,
  description
}: {
  icon: React.ReactNode
  color: string
  title: string
  description: string
}) {
  return (
    <div className="group bg-white rounded-2xl p-8 shadow-sm hover:shadow-xl transition-all duration-300 border border-gray-100 hover:border-gray-200 hover:-translate-y-1">
      <div className={`inline-flex items-center justify-center w-14 h-14 ${color} text-white rounded-xl mb-6 group-hover:scale-110 transition-transform duration-300`}>
        {icon}
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-3">{title}</h3>
      <p className="text-gray-600 leading-relaxed">{description}</p>
    </div>
  )
}

function Step({
  number,
  icon,
  title,
  description,
  color
}: {
  number: number
  icon: React.ReactNode
  title: string
  description: string
  color: string
}) {
  return (
    <div className="text-center relative">
      <div className={`w-20 h-20 ${color} text-white rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg relative`}>
        <span className="absolute -top-2 -right-2 w-8 h-8 bg-gray-900 text-white rounded-full flex items-center justify-center text-sm font-bold">
          {number}
        </span>
        {icon}
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-3">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}
