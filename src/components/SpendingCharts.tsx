import { useMemo } from 'react'
import { Card } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { Expense, Category } from '@/lib/types'
import { CATEGORIES, CATEGORY_COLORS, formatCurrency } from '@/lib/constants'

interface SpendingChartsProps {
  expenses: Expense[]
  currentMonth: string
}

export function SpendingCharts({ expenses, currentMonth }: SpendingChartsProps) {
  const categoryData = useMemo(() => {
    const [year, month] = currentMonth.split('-')
    const monthExpenses = expenses.filter(e => {
      const expenseDate = new Date(e.date)
      return expenseDate.getFullYear() === parseInt(year) && 
             expenseDate.getMonth() === parseInt(month) - 1
    })

    const categoryTotals = CATEGORIES.map(category => {
      const total = monthExpenses
        .filter(e => e.category === category)
        .reduce((sum, e) => sum + e.amount, 0)
      
      return {
        category,
        amount: total,
        fill: CATEGORY_COLORS[category]
      }
    }).filter(item => item.amount > 0)

    return categoryTotals
  }, [expenses, currentMonth])

  const dailyData = useMemo(() => {
    const [year, month] = currentMonth.split('-')
    const daysInMonth = new Date(parseInt(year), parseInt(month), 0).getDate()
    
    const dailyTotals: Record<number, number> = {}
    
    expenses.forEach(expense => {
      const expenseDate = new Date(expense.date)
      if (expenseDate.getFullYear() === parseInt(year) && 
          expenseDate.getMonth() === parseInt(month) - 1) {
        const day = expenseDate.getDate()
        dailyTotals[day] = (dailyTotals[day] || 0) + expense.amount
      }
    })

    return Array.from({ length: daysInMonth }, (_, i) => ({
      day: i + 1,
      amount: dailyTotals[i + 1] || 0
    })).filter(item => item.amount > 0)
  }, [expenses, currentMonth])

  const totalSpent = categoryData.reduce((sum, item) => sum + item.amount, 0)

  if (categoryData.length === 0) {
    return (
      <Card className="p-12">
        <div className="text-center">
          <p className="text-lg font-medium text-muted-foreground">No expenses this month</p>
          <p className="text-sm text-muted-foreground mt-2">Add some expenses to see your spending trends</p>
        </div>
      </Card>
    )
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Spending by Category</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={categoryData}
              dataKey="amount"
              nameKey="category"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label={(entry) => `${entry.category}: ${formatCurrency(entry.amount)}`}
            >
              {categoryData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value: number) => formatCurrency(value)}
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '0.5rem'
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="mt-4 text-center">
          <p className="text-sm text-muted-foreground">Total Spent</p>
          <p className="text-2xl font-semibold tabular-nums">{formatCurrency(totalSpent)}</p>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Daily Spending</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dailyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="day" 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickFormatter={(value) => `$${value}`}
            />
            <Tooltip 
              formatter={(value: number) => formatCurrency(value)}
              labelFormatter={(label) => `Day ${label}`}
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '0.5rem'
              }}
            />
            <Bar dataKey="amount" fill="hsl(var(--accent))" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  )
}
