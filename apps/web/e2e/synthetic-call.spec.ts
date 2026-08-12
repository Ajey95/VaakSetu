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
