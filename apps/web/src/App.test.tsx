import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

describe('sales coach workspace', () => {
  it('shows explicit synthetic mode and all required health domains', () => {
    render(<App />)
    expect(screen.getByText(/synthetic demonstration/i)).toBeInTheDocument()
    for (const label of ['CALL', 'MEDIA', 'STT', 'COACH', 'DATA']) expect(screen.getByText(label)).toBeInTheDocument()
  })
  it('validates phone number before calling', async () => {
    render(<App />)
    fireEvent.change(screen.getByLabelText(/phone number/i), { target: { value: 'Ajay' } })
    fireEvent.click(screen.getByRole('button', { name: /^call$/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/valid phone/i)
  })
  it('renders coaching, transcript, profile and evidence semantics from a session', () => {
    render(<App initialDemo />)
    expect(screen.getByRole('heading', { name: /call & profile/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /live conversation/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /ai coach/i })).toBeInTheDocument()
    expect(screen.getByText('£450,000')).toBeInTheDocument()
    expect(screen.getAllByText(/buyer/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/UK House Price Index/i)).toBeInTheDocument()
    expect(screen.getByText(/Partially supported/i)).toBeInTheDocument()
  })
})
