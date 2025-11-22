import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { CATEGORY_ICONS, formatCurrency } from '@/lib/constants'
import { Category, Expense, BudgetMap } from '@/lib/types'
import { useMemo } from 'react'

interface BudgetCardProps {
  category: Category
  budget: number
  expenses: Expense[]
  onBudgetChange: (category: Category, amount: number) => void
}

export function BudgetCard({ category, budget, expenses, onBudgetChange }: BudgetCardProps) {
  const Icon = CATEGORY_ICONS[category]

  const spent = useMemo(() => {
    return expenses
      .filter(e => e.category === category)
      .reduce((sum, e) => sum + e.amount, 0)
  }, [expenses, category])

  const percentage = budget > 0 ? Math.min((spent / budget) * 100, 100) : 0
  const remaining = budget - spent
  const isOverBudget = spent > budget && budget > 0

  const getProgressColorClass = () => {
    if (budget === 0) return 'muted'
    if (isOverBudget) return 'destructive'
    if (percentage >= 80) return 'warning'
    return 'success'
  }

  const colorClass = getProgressColorClass()

  return (
    <Card className="p-6">
      <div className="flex items-start gap-3 mb-4">
        <div className="p-2 bg-muted rounded-lg">
          <Icon className="w-5 h-5 text-muted-foreground" />
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-foreground">{category}</h3>
          <p className="text-sm text-muted-foreground">
            {formatCurrency(spent)} of {formatCurrency(budget)}
          </p>
        </div>
      </div>

      <div className="mb-4">
        <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
          <div 
            className={`h-full transition-all duration-300 ${
              colorClass === 'destructive' ? 'bg-destructive' :
              colorClass === 'warning' ? 'bg-warning' :
              colorClass === 'success' ? 'bg-success' :
              'bg-muted-foreground'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <div className="flex justify-between items-center mt-2">
          <span className={`text-sm font-medium ${isOverBudget ? 'text-destructive' : remaining < budget * 0.2 && budget > 0 ? 'text-warning' : 'text-success'}`}>
            {isOverBudget ? `Over by ${formatCurrency(Math.abs(remaining))}` : `${formatCurrency(remaining)} remaining`}
          </span>
          <span className="text-sm text-muted-foreground">
            {percentage.toFixed(0)}%
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor={`budget-${category}`} className="text-sm">
          Monthly Budget
        </Label>
        <Input
          id={`budget-${category}`}
          type="number"
          step="0.01"
          min="0"
          placeholder="0.00"
          value={budget || ''}
          onChange={(e) => onBudgetChange(category, parseFloat(e.target.value) || 0)}
          className="tabular-nums"
        />
      </div>
    </Card>
  )
}
