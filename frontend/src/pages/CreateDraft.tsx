import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DraftFormat } from '../types'

export default function CreateDraft() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    displayName: '',
    format: 'snake' as DraftFormat,
    rosterSize: 6,
    timerSeconds: 90,
    budgetEnabled: false,
    budgetPerTeam: 100,
    template: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Call API to create draft
    console.log('Creating draft:', formData)
    // navigate(`/d/${draftId}`)
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Create a Draft</h1>
      <p className="text-gray-600 mb-8">
        Set up a quick draft session. No account required!
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Your Info</h2>
          <div>
            <label className="label">Display Name</label>
            <input
              type="text"
              value={formData.displayName}
              onChange={(e) => setFormData({ ...formData, displayName: e.target.value })}
              className="input"
              placeholder="Enter your name"
              required
            />
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Draft Settings</h2>

          <div className="space-y-4">
            <div>
              <label className="label">Draft Format</label>
              <select
                value={formData.format}
                onChange={(e) => setFormData({ ...formData, format: e.target.value as DraftFormat })}
                className="input"
              >
                <option value="snake">Snake Draft</option>
                <option value="linear">Linear Draft</option>
                <option value="auction">Auction Draft</option>
              </select>
              <p className="text-sm text-gray-500 mt-1">
                {formData.format === 'snake' && 'Pick order reverses each round (1→8, 8→1, 1→8...)'}
                {formData.format === 'linear' && 'Same pick order every round (1→8, 1→8...)'}
                {formData.format === 'auction' && 'Pokemon are nominated and teams bid. Highest bidder wins.'}
              </p>
            </div>

            <div>
              <label className="label">Roster Size</label>
              <input
                type="number"
                value={formData.rosterSize}
                onChange={(e) => setFormData({ ...formData, rosterSize: parseInt(e.target.value) })}
                className="input"
                min={1}
                max={20}
              />
            </div>

            <div>
              <label className="label">Timer (seconds per pick)</label>
              <input
                type="number"
                value={formData.timerSeconds}
                onChange={(e) => setFormData({ ...formData, timerSeconds: parseInt(e.target.value) })}
                className="input"
                min={30}
                max={600}
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="budgetEnabled"
                checked={formData.budgetEnabled}
                onChange={(e) => setFormData({ ...formData, budgetEnabled: e.target.checked })}
                className="h-4 w-4 text-pokemon-red rounded border-gray-300"
              />
              <label htmlFor="budgetEnabled" className="ml-2 text-sm text-gray-700">
                Enable salary cap / point budget
              </label>
            </div>

            {formData.budgetEnabled && (
              <div>
                <label className="label">Budget Per Team</label>
                <input
                  type="number"
                  value={formData.budgetPerTeam}
                  onChange={(e) => setFormData({ ...formData, budgetPerTeam: parseInt(e.target.value) })}
                  className="input"
                  min={1}
                />
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Pokemon Pool</h2>
          <div>
            <label className="label">Template</label>
            <select
              value={formData.template}
              onChange={(e) => setFormData({ ...formData, template: e.target.value })}
              className="input"
            >
              <option value="">All Pokemon</option>
              <option value="ou">OU (OverUsed)</option>
              <option value="uu">UU (UnderUsed)</option>
              <option value="monotype">Monotype</option>
              <option value="little_cup">Little Cup</option>
              <option value="draft_league">Draft League (with points)</option>
            </select>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            You can customize the pool further after creating the draft.
          </p>
        </div>

        <button type="submit" className="btn btn-primary w-full py-3 text-lg">
          Create Draft
        </button>
      </form>
    </div>
  )
}
