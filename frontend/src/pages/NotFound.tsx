import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-pokemon-red mb-4">404</h1>
        <p className="text-xl text-gray-600 mb-8">
          This page has fled the battle!
        </p>
        <Link to="/" className="btn btn-primary">
          Return Home
        </Link>
      </div>
    </div>
  )
}
