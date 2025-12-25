import { useEffect, useRef, useState, useCallback } from 'react'
import { DraftState, WebSocketEvent } from '../types'

interface UseWebSocketOptions {
  draftId: string
  onStateUpdate?: (state: DraftState) => void
  onPickMade?: (data: { team_id: string; pokemon_id: number; pick_number: number }) => void
  onTurnStart?: (data: { team_id: string; timer_end: string }) => void
  onTimerTick?: (data: { seconds_remaining: number }) => void
  onDraftComplete?: (data: { final_teams: unknown[] }) => void
  onError?: (data: { message: string; code: string }) => void
}

export function useWebSocket({
  draftId,
  onStateUpdate,
  onPickMade,
  onTurnStart,
  onTimerTick,
  onDraftComplete,
  onError,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/draft/${draftId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      setReconnectAttempts(0)
      console.log('WebSocket connected')
    }

    ws.onclose = () => {
      setIsConnected(false)
      console.log('WebSocket disconnected')

      // Attempt to reconnect with exponential backoff
      if (reconnectAttempts < 5) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
        setTimeout(() => {
          setReconnectAttempts((prev) => prev + 1)
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

        switch (message.event) {
          case 'draft_state':
            onStateUpdate?.(message.data)
            break
          case 'pick_made':
            onPickMade?.(message.data)
            break
          case 'turn_start':
            onTurnStart?.(message.data)
            break
          case 'timer_tick':
            onTimerTick?.(message.data)
            break
          case 'draft_complete':
            onDraftComplete?.(message.data)
            break
          case 'error':
            onError?.(message.data)
            break
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    return ws
  }, [draftId, reconnectAttempts, onStateUpdate, onPickMade, onTurnStart, onTimerTick, onDraftComplete, onError])

  useEffect(() => {
    const ws = connect()

    return () => {
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

  return {
    isConnected,
    send,
    makePick,
    placeBid,
    nominate,
  }
}
