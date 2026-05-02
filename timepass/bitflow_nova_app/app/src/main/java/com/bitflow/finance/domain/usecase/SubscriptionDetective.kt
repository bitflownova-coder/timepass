package com.bitflow.finance.domain.usecase

import com.bitflow.finance.data.local.entity.TransactionEntity
import com.bitflow.finance.domain.model.RecurringPattern
import com.bitflow.finance.domain.model.RecurrenceFrequency
import com.bitflow.finance.domain.model.ActivityType
import java.time.LocalDate
import java.time.temporal.ChronoUnit
import javax.inject.Inject
import kotlin.math.abs

/**
 * Subscription Detective: Analyzes transaction patterns to detect recurring payments.
 * Uses "Don't Make Me Think" approach - only surfaces high-confidence matches.
 */
class SubscriptionDetective @Inject constructor() {
    
    companion object {
        private const val MIN_OCCURRENCES = 2 // Need at least 2 to establish pattern
        private const val AMOUNT_VARIANCE_THRESHOLD = 0.15 // 15% tolerance
        private const val DAILY_INTERVAL_DAYS = 1
        private const val WEEKLY_INTERVAL_DAYS = 7
        private const val MONTHLY_INTERVAL_DAYS = 30
        private const val YEARLY_INTERVAL_DAYS = 365
        private const val INTERVAL_TOLERANCE_DAYS = 3 // Allow ±3 days variance
    }
    
    /**
     * Detect potential subscriptions from transaction history.
     * Returns only high-confidence patterns worth showing to user.
     */
    suspend fun detectPotentialSubscriptions(
        transactions: List<TransactionEntity>,
        lookbackMonths: Int = 3
    ): List<RecurringPattern> {
        val cutoffDate = LocalDate.now().minusMonths(lookbackMonths.toLong())
        val recentTransactions = transactions.filter { it.txnDate >= cutoffDate }
        
        // Group by merchant name
        val groupedByMerchant = recentTransactions
            .filter { !it.merchantName.isNullOrBlank() }
            .groupBy { normalizeMerchantName(it.merchantName!!) }
        
        val patterns = mutableListOf<RecurringPattern>()
        
        for ((merchantName, merchantTransactions) in groupedByMerchant) {
            if (merchantTransactions.size < MIN_OCCURRENCES) continue
            
            val pattern = analyzePattern(merchantName, merchantTransactions)
            if (pattern != null) {
                patterns.add(pattern)
            }
        }
        
        return patterns.sortedByDescending { it.occurrenceCount }
    }
    
    /**
     * Analyze a group of transactions to determine if they form a recurring pattern
     */
    private fun analyzePattern(
        merchantName: String,
        transactions: List<TransactionEntity>
    ): RecurringPattern? {
        if (transactions.size < MIN_OCCURRENCES) return null
        
        val sortedTransactions = transactions.sortedBy { it.txnDate }
        val amounts = sortedTransactions.map { it.amount }
        val dates = sortedTransactions.map { it.txnDate }
        
        // Check amount consistency
        val avgAmount = amounts.average()
        val amountVariance = amounts.all { 
            abs(it - avgAmount) / avgAmount <= AMOUNT_VARIANCE_THRESHOLD 
        }
        
        if (!amountVariance) return null
        
        // Calculate intervals between transactions
        val intervals = mutableListOf<Long>()
        for (i in 0 until dates.size - 1) {
            val daysBetween = ChronoUnit.DAYS.between(dates[i], dates[i + 1])
            intervals.add(daysBetween)
        }
        
        if (intervals.isEmpty()) return null
        
        val avgInterval = intervals.average()
        
        // Detect frequency type
        val frequency = when {
            isCloseToInterval(avgInterval, DAILY_INTERVAL_DAYS) -> "Daily"
            isCloseToInterval(avgInterval, WEEKLY_INTERVAL_DAYS) -> "Weekly"
            isCloseToInterval(avgInterval, MONTHLY_INTERVAL_DAYS) -> "Monthly"
            isCloseToInterval(avgInterval, YEARLY_INTERVAL_DAYS) -> "Yearly"
            else -> "Custom (${avgInterval.toInt()} days)"
        }
        
        // Calculate confidence score
        val intervalConsistency = calculateIntervalConsistency(intervals, avgInterval)
        val occurrenceBonus = minOf(transactions.size / 10f, 0.3f) // Up to +0.3 for more occurrences
        val confidenceScore = (intervalConsistency * 0.7f) + occurrenceBonus
        
        // Predict next date
        val lastDate = dates.last()
        val nextExpectedDate = lastDate.plusDays(avgInterval.toLong())
        
        return RecurringPattern(
            userId = transactions.first().userId,
            merchantName = merchantName,
            averageAmount = avgAmount,
            frequency = when {
                isCloseToInterval(avgInterval, DAILY_INTERVAL_DAYS) -> RecurrenceFrequency.DAILY
                isCloseToInterval(avgInterval, WEEKLY_INTERVAL_DAYS) -> RecurrenceFrequency.WEEKLY
                isCloseToInterval(avgInterval, MONTHLY_INTERVAL_DAYS) -> RecurrenceFrequency.MONTHLY
                else -> RecurrenceFrequency.YEARLY
            },
            intervalDays = avgInterval.toInt(),
            lastTransactionDate = lastDate,
            nextExpectedDate = nextExpectedDate,
            occurrenceCount = transactions.size,
            confidenceScore = confidenceScore.toFloat(),
            isConfirmedSubscription = false,
            isDismissed = false,
            type = com.bitflow.finance.domain.model.ActivityType.EXPENSE, // Assuming expense for now
            categoryId = transactions.first().categoryId
        )
    }
    
    /**
     * Check if interval is close to expected frequency
     */
    private fun isCloseToInterval(actual: Double, expected: Int): Boolean {
        return abs(actual - expected) <= INTERVAL_TOLERANCE_DAYS
    }
    
    /**
     * Calculate how consistent the intervals are (0-1 score)
     */
    private fun calculateIntervalConsistency(intervals: List<Long>, avgInterval: Double): Float {
        val deviations = intervals.map { abs(it - avgInterval) / avgInterval }
        val avgDeviation = deviations.average()
        return (1f - avgDeviation.toFloat()).coerceIn(0f, 1f)
    }
    
    /**
     * Normalize merchant name for matching
     * Removes special characters, extra spaces, etc.
     */
    private fun normalizeMerchantName(name: String): String {
        return name
            .trim()
            .lowercase()
            .replace(Regex("[^a-z0-9\\s]"), "")
            .replace(Regex("\\s+"), " ")
    }
}
