import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function JoinDraft() {
  const navigate = useNavigate()
  const [rejoinCode, setRejoinCode] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!rejoinCode.trim()) {
      setError('Please enter a rejoin code')
      return
    }

    // TODO: Call API to join draft
    console.log('Joining draft:', { rejoinCode, displayName })
    // navigate(`/d/${draftId}`)
  }

  return (
    <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">Join a Draft</h1>
      <p className="text-gray-600 mb-8 text-center">
        Enter your rejoin code to join an active draft session.
      </p>

      <form onSubmit={handleSubmit} className="card space-y-6">
        <div>
          <label className="label">Rejoin Code</label>
          <input
            type="text"
            value={rejoinCode}
            onChange={(e) => setRejoinCode(e.target.value.toUpperCase())}
            className="input text-center text-2xl tracking-widest"
            placeholder="PIKA-1234"
            maxLength={9}
          />
          <p className="text-sm text-gray-500 mt-1">
            The code was displayed when the draft was created.
          </p>
        </div>

        <div>
          <label className="label">Your Display Name</label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="input"
            placeholder="Enter your name"
          />
        </div>

        {error && (
          <div className="text-red-600 text-sm">{error}</div>
        )}

        <button type="submit" className="btn btn-primary w-full py-3">
          Join Draft
        </button>
      </form>

      <p className="text-center text-gray-500 mt-6 text-sm">
        Don't have a code?{' '}
        <a href="/draft/create" className="text-pokemon-red hover:underline">
          Create a new draft
        </a>
      </p>
    </div>
  )
}
