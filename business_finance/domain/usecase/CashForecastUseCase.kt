package com.bitflow.finance.domain.usecase

import com.bitflow.finance.data.local.dao.RecurringPatternDao
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.model.RecurrenceFrequency
import com.bitflow.finance.domain.repository.BillReminderRepository
import com.bitflow.finance.domain.repository.TransactionRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map
import java.time.LocalDate
import java.time.temporal.ChronoUnit
import javax.inject.Inject
import kotlin.math.abs

data class DailyBalanceProjection(
    val date: LocalDate,
    val startingBalance: Double,
    val income: Double,
    val expenses: Double,
    val endingBalance: Double,
    val events: List<ProjectionEvent>
)

data class ProjectionEvent(
    val name: String,
    val amount: Double,
    val type: ActivityType,
    val isRecurring: Boolean
)

class CashForecastUseCase @Inject constructor(
    private val transactionRepository: TransactionRepository,
    private val accountRepository: com.bitflow.finance.domain.repository.AccountRepository,
    private val billReminderRepository: BillReminderRepository,
    private val recurringPatternDao: RecurringPatternDao, // Using DAO directly for now as Repo might not expose all
    private val authRepository: com.bitflow.finance.domain.repository.AuthRepository
) {

    operator fun invoke(userId: String, daysToProject: Int = 30): Flow<List<DailyBalanceProjection>> {
        return combine(
            accountRepository.getAllAccounts(), // Get current balance
            billReminderRepository.getActiveReminders(),
            recurringPatternDao.getConfirmedSubscriptions(userId) // Using DAO flow
        ) { accounts, reminders, subscriptions ->
            
            // 1. Calculate confirmed current balance
            val currentBalance = accounts.sumOf { it.currentBalance }
            
            val projections = mutableListOf<DailyBalanceProjection>()
            var runningBalance = currentBalance
            val today = LocalDate.now()
            
            // 2. Project for each day
            for (i in 1..daysToProject) {
                val date = today.plusDays(i.toLong())
                val dayEvents = mutableListOf<ProjectionEvent>()
                
                // A. Check Bill Reminders
                // Simple logic: If dueDay == date.dayOfMonth
                reminders.filter { it.isActive }.forEach { bill ->
                    // Handle month overflow logic properly in real app, simplistic here
                    // e.g. dueDay 31 in Feb -> skip or move to 28
                    // For now, simpler equality check:
                    if (bill.dueDay == date.dayOfMonth) {
                        dayEvents.add(
                            ProjectionEvent(
                                name = bill.name,
                                amount = bill.amount,
                                type = ActivityType.EXPENSE,
                                isRecurring = bill.isRecurring
                            )
                        )
                    }
                }
                
                // B. Check Recurring Patterns (Subscriptions & Income)
                subscriptions.map { it.toDomain() }.forEach { pattern ->
                    if (isDueOnDate(pattern, date)) {
                        dayEvents.add(
                            ProjectionEvent(
                                name = pattern.merchantName,
                                amount = pattern.averageAmount,
                                type = pattern.type, 
                                isRecurring = true
                            )
                        )
                    }
                }
                
                // C. Calculate Totals
                val dayIncome = dayEvents.filter { it.type == ActivityType.INCOME }.sumOf { it.amount }
                val dayExpenses = dayEvents.filter { it.type == ActivityType.EXPENSE }.sumOf { it.amount }
                
                val start = runningBalance
                val end = runningBalance + dayIncome - dayExpenses
                
                projections.add(
                    DailyBalanceProjection(
                        date = date,
                        startingBalance = start,
                        income = dayIncome,
                        expenses = dayExpenses,
                        endingBalance = end,
                        events = dayEvents
                    )
                )
                
                runningBalance = end
            }
            
            projections
        }
    }
    
    private fun isDueOnDate(pattern: com.bitflow.finance.domain.model.RecurringPattern, date: LocalDate): Boolean {
        // Only simple logic for now: Check if days between last detected and date is multiple of interval
        // Ideally we use nextExpectedDate and roll it forward
        
        // Better: Use nextExpectedDate. If date matches nextExpectedDate + N * interval
        val nextDate = pattern.nextExpectedDate // pattern.nextExpectedDate is not nullable in my update
        
        val daysDiff = ChronoUnit.DAYS.between(nextDate, date)
        if (daysDiff < 0) return false // Past date relative to expectation
        
        return when (pattern.frequency) {
            RecurrenceFrequency.DAILY -> true
            RecurrenceFrequency.WEEKLY -> daysDiff % 7 == 0L
            RecurrenceFrequency.MONTHLY -> date.dayOfMonth == nextDate.dayOfMonth // Simplification
            RecurrenceFrequency.YEARLY -> date.month == nextDate.month && date.dayOfMonth == nextDate.dayOfMonth
            else -> false
        }
    }

    private fun com.bitflow.finance.data.local.entity.RecurringPatternEntity.toDomain(): com.bitflow.finance.domain.model.RecurringPattern {
        return com.bitflow.finance.domain.model.RecurringPattern(
            id = this.id,
            userId = this.userId,
            merchantName = this.merchantName,
            averageAmount = this.averageAmount,
            frequency = try { com.bitflow.finance.domain.model.RecurrenceFrequency.valueOf(this.frequency) } catch (e: Exception) { com.bitflow.finance.domain.model.RecurrenceFrequency.MONTHLY },
            intervalDays = this.intervalDays,
            occurrenceCount = this.occurrenceCount,
            lastTransactionDate = this.lastTransactionDate,
            nextExpectedDate = this.nextExpectedDate,
            confidenceScore = this.confidenceScore,
            isConfirmedSubscription = this.isConfirmedSubscription,
            categoryId = this.categoryId,
            type = try { ActivityType.valueOf(this.type) } catch (e: Exception) { ActivityType.EXPENSE }
        )
    }
}
