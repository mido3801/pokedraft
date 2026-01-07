import { useState, useEffect } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  Play,
  Users,
  LogIn,
  Sparkles,
} from 'lucide-react'

const pokemonQuotes = [
  "Take charge of your destiny.",
  "I'm going to become the world's greatest Pokémon Master!",
  "Gotta catch 'em all!",
  "A new adventure awaits!",
  "Time to assemble your dream team!",
  "The road to becoming Champion starts here!",
  "What will you do next?",
  "Trust in your Pokémon and they'll trust in you!",
]

export default function Home() {
  const { isAuthenticated, loading } = useAuth()
  const [quoteIndex, setQuoteIndex] = useState(0)
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    const interval = setInterval(() => {
      // Fade out
      setIsVisible(false)
      // Change quote and fade in after fade-out completes
      setTimeout(() => {
        setQuoteIndex((prev) => (prev + 1) % pokemonQuotes.length)
        setIsVisible(true)
      }, 300)
    }, 4000)
    return () => clearInterval(interval)
  }, [])

  // Redirect to dashboard if authenticated
  if (!loading && isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center overflow-hidden">
      {/* Full page hero */}
      <section className="relative w-full min-h-[calc(100vh-4rem)] bg-gradient-to-br from-pokemon-red via-red-600 to-red-800 text-white flex items-center justify-center overflow-hidden">
        {/* Animated pokeball patterns */}
        <div className="absolute inset-0 opacity-10">
          {/* Top left pokeball */}
          <div className="absolute top-10 left-10 w-32 h-32 border-4 border-white rounded-full animate-pulse" />
          <div className="absolute top-10 left-10 w-32 h-16 bg-white rounded-t-full" />
          <div className="absolute top-24 left-10 w-32 h-1 bg-white" />
          <div className="absolute top-20 left-20 w-12 h-12 border-4 border-white rounded-full bg-pokemon-red" />

          {/* Bottom right pokeball */}
          <div className="absolute bottom-20 right-20 w-48 h-48 border-4 border-white rounded-full animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute bottom-44 right-20 w-48 h-24 bg-white rounded-t-full" />
          <div className="absolute bottom-44 right-20 w-48 h-1 bg-white" />
          <div className="absolute bottom-36 right-36 w-16 h-16 border-4 border-white rounded-full bg-pokemon-red" />

          {/* Floating pokeball 1 */}
          <div className="absolute top-1/4 right-1/4 opacity-50 animate-bounce" style={{ animationDuration: '3s' }}>
            <div className="w-20 h-20 border-4 border-white rounded-full" />
            <div className="absolute top-0 left-0 w-20 h-10 bg-white rounded-t-full" />
            <div className="absolute top-[38px] left-0 w-20 h-1 bg-white" />
            <div className="absolute top-[30px] left-[30px] w-5 h-5 border-2 border-white rounded-full bg-pokemon-red" />
          </div>

          {/* Floating pokeball 2 */}
          <div className="absolute bottom-1/3 left-1/4 opacity-30 animate-bounce" style={{ animationDuration: '4s', animationDelay: '0.5s' }}>
            <div className="w-16 h-16 border-4 border-white rounded-full" />
            <div className="absolute top-0 left-0 w-16 h-8 bg-white rounded-t-full" />
            <div className="absolute top-[30px] left-0 w-16 h-1 bg-white" />
            <div className="absolute top-[23px] left-[23px] w-4 h-4 border-2 border-white rounded-full bg-pokemon-red" />
          </div>
        </div>

        {/* Content */}
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          {/* Rotating quote */}
          <div className={`inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-medium mb-8 min-h-[2.5rem] transition-opacity duration-300 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
            <Sparkles className="w-4 h-4 flex-shrink-0" />
            <span className="text-center">{pokemonQuotes[quoteIndex]}</span>
          </div>

          {/* Title */}
          <h1 className="text-5xl md:text-7xl font-extrabold mb-6 tracking-tight drop-shadow-lg">
            PokéDraft
          </h1>
          <p className="text-xl md:text-2xl mb-12 max-w-xl mx-auto text-white/90 leading-relaxed">
            Draft Pokémon with friends. No signup required.
          </p>

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row justify-center gap-4 mb-8">
            <Link
              to="/draft/create"
              className="group inline-flex items-center justify-center gap-3 bg-white text-pokemon-red px-8 py-4 rounded-2xl font-bold text-lg shadow-lg hover:shadow-2xl hover:scale-105 transition-all duration-200"
            >
              <Play className="w-6 h-6" />
              Start Draft
            </Link>
            <Link
              to="/draft/join"
              className="group inline-flex items-center justify-center gap-3 bg-white/10 backdrop-blur-sm border-2 border-white text-white px-8 py-4 rounded-2xl font-bold text-lg hover:bg-white hover:text-pokemon-red transition-all duration-200"
            >
              <Users className="w-6 h-6" />
              Join Draft
            </Link>
          </div>

          {/* Sign in link */}
          <Link
            to="/login"
            className="inline-flex items-center gap-2 text-white/80 hover:text-white transition-colors text-sm font-medium group"
          >
            <LogIn className="w-4 h-4" />
            Sign in to save your drafts and manage your leagues!
            <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
          </Link>
        </div>

        {/* Bottom gradient fade */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black/20 to-transparent" />
      </section>
    </div>
  )
}
