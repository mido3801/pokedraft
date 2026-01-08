import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { presetService } from '../services/preset'
import { queryKeys } from '../services/queryKeys'
import { PoolPreset } from '../types'
import { downloadFile } from '../utils/csvUtils'
import PoolPresetModal from './PoolPresetModal'
import {
  Database,
  Plus,
  Globe,
  Lock,
  Trash2,
  Pencil,
  Download,
} from 'lucide-react'

export default function PoolPresetsCard() {
  const queryClient = useQueryClient()
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingPreset, setEditingPreset] = useState<PoolPreset | null>(null)
  const [loadingPresetId, setLoadingPresetId] = useState<string | null>(null)

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

  const handleEdit = async (presetId: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setLoadingPresetId(presetId)
    try {
      const fullPreset = await presetService.getPreset(presetId)
      setEditingPreset(fullPreset)
      setIsModalOpen(true)
    } catch (err) {
      console.error('Failed to load preset:', err)
    } finally {
      setLoadingPresetId(null)
    }
  }

  const handleDownload = async (presetId: string, presetName: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDownloadingId(presetId)
    try {
      const fullPreset = await presetService.getPreset(presetId)
      // Generate CSV from the pool
      const headers = ['id', 'name', 'types', 'generation', 'bst', 'is_legendary', 'is_mythical']
      const rows = Object.entries(fullPreset.pokemon_pool)
        .map(([id, pokemon]) => {
          const p = pokemon as { name: string; types: string[]; generation?: number; bst?: number; is_legendary?: boolean; is_mythical?: boolean }
          return [
            id,
            p.name,
            `"${p.types.join(',')}"`,
            p.generation?.toString() || '',
            p.bst?.toString() || '',
            p.is_legendary?.toString() || 'false',
            p.is_mythical?.toString() || 'false',
          ].join(',')
        })
        .sort((a, b) => parseInt(a.split(',')[0]) - parseInt(b.split(',')[0]))
      const csv = [headers.join(','), ...rows].join('\n')
      const safeName = presetName.replace(/[^a-z0-9]/gi, '_').toLowerCase()
      downloadFile(csv, `${safeName}_pool.csv`)
    } catch (err) {
      console.error('Failed to download preset:', err)
    } finally {
      setDownloadingId(null)
    }
  }

  const handleCreateNew = () => {
    setEditingPreset(null)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingPreset(null)
  }

  // Separate own presets from public presets
  const myPresets = presets?.filter(p => !p.creator_name) || []
  const publicPresets = presets?.filter(p => p.creator_name) || []

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
            <Database className="w-5 h-5 text-indigo-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900">Pool Presets</h2>
        </div>
        <button
          onClick={handleCreateNew}
          className="flex items-center gap-1 text-sm text-indigo-600 hover:underline"
        >
          <Plus className="w-4 h-4" />
          Add Pool
        </button>
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
              <div className="flex items-center gap-1">
                <button
                  onClick={(e) => handleEdit(preset.id, e)}
                  disabled={loadingPresetId === preset.id}
                  className="p-1.5 rounded text-gray-400 hover:text-indigo-500 hover:bg-indigo-50 transition-colors disabled:opacity-50"
                  title="Edit preset"
                >
                  {loadingPresetId === preset.id ? (
                    <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
                  ) : (
                    <Pencil className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={(e) => handleDownload(preset.id, preset.name, e)}
                  disabled={downloadingId === preset.id}
                  className="p-1.5 rounded text-gray-400 hover:text-blue-500 hover:bg-blue-50 transition-colors disabled:opacity-50"
                  title="Download CSV"
                >
                  {downloadingId === preset.id ? (
                    <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                </button>
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
          <button
            onClick={handleCreateNew}
            className="inline-flex items-center gap-2 text-indigo-600 font-medium hover:underline"
          >
            <Plus className="w-4 h-4" />
            Create your first pool
          </button>
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

      <PoolPresetModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        editPreset={editingPreset}
      />
    </div>
  )
}
