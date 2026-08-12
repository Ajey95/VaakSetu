import { describe, expect, it, vi } from 'vitest'
import { requestMicrophone } from './microphone'

describe('requestMicrophone', () => {
  it('requests audio permission and releases the probe stream', async () => {
    const stop = vi.fn()
    const getUserMedia = vi.fn().mockResolvedValue({ getTracks: () => [{ stop }] })

    await requestMicrophone({ getUserMedia } as unknown as MediaDevices)

    expect(getUserMedia).toHaveBeenCalledWith({ audio: true })
    expect(stop).toHaveBeenCalledOnce()
  })

  it('explains when microphone permission is denied', async () => {
    const denied = new Error('denied')
    denied.name = 'NotAllowedError'
    const getUserMedia = vi.fn().mockRejectedValue(denied)

    await expect(requestMicrophone({ getUserMedia } as unknown as MediaDevices))
      .rejects.toThrow('Microphone access was blocked')
  })

  it('rejects browsers without microphone capture support', async () => {
    await expect(requestMicrophone(undefined)).rejects.toThrow('Microphone capture is unavailable')
  })
})
