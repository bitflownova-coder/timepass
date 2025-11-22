export type Category = 
  | 'Food' 
  | 'Transport' 
  | 'Entertainment' 
  | 'Shopping' 
  | 'Bills' 
  | 'Health' 
  | 'Other'

export interface Expense {
  id: string
  amount: number
  category: Category
  description: string
  date: string
  createdAt: string
}

export interface Budget {
  category: Category
  limit: number
}

export type BudgetMap = Record<Category, number>
