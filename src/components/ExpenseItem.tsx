import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PencilSimple, Trash } from '@phosphor-icons/react'
import { Expense } from '@/lib/types'
import { formatCurrency, formatDate, CATEGORY_ICONS } from '@/lib/constants'

interface ExpenseItemProps {
  expense: Expense
  onEdit: (expense: Expense) => void
  onDelete: (id: string) => void
}

export function ExpenseItem({ expense, onEdit, onDelete }: ExpenseItemProps) {
  const Icon = CATEGORY_ICONS[expense.category]
  const isFuture = new Date(expense.date) > new Date()

  return (
    <Card className="p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="p-2 bg-muted rounded-lg shrink-0">
            <Icon className="w-5 h-5 text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-1">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground truncate">
                  {expense.description || 'No description'}
                </p>
                <p className="text-sm text-muted-foreground">
                  {formatDate(expense.date)}
                  {isFuture && <span className="ml-2 text-accent">(Planned)</span>}
                </p>
              </div>
              <p className="text-lg font-semibold text-foreground tabular-nums shrink-0">
                {formatCurrency(expense.amount)}
              </p>
            </div>
            <Badge variant="secondary" className="mt-1">
              {expense.category}
            </Badge>
          </div>
        </div>
        <div className="flex gap-1 shrink-0">
          <Button
            size="icon"
            variant="ghost"
            onClick={() => onEdit(expense)}
            className="h-8 w-8"
          >
            <PencilSimple className="w-4 h-4" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            onClick={() => onDelete(expense.id)}
            className="h-8 w-8 text-destructive hover:text-destructive"
          >
            <Trash className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  )
}
