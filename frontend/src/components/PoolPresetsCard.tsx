import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { presetService } from '../services/preset'
import { queryKeys } from '../services/queryKeys'
import {
  Database,
  Plus,
  Globe,
  Lock,
  Trash2,
} from 'lucide-react'

export default function PoolPresetsCard() {
  const queryClient = useQueryClient()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const { data: presets, isLoading } = useQuery({
    queryKey: queryKeys.presets,
    queryFn: presetService.getPresets,
  })

  const deleteMutation = useMutation({
    mutationFn: presetService.deletePreset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.presets })
    },
  })

  const handleDelete = async (presetId: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm('Delete this preset?')) return
    setDeletingId(presetId)
    try {
      await deleteMutation.mutateAsync(presetId)
    } finally {
      setDeletingId(null)
    }
  }

  // Separate own presets from public presets
  const myPresets = presets?.filter(p => !p.creator_name) || []
  const publicPresets = presets?.filter(p => p.creator_name) || []

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
            <Database className="w-5 h-5 text-purple-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900">Pool Presets</h2>
        </div>
        <Link
          to="/draft/create"
          className="flex items-center gap-1 text-sm text-purple-600 hover:underline"
        >
          <Plus className="w-4 h-4" />
          Create New
        </Link>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="loader w-6 h-6"></div>
        </div>
      ) : myPresets.length > 0 ? (
        <div className="space-y-2">
          {myPresets.slice(0, 5).map((preset) => (
            <div
              key={preset.id}
              className="flex items-center justify-between p-3 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors"
            >
              <div className="flex items-center gap-3">
                {preset.is_public ? (
                  <Globe className="w-4 h-4 text-green-500" />
                ) : (
                  <Lock className="w-4 h-4 text-gray-400" />
                )}
                <div>
                  <span className="font-medium text-gray-900">{preset.name}</span>
                  <span className="text-xs text-gray-500 ml-2">
                    {preset.pokemon_count} Pokemon
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => handleDelete(preset.id, e)}
                  disabled={deletingId === preset.id}
                  className="p-1.5 rounded text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors disabled:opacity-50"
                  title="Delete preset"
                >
                  {deletingId === preset.id ? (
                    <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          ))}
          {myPresets.length > 5 && (
            <p className="text-sm text-gray-500 text-center pt-2">
              +{myPresets.length - 5} more presets
            </p>
          )}
        </div>
      ) : (
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Database className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-500 mb-4">
            No saved presets yet
          </p>
          <Link
            to="/draft/create"
            className="inline-flex items-center gap-2 text-purple-600 font-medium hover:underline"
          >
            <Plus className="w-4 h-4" />
            Create your first preset
          </Link>
        </div>
      )}

      {publicPresets.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-xs text-gray-500 mb-2">Public Presets</p>
          <div className="space-y-1">
            {publicPresets.slice(0, 3).map((preset) => (
              <div
                key={preset.id}
                className="text-sm text-gray-600 flex items-center justify-between"
              >
                <span>{preset.name}</span>
                <span className="text-xs text-gray-400">by {preset.creator_name}</span>
              </div>
            ))}
            {publicPresets.length > 3 && (
              <p className="text-xs text-gray-400">+{publicPresets.length - 3} more</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
