import { Card } from '@/components/ui/card'
import { formatCurrency } from '@/lib/constants'
import { TrendUp, TrendDown } from '@phosphor-icons/react'

interface StatCardProps {
  label: string
  value: number
  trend?: number
  variant?: 'default' | 'success' | 'warning' | 'destructive'
}

export function StatCard({ label, value, trend, variant = 'default' }: StatCardProps) {
  const variantStyles = {
    default: 'bg-card',
    success: 'bg-success/10 border-success/30',
    warning: 'bg-warning/10 border-warning/30',
    destructive: 'bg-destructive/10 border-destructive/30'
  }

  const valueStyles = {
    default: 'text-foreground',
    success: 'text-success',
    warning: 'text-warning-foreground',
    destructive: 'text-destructive'
  }

  return (
    <Card className={`p-6 ${variantStyles[variant]}`}>
      <p className="text-sm font-medium text-muted-foreground mb-1">{label}</p>
      <p className={`text-3xl font-semibold tabular-nums ${valueStyles[variant]}`}>
        {formatCurrency(value)}
      </p>
      {trend !== undefined && trend !== 0 && (
        <div className="flex items-center gap-1 mt-2">
          {trend > 0 ? (
            <TrendUp className="w-4 h-4 text-destructive" weight="bold" />
          ) : (
            <TrendDown className="w-4 h-4 text-success" weight="bold" />
          )}
          <span className={`text-sm font-medium ${trend > 0 ? 'text-destructive' : 'text-success'}`}>
            {Math.abs(trend).toFixed(0)}% vs last month
          </span>
        </div>
      )}
    </Card>
  )
}
