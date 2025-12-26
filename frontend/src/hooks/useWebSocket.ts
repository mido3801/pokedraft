import { useEffect, useRef, useState, useCallback } from 'react'
import { DraftState, WebSocketEvent } from '../types'

interface UseWebSocketOptions {
  draftId: string
  teamId?: string | null
  sessionToken?: string | null
  onStateUpdate?: (state: DraftState) => void
  onPickMade?: (data: { team_id: string; pokemon_id: number; pick_number: number }) => void
  onTurnStart?: (data: { team_id: string; timer_end: string }) => void
  onTimerTick?: (data: { seconds_remaining: number }) => void
  onDraftComplete?: (data: { final_teams: unknown[] }) => void
  onDraftStarted?: (data: { status: string; pick_order: string[]; current_team_id: string; current_team_name: string; timer_end?: string }) => void
  onUserJoined?: (data: { team_id: string; display_name: string }) => void
  onUserLeft?: (data: { team_id: string; display_name: string }) => void
  onError?: (data: { message: string; code: string }) => void
}

export function useWebSocket({
  draftId,
  teamId,
  sessionToken,
  onStateUpdate,
  onPickMade,
  onTurnStart,
  onTimerTick,
  onDraftComplete,
  onDraftStarted,
  onUserJoined,
  onUserLeft,
  onError,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isIntentionalCloseRef = useRef(false)

  // Store callbacks in refs to avoid reconnection on callback changes
  const callbacksRef = useRef({
    onStateUpdate,
    onPickMade,
    onTurnStart,
    onTimerTick,
    onDraftComplete,
    onDraftStarted,
    onUserJoined,
    onUserLeft,
    onError,
  })

  // Update callbacks ref when they change
  useEffect(() => {
    callbacksRef.current = {
      onStateUpdate,
      onPickMade,
      onTurnStart,
      onTimerTick,
      onDraftComplete,
      onDraftStarted,
      onUserJoined,
      onUserLeft,
      onError,
    }
  }, [onStateUpdate, onPickMade, onTurnStart, onTimerTick, onDraftComplete, onDraftStarted, onUserJoined, onUserLeft, onError])

  const connect = useCallback(() => {
    // Clear any pending reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Close existing connection if any (don't reconnect from this close)
    if (wsRef.current) {
      wsRef.current.onclose = null // Remove handler to prevent reconnect
      wsRef.current.close()
    }

    const wsBaseUrl = (import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`).replace(/\/$/, '')
    const wsUrl = `${wsBaseUrl}/ws/draft/${draftId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws
    isIntentionalCloseRef.current = false

    ws.onopen = () => {
      setIsConnected(true)
      reconnectAttemptsRef.current = 0

      // Send join_draft event to identify our team
      if (teamId || sessionToken) {
        ws.send(JSON.stringify({
          event: 'join_draft',
          data: {
            team_id: teamId,
            user_token: sessionToken,
          },
        }))
      }
    }

    ws.onclose = () => {
      setIsConnected(false)

      // Only reconnect if this wasn't an intentional close
      if (!isIntentionalCloseRef.current && reconnectAttemptsRef.current < 5) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000)
        reconnectAttemptsRef.current += 1
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, delay)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketEvent = JSON.parse(event.data)
        const callbacks = callbacksRef.current

        switch (message.event) {
          case 'draft_state':
            callbacks.onStateUpdate?.(message.data)
            break
          case 'pick_made':
            callbacks.onPickMade?.(message.data)
            break
          case 'turn_start':
            callbacks.onTurnStart?.(message.data)
            break
          case 'timer_tick':
            callbacks.onTimerTick?.(message.data)
            break
          case 'draft_complete':
            callbacks.onDraftComplete?.(message.data)
            break
          case 'draft_started':
            callbacks.onDraftStarted?.(message.data)
            break
          case 'user_joined':
            callbacks.onUserJoined?.(message.data)
            break
          case 'user_left':
            callbacks.onUserLeft?.(message.data)
            break
          case 'error':
            callbacks.onError?.(message.data)
            break
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    return ws
  }, [draftId, teamId, sessionToken])

  useEffect(() => {
    const ws = connect()

    return () => {
      // Clear reconnect timeout on cleanup
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      isIntentionalCloseRef.current = true
      ws.close()
    }
  }, [connect])

  const send = useCallback((event: string, data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ event, data }))
    }
  }, [])

  const makePick = useCallback((pokemonId: number) => {
    send('make_pick', { pokemon_id: pokemonId })
  }, [send])

  const placeBid = useCallback((pokemonId: number, amount: number) => {
    send('place_bid', { pokemon_id: pokemonId, amount })
  }, [send])

  const nominate = useCallback((pokemonId: number) => {
    send('nominate', { pokemon_id: pokemonId })
  }, [send])

  const startDraft = useCallback(() => {
    send('start_draft', {})
  }, [send])

  return {
    isConnected,
    send,
    makePick,
    placeBid,
    nominate,
    startDraft,
  }
}
