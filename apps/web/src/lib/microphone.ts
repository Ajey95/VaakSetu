export async function requestMicrophone(mediaDevices: MediaDevices | undefined = navigator.mediaDevices): Promise<void> {
  if (!mediaDevices?.getUserMedia) {
    throw new Error('Microphone capture is unavailable in this browser. Use a current Chrome or Edge window over HTTPS.')
  }

  try {
    const stream = await mediaDevices.getUserMedia({ audio: true })
    stream.getTracks().forEach((track) => track.stop())
  } catch (error) {
    if (error instanceof Error && error.name === 'NotAllowedError') {
      throw new Error('Microphone access was blocked. Allow microphone access for this site, then press Call again.')
    }
    if (error instanceof Error && error.name === 'NotFoundError') {
      throw new Error('No microphone was found. Connect a microphone or headset, then press Call again.')
    }
    throw new Error('The microphone could not be started. Check browser and operating-system microphone permissions, then try again.')
  }
}
