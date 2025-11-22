import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { CATEGORIES } from '@/lib/constants'
import { Category, Expense } from '@/lib/types'
import { toast } from 'sonner'

interface ExpenseDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (expense: Omit<Expense, 'id' | 'createdAt'>) => void
  expense?: Expense
}

export function ExpenseDialog({ open, onOpenChange, onSave, expense }: ExpenseDialogProps) {
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState<Category>('Food')
  const [description, setDescription] = useState('')
  const [date, setDate] = useState('')

  useEffect(() => {
    if (expense) {
      setAmount(expense.amount.toString())
      setCategory(expense.category)
      setDescription(expense.description)
      setDate(expense.date)
    } else {
      setAmount('')
      setCategory('Food')
      setDescription('')
      setDate(new Date().toISOString().split('T')[0])
    }
  }, [expense, open])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const numAmount = parseFloat(amount)
    if (isNaN(numAmount) || numAmount <= 0) {
      toast.error('Please enter a valid amount')
      return
    }

    onSave({
      amount: numAmount,
      category,
      description,
      date
    })

    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{expense ? 'Edit Expense' : 'Add Expense'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="amount">Amount (₹)</Label>
            <Input
              id="amount"
              type="number"
              step="1"
              placeholder="Enter amount in ₹"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="category">Category</Label>
            <Select value={category} onValueChange={(val) => setCategory(val as Category)}>
              <SelectTrigger id="category">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {cat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="What was this expense for?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="date">Date</Label>
            <Input
              id="date"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} className="flex-1">
              Cancel
            </Button>
            <Button type="submit" className="flex-1">
              {expense ? 'Save Changes' : 'Add Expense'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
