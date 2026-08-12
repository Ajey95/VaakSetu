import { Device, Call } from '@twilio/voice-sdk'

export class TwilioCallClient {
  private device?: Device
  private call?: Call
  async connect(token: string, phoneNumber: string, onStatus: (status: string, callSid?: string) => void): Promise<void> {
    this.device = new Device(token, { closeProtection: true })
    this.device.on('error', (error) => onStatus(`error:${error.code}`))
    await this.device.register()
    onStatus('dialing')
    this.call = await this.device.connect({ params: { To: phoneNumber } })
    this.call.on('ringing', () => onStatus('ringing'))
    this.call.on('accept', (call) => onStatus('connected', call.parameters.CallSid))
    this.call.on('disconnect', () => onStatus('ended'))
    this.call.on('cancel', () => onStatus('ended'))
    this.call.on('error', () => onStatus('error'))
  }
  hangUp(): void { this.call?.disconnect(); this.call = undefined }
  destroy(): void { this.device?.destroy(); this.device = undefined }
}
