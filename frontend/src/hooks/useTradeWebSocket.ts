import { useEffect, useRef, useState, useCallback } from 'react'
import { Trade, TradeWebSocketEvent } from '../types'

interface UseTradeWebSocketOptions {
  seasonId: string
  enabled?: boolean
  onTradeProposed?: (trade: Trade) => void
  onTradeAccepted?: (data: { trade_id: string; requires_approval: boolean; trade?: Trade }) => void
  onTradeRejected?: (data: { trade_id: string }) => void
  onTradeCancelled?: (data: { trade_id: string }) => void
  onTradeApproved?: (data: { trade_id: string; trade: Trade }) => void
  onError?: (data: { message: string; code: string }) => void
}

export function useTradeWebSocket({
  seasonId,
  enabled = true,
  onTradeProposed,
  onTradeAccepted,
  onTradeRejected,
  onTradeCancelled,
  onTradeApproved,
  onError,
}: UseTradeWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isIntentionalCloseRef = useRef(false)

  // Store callbacks in refs to avoid reconnection on callback changes
  const callbacksRef = useRef({
    onTradeProposed,
    onTradeAccepted,
    onTradeRejected,
    onTradeCancelled,
    onTradeApproved,
    onError,
  })

  // Update callbacks ref when they change
  useEffect(() => {
    callbacksRef.current = {
      onTradeProposed,
      onTradeAccepted,
      onTradeRejected,
      onTradeCancelled,
      onTradeApproved,
      onError,
    }
  }, [onTradeProposed, onTradeAccepted, onTradeRejected, onTradeCancelled, onTradeApproved, onError])

  const connect = useCallback(() => {
    if (!enabled || !seasonId) return null

    // Clear any pending reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.close()
    }

    const wsBaseUrl = (
      import.meta.env.VITE_WS_URL ||
      `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
    ).replace(/\/$/, '')
    const wsUrl = `${wsBaseUrl}/ws/trades/${seasonId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws
    isIntentionalCloseRef.current = false

    ws.onopen = () => {
      setIsConnected(true)
      reconnectAttemptsRef.current = 0
    }

    ws.onclose = (event) => {
      setIsConnected(false)

      // Don't reconnect on 403/policy violations - server is rejecting connections
      if (event.code === 1008 || event.code === 403) {
        console.log('Trade WebSocket: Connection rejected by server, not reconnecting')
        isIntentionalCloseRef.current = true
        return
      }

      // Only reconnect if this wasn't an intentional close (limit to 3 attempts)
      if (!isIntentionalCloseRef.current && reconnectAttemptsRef.current < 3) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000)
        reconnectAttemptsRef.current += 1
        console.log(`Trade WebSocket: Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`)
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, delay)
      } else if (reconnectAttemptsRef.current >= 3) {
        console.log('Trade WebSocket: Max reconnection attempts reached')
      }
    }

    ws.onerror = () => {
      // Error is logged, but onclose will handle reconnection logic
    }

    ws.onmessage = (event) => {
      try {
        const message: TradeWebSocketEvent = JSON.parse(event.data)
        const callbacks = callbacksRef.current

        switch (message.event) {
          case 'trade_proposed':
            callbacks.onTradeProposed?.(message.data.trade)
            break
          case 'trade_accepted':
            callbacks.onTradeAccepted?.(message.data)
            break
          case 'trade_rejected':
            callbacks.onTradeRejected?.(message.data)
            break
          case 'trade_cancelled':
            callbacks.onTradeCancelled?.(message.data)
            break
          case 'trade_approved':
            callbacks.onTradeApproved?.(message.data)
            break
          case 'error':
            callbacks.onError?.(message.data)
            break
        }
      } catch (error) {
        console.error('Failed to parse trade WebSocket message:', error)
      }
    }

    return ws
  }, [seasonId, enabled])

  useEffect(() => {
    const ws = connect()

    return () => {
      // Clear reconnect timeout on cleanup
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      isIntentionalCloseRef.current = true
      ws?.close()
    }
  }, [connect])

  return { isConnected }
}
