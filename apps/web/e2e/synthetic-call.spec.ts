import { expect, test } from '@playwright/test'

test('accepted active-call workspace renders without overflow', async ({ page }) => {
  await page.goto('/?demo=1')
  await expect(page.getByRole('heading',{name:'AI SALES COACH'})).toBeVisible()
  await expect(page.getByText('Acknowledge the price concern, confirm the mortgage position, then offer a Saturday viewing.')).toBeVisible()
  await expect(page.getByText('UK House Price Index (synthetic fixture)')).toBeVisible()
  await expect(page.getByText('Synthetic demonstration')).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)
  expect(overflow).toBe(false)
})

test('call controls and semantic regions remain available at mobile size', async ({ page }) => {
  await page.goto('/?demo=1')
  await expect(page.getByRole('button',{name:'Hang up'})).toBeVisible()
  await expect(page.getByRole('heading',{name:'AI COACH'})).toBeVisible()
  await expect(page.getByRole('heading',{name:'LIVE CONVERSATION'})).toBeVisible()
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)
  expect(overflow).toBe(false)
})

test('one click runs the complete automated sales-coach demo without microphone access', async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, '__microphoneRequests', { value: 0, writable: true })
    Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia: async () => {
      ;(window as typeof window & { __microphoneRequests: number }).__microphoneRequests += 1
      throw new Error('Demo must not request microphone access')
    } } })
  })
  await page.goto('/?demoDelay=0')

  await page.getByRole('button', { name: 'Start automated demo' }).click()
  await expect(page.getByText('Demo complete — post-call summary ready')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByRole('heading', { name: 'CALL SUMMARY' })).toBeVisible()
  await expect(page.getByText(/Budget: £450,000/).first()).toBeVisible()
  await expect(page.getByText(/Viewing:.*Saturday viewing works for me/i)).toBeVisible()
  expect(await page.evaluate(() => (window as typeof window & { __microphoneRequests: number }).__microphoneRequests)).toBe(0)
})
