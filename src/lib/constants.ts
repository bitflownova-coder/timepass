import { Category } from './types'
import { 
  Hamburger, 
  Car, 
  FilmSlate, 
  ShoppingBag, 
  Receipt, 
  FirstAid, 
  DotsThree 
} from '@phosphor-icons/react'

export const CATEGORIES: Category[] = [
  'Food',
  'Transport',
  'Entertainment',
  'Shopping',
  'Bills',
  'Health',
  'Other'
]

export const CATEGORY_ICONS = {
  Food: Hamburger,
  Transport: Car,
  Entertainment: FilmSlate,
  Shopping: ShoppingBag,
  Bills: Receipt,
  Health: FirstAid,
  Other: DotsThree
}

export const CATEGORY_COLORS = {
  Food: 'oklch(0.65 0.18 145)',
  Transport: 'oklch(0.65 0.15 200)',
  Entertainment: 'oklch(0.60 0.22 320)',
  Shopping: 'oklch(0.75 0.15 85)',
  Bills: 'oklch(0.60 0.22 25)',
  Health: 'oklch(0.65 0.15 25)',
  Other: 'oklch(0.50 0.02 250)'
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount)
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }).format(date)
}

export function getMonthYear(dateString: string): string {
  const date = new Date(dateString)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

export function getCurrentMonthYear(): string {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}
