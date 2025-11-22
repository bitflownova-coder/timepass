import { useState, useMemo } from 'react'
import { useKV } from '@github/spark/hooks'
import { useTheme } from '@/hooks/use-theme'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Plus, Wallet, ChartBar, Tag } from '@phosphor-icons/react'
import { LoginPage } from '@/components/LoginPage'
import { Header } from '@/components/Header'
import { ExpenseDialog } from '@/components/ExpenseDialog'
import { ExpenseItem } from '@/components/ExpenseItem'
import { StatCard } from '@/components/StatCard'
import { BudgetCard } from '@/components/BudgetCard'
import { SpendingCharts } from '@/components/SpendingCharts'
import { Expense, BudgetMap, Category } from '@/lib/types'
import { CATEGORIES, getCurrentMonthYear, getMonthYear } from '@/lib/constants'
import { toast } from 'sonner'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

function App() {
  useTheme()
  const [userEmail, setUserEmail] = useKV<string | null>('user-email', null)
  const [expenses, setExpenses] = useKV<Expense[]>('expenses', [])
  const [budgets, setBudgets] = useKV<BudgetMap>('budgets', {} as BudgetMap)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingExpense, setEditingExpense] = useState<Expense | undefined>()
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const currentMonth = getCurrentMonthYear()

  const currentMonthExpenses = useMemo(() => {
    return (expenses || []).filter(e => getMonthYear(e.date) === currentMonth)
  }, [expenses, currentMonth])

  const lastMonthExpenses = useMemo(() => {
    const [year, month] = currentMonth.split('-')
    const lastMonth = new Date(parseInt(year), parseInt(month) - 2, 1)
    const lastMonthStr = `${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, '0')}`
    return (expenses || []).filter(e => getMonthYear(e.date) === lastMonthStr)
  }, [expenses, currentMonth])

  const currentTotal = useMemo(() => {
    return currentMonthExpenses.reduce((sum, e) => sum + e.amount, 0)
  }, [currentMonthExpenses])

  const lastMonthTotal = useMemo(() => {
    return lastMonthExpenses.reduce((sum, e) => sum + e.amount, 0)
  }, [lastMonthExpenses])

  const trend = useMemo(() => {
    if (lastMonthTotal === 0) return 0
    return ((currentTotal - lastMonthTotal) / lastMonthTotal) * 100
  }, [currentTotal, lastMonthTotal])

  const totalBudget = useMemo(() => {
    return Object.values(budgets || {}).reduce((sum, b) => sum + (b || 0), 0)
  }, [budgets])

  const budgetStatus = useMemo(() => {
    if (totalBudget === 0) return 'default'
    const percentage = (currentTotal / totalBudget) * 100
    if (percentage >= 100) return 'destructive'
    if (percentage >= 80) return 'warning'
    return 'success'
  }, [currentTotal, totalBudget])

  const overBudgetCategories = useMemo(() => {
    return CATEGORIES.filter(cat => {
      const budget = (budgets || {})[cat] || 0
      if (budget === 0) return false
      const spent = currentMonthExpenses
        .filter(e => e.category === cat)
        .reduce((sum, e) => sum + e.amount, 0)
      return spent > budget
    })
  }, [budgets, currentMonthExpenses])

  const sortedExpenses = useMemo(() => {
    return [...(expenses || [])].sort((a, b) => 
      new Date(b.date).getTime() - new Date(a.date).getTime()
    )
  }, [expenses])

  const handleLogin = (email: string) => {
    setUserEmail(email)
  }

  const handleLogout = () => {
    setUserEmail(null)
    toast.success('Signed out successfully')
  }

  if (!userEmail) {
    return <LoginPage onLogin={handleLogin} />
  }

  const handleSaveExpense = (expenseData: Omit<Expense, 'id' | 'createdAt'>) => {
    if (editingExpense) {
      setExpenses(current => 
        (current || []).map(e => 
          e.id === editingExpense.id 
            ? { ...e, ...expenseData }
            : e
        )
      )
      toast.success('Expense updated')
      setEditingExpense(undefined)
    } else {
      const newExpense: Expense = {
        ...expenseData,
        id: `exp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        createdAt: new Date().toISOString()
      }
      setExpenses(current => [...(current || []), newExpense])
      toast.success('Expense added')
    }
  }

  const handleEditExpense = (expense: Expense) => {
    setEditingExpense(expense)
    setDialogOpen(true)
  }

  const handleDeleteExpense = (id: string) => {
    setDeleteId(id)
  }

  const confirmDelete = () => {
    if (deleteId) {
      setExpenses(current => (current || []).filter(e => e.id !== deleteId))
      toast.success('Expense deleted')
      setDeleteId(null)
    }
  }

  const handleBudgetChange = (category: Category, amount: number) => {
    setBudgets(current => (({
      ...(current || {}),
      [category]: amount
    }) as BudgetMap))
  }

  const handleDialogOpenChange = (open: boolean) => {
    setDialogOpen(open)
    if (!open) {
      setEditingExpense(undefined)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Header userEmail={userEmail} onLogout={handleLogout} />
      
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-semibold text-foreground tracking-tight">Expense Dashboard</h2>
            <p className="text-muted-foreground mt-1">Track your expenses and manage your budget</p>
          </div>
          <Button onClick={() => setDialogOpen(true)} size="lg" className="gap-2">
            <Plus className="w-5 h-5" />
            <span className="hidden sm:inline">Add Expense</span>
          </Button>
        </div>

        {overBudgetCategories.length > 0 && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>
              You're over budget in {overBudgetCategories.length} {overBudgetCategories.length === 1 ? 'category' : 'categories'}: {overBudgetCategories.join(', ')}
            </AlertDescription>
          </Alert>
        )}

        <div className="grid gap-6 md:grid-cols-3 mb-8">
          <StatCard 
            label="Total Spent This Month" 
            value={currentTotal}
            trend={trend}
          />
          <StatCard 
            label="Total Budget" 
            value={totalBudget}
            variant={totalBudget > 0 ? 'default' : 'default'}
          />
          <StatCard 
            label="Remaining Budget" 
            value={totalBudget - currentTotal}
            variant={budgetStatus}
          />
        </div>

        <Tabs defaultValue="expenses" className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="expenses" className="gap-2">
              <Wallet className="w-4 h-4" />
              <span className="hidden sm:inline">Expenses</span>
            </TabsTrigger>
            <TabsTrigger value="budgets" className="gap-2">
              <Tag className="w-4 h-4" />
              <span className="hidden sm:inline">Budgets</span>
            </TabsTrigger>
            <TabsTrigger value="trends" className="gap-2">
              <ChartBar className="w-4 h-4" />
              <span className="hidden sm:inline">Trends</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="expenses" className="space-y-4">
            {sortedExpenses.length === 0 ? (
              <div className="text-center py-16">
                <Wallet className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No expenses yet</h3>
                <p className="text-muted-foreground mb-6">Start tracking your spending by adding your first expense</p>
                <Button onClick={() => setDialogOpen(true)} className="gap-2">
                  <Plus className="w-5 h-5" />
                  Add Your First Expense
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {sortedExpenses.map(expense => (
                  <ExpenseItem
                    key={expense.id}
                    expense={expense}
                    onEdit={handleEditExpense}
                    onDelete={handleDeleteExpense}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="budgets" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {CATEGORIES.map(category => (
                <BudgetCard
                  key={category}
                  category={category}
                  budget={(budgets || {})[category] || 0}
                  expenses={currentMonthExpenses}
                  onBudgetChange={handleBudgetChange}
                />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="trends" className="space-y-6">
            <SpendingCharts expenses={expenses || []} currentMonth={currentMonth} />
          </TabsContent>
        </Tabs>
      </div>

      <ExpenseDialog
        open={dialogOpen}
        onOpenChange={handleDialogOpenChange}
        onSave={handleSaveExpense}
        expense={editingExpense}
      />

      <AlertDialog open={deleteId !== null} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Expense</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this expense? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export default App