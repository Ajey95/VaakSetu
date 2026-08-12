import { useEffect, useRef } from 'react'
import { isAppEvent } from '../types/contracts'
import { wsUrl } from '../lib/api'

export function useSessionSocket(callId: string | undefined, dispatch: (event: any) => void): void {
  const attempts = useRef(0)
  useEffect(() => {
    if (!callId) return
    let socket: WebSocket | undefined, timer: number | undefined, active = true
    const connect = () => {
      socket = new WebSocket(wsUrl(callId))
      socket.onopen = () => { attempts.current = 0 }
      socket.onmessage = (message) => { const value = JSON.parse(message.data); if (isAppEvent(value)) dispatch(value) }
      socket.onclose = () => { if (active) { attempts.current += 1; timer = window.setTimeout(connect, Math.min(500 * 2 ** attempts.current, 8000)) } }
    }
    connect()
    return () => { active = false; if (timer) clearTimeout(timer); socket?.close() }
  }, [callId, dispatch])
}

