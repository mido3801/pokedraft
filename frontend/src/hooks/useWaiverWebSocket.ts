import { useEffect, useRef, useState, useCallback } from 'react'
import { WaiverClaim, WaiverWebSocketEvent } from '../types'

interface UseWaiverWebSocketOptions {
  seasonId: string
  enabled?: boolean
  onClaimCreated?: (claim: WaiverClaim) => void
  onClaimCancelled?: (data: { claim_id: string }) => void
  onClaimApproved?: (claim: WaiverClaim) => void
  onClaimRejected?: (claim: WaiverClaim) => void
  onVoteCast?: (data: { claim_id: string; votes_for: number; votes_against: number }) => void
  onError?: (data: { message: string; code: string }) => void
}

export function useWaiverWebSocket({
  seasonId,
  enabled = true,
  onClaimCreated,
  onClaimCancelled,
  onClaimApproved,
  onClaimRejected,
  onVoteCast,
  onError,
}: UseWaiverWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isIntentionalCloseRef = useRef(false)

  // Store callbacks in refs to avoid reconnection on callback changes
  const callbacksRef = useRef({
    onClaimCreated,
    onClaimCancelled,
    onClaimApproved,
    onClaimRejected,
    onVoteCast,
    onError,
  })

  // Update callbacks ref when they change
  useEffect(() => {
    callbacksRef.current = {
      onClaimCreated,
      onClaimCancelled,
      onClaimApproved,
      onClaimRejected,
      onVoteCast,
      onError,
    }
  }, [onClaimCreated, onClaimCancelled, onClaimApproved, onClaimRejected, onVoteCast, onError])

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
    const wsUrl = `${wsBaseUrl}/ws/waivers/${seasonId}`

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
        console.log('Waiver WebSocket: Connection rejected by server, not reconnecting')
        isIntentionalCloseRef.current = true
        return
      }

      // Only reconnect if this wasn't an intentional close (limit to 3 attempts)
      if (!isIntentionalCloseRef.current && reconnectAttemptsRef.current < 3) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000)
        reconnectAttemptsRef.current += 1
        console.log(`Waiver WebSocket: Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`)
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, delay)
      } else if (reconnectAttemptsRef.current >= 3) {
        console.log('Waiver WebSocket: Max reconnection attempts reached')
      }
    }

    ws.onerror = () => {
      // Error is logged, but onclose will handle reconnection logic
    }

    ws.onmessage = (event) => {
      try {
        const message: WaiverWebSocketEvent = JSON.parse(event.data)
        const callbacks = callbacksRef.current

        switch (message.event) {
          case 'waiver_claim_created':
            callbacks.onClaimCreated?.(message.data.claim)
            break
          case 'waiver_claim_cancelled':
            callbacks.onClaimCancelled?.(message.data)
            break
          case 'waiver_claim_approved':
            callbacks.onClaimApproved?.(message.data.claim)
            break
          case 'waiver_claim_rejected':
            callbacks.onClaimRejected?.(message.data.claim)
            break
          case 'waiver_vote_cast':
            callbacks.onVoteCast?.(message.data)
            break
          case 'error':
            callbacks.onError?.(message.data)
            break
        }
      } catch (error) {
        console.error('Failed to parse waiver WebSocket message:', error)
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
