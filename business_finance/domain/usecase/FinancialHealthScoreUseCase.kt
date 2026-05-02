package com.bitflow.finance.domain.usecase

import com.bitflow.finance.domain.repository.TransactionRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import java.time.LocalDate

data class FinancialHealth(
    val score: Int, // 0-1000
    val savingsRateExScore: Int, // 0-100
    val budgetScore: Int,
    val debtScore: Int,
    val status: HealthStatus
)

enum class HealthStatus {
    CRITICAL, VULNERABLE, STABLE, HEALTHY, EXCELLENT
}

class FinancialHealthScoreUseCase @Inject constructor(
    private val transactionRepository: TransactionRepository
) {
    operator fun invoke(): Flow<FinancialHealth> {
        return transactionRepository.getAllTransactions().map { transactions ->
            if (transactions.isEmpty()) return@map FinancialHealth(0, 0, 0, 0, HealthStatus.VULNERABLE)
            
            // 1. Savings Rate (40% weight)
            val lastMonth = LocalDate.now().minusMonths(1)
            val monthTxns = transactions.filter { it.activityDate.isAfter(lastMonth) }
            
            val income = monthTxns.filter { it.type == com.bitflow.finance.domain.model.ActivityType.INCOME }.sumOf { it.amount }
            val expense = monthTxns.filter { it.type == com.bitflow.finance.domain.model.ActivityType.EXPENSE }.sumOf { it.amount }
            
            val savingsRate = if (income > 0) ((income - expense) / income) * 100 else 0.0
            val sScore = (savingsRate * 3).coerceIn(0.0, 100.0).toInt() // 33% savings = 100 score

            // 2. Volatility / Stability (30% weight)
            // Ideally check consistency, but for now simple Budget Adherence proxy
            // Let's assume stability if expenses < income
            val bScore = if (income > expense) 100 else 50
            
            // 3. Debt/Income Ratio (30% weight)
            // Placeholder: Assume 100 if no debt payments detected
            val dScore = 100 
            
            // Total Weighted Score (0 - 1000 scale)
            val finalScore = ((sScore * 0.4) + (bScore * 0.3) + (dScore * 0.3)) * 10
            
            val status = when {
                finalScore > 800 -> HealthStatus.EXCELLENT
                finalScore > 600 -> HealthStatus.HEALTHY
                finalScore > 400 -> HealthStatus.STABLE
                finalScore > 200 -> HealthStatus.VULNERABLE
                else -> HealthStatus.CRITICAL
            }
            
            FinancialHealth(finalScore.toInt(), sScore, bScore, dScore, status)
        }
    }
}
