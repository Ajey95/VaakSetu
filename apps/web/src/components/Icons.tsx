import type { SVGProps } from 'react'
const Icon = ({ children, ...props }: SVGProps<SVGSVGElement>) => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{children}</svg>
export const PhoneIcon = (p: SVGProps<SVGSVGElement>) => <Icon {...p}><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.12.9.33 1.78.62 2.63a2 2 0 0 1-.45 2.11L8 9.74a16 16 0 0 0 6 6l1.28-1.28a2 2 0 0 1 2.11-.45c.85.29 1.73.5 2.63.62A2 2 0 0 1 22 16.92Z"/></Icon>
export const HangupIcon = (p: SVGProps<SVGSVGElement>) => <Icon {...p}><path d="M4 15.5c4.8-4.7 11.2-4.7 16 0"/><path d="m3 14 2.5 4 3-2.5M21 14l-2.5 4-3-2.5"/></Icon>
export const AlertIcon = (p: SVGProps<SVGSVGElement>) => <Icon {...p}><path d="M10.3 2.9 1.8 17a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 2.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4m0 4h.01"/></Icon>
export const ThumbIcon = ({ down = false, ...p }: SVGProps<SVGSVGElement> & { down?: boolean }) => <Icon style={{ transform: down ? 'rotate(180deg)' : undefined }} {...p}><path d="M7 10v12H3V10h4Zm0 10h10.3a2 2 0 0 0 1.9-1.4l2.4-8A2 2 0 0 0 19.7 8H15l.7-3.4A2.2 2.2 0 0 0 11.5 3L7 10Z"/></Icon>

