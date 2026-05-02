package com.bitflow.finance.domain.usecase

import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.model.RecurringPattern
import com.bitflow.finance.domain.model.RecurrenceFrequency
import com.bitflow.finance.domain.model.SubscriptionDetectionCard
import com.bitflow.finance.domain.repository.TransactionRepository
import kotlinx.coroutines.flow.first
import java.time.LocalDate
import java.time.temporal.ChronoUnit
import javax.inject.Inject
import kotlin.math.abs

/**
 * Subscription Detective - Scans transaction history for recurring payments
 * 
 * Philosophy: Don't ask users to set up subscriptions. Find them automatically.
 */
class DetectSubscriptionsUseCase @Inject constructor(
    private val transactionRepository: TransactionRepository,
    private val authRepository: com.bitflow.finance.domain.repository.AuthRepository
) {
    /**
     * Scan all activities and detect recurring patterns
     */
    suspend fun detectRecurringPayments(): List<RecurringPattern> {
        val userId = authRepository.currentUserId.first()
        val activities = transactionRepository.getAllTransactions().first()
        
        // Group activities by merchant name (extracted from description)
        val merchantGroups = activities
            .filter { it.type == com.bitflow.finance.domain.model.ActivityType.EXPENSE }
            .groupBy { extractMerchantName(it.description) }
            .filter { it.key.isNotBlank() }
        
        val patterns = mutableListOf<RecurringPattern>()
        
        for ((merchant, merchantActivities) in merchantGroups) {
            if (merchantActivities.size >= 2) { // Need at least 2 occurrences
                val pattern = analyzePattern(merchant, merchantActivities, userId)
                if (pattern != null) {
                    patterns.add(pattern)
                }
            }
        }
        
        return patterns
    }

    /**
     * Analyze a group of transactions to determine if they form a recurring pattern
     */
    private suspend fun analyzePattern(
        merchant: String,
        activities: List<Activity>,
        userId: String
    ): RecurringPattern? {
        if (activities.size < 2) return null
        
        // Sort by date
        val sortedActivities = activities.sortedBy { it.activityDate }
        
        // Calculate intervals between transactions
        val intervals = mutableListOf<Long>()
        for (i in 1 until sortedActivities.size) {
            val daysBetween = ChronoUnit.DAYS.between(
                sortedActivities[i - 1].activityDate,
                sortedActivities[i].activityDate
            )
            intervals.add(daysBetween)
        }
        
        // Determine frequency based on average interval
        val avgInterval = intervals.average()
        val frequency = when {
            isCloseTo(avgInterval, 1.0, 0.2) -> RecurrenceFrequency.DAILY
            isCloseTo(avgInterval, 7.0, 1.0) -> RecurrenceFrequency.WEEKLY
            isCloseTo(avgInterval, 30.0, 5.0) -> RecurrenceFrequency.MONTHLY
            isCloseTo(avgInterval, 365.0, 10.0) -> RecurrenceFrequency.YEARLY
            else -> return null // Not a recognized pattern
        }
        
        // Check amount consistency (within 10% variance)
        val avgAmount = activities.map { it.amount }.average()
        val amountVariance = activities.map { abs(it.amount - avgAmount) / avgAmount }.average()
        
        if (amountVariance > 0.1) return null // Too much variance
        
        // Check if pattern already exists
        val existingPattern = transactionRepository.findRecurringPattern(merchant)
        if (existingPattern != null && existingPattern.isConfirmedSubscription) {
            return null // Already confirmed
        }
        
        val lastDate = sortedActivities.last().activityDate
        val intervalDays = avgInterval.toInt()
        val nextExpected = lastDate.plusDays(intervalDays.toLong())
        // Simplified confidence score
        val confidence = 0.8 + (if(activities.size > 5) 0.1 else 0.0)

        return RecurringPattern(
            userId = userId,
            merchantName = merchant,
            averageAmount = avgAmount,
            frequency = frequency,
            intervalDays = intervalDays,
            lastTransactionDate = lastDate,
            nextExpectedDate = nextExpected,
            occurrenceCount = activities.size,
            confidenceScore = confidence.toFloat(),
            isConfirmedSubscription = false,
            isDismissed = false,
            categoryId = activities.firstOrNull()?.categoryId,
            type = com.bitflow.finance.domain.model.ActivityType.EXPENSE
        )
    }

    /**
     * Convert patterns to UI-friendly detection cards
     */
    fun patternsToDetectionCards(patterns: List<RecurringPattern>): List<SubscriptionDetectionCard> {
        return patterns
            .filter { !it.isConfirmedSubscription && !it.isDismissed }
            .map { pattern ->
                SubscriptionDetectionCard(
                    id = pattern.id,
                    merchantName = pattern.merchantName,
                    averageAmount = pattern.averageAmount,
                    frequency = pattern.frequency.name,
                    confidenceScore = pattern.confidenceScore,
                    nextExpectedDate = pattern.nextExpectedDate
                )
            }
    }

    /**
     * Extract merchant name from transaction description
     */
    private fun extractMerchantName(description: String): String {
        // Common patterns in UPI/card transactions
        val patterns = listOf(
            Regex("(?:UPI/(?:CR|DR)/\\d+/)([^/]+)"),  // UPI transactions
            Regex("(?:OTHPG|SBIPG|OTHPOS)\\s+\\w+\\s+(.+?)\\s+[A-Z]{2,}"),  // Card transactions
            Regex("(?:ATM WDL-)(.+?)\\s{2,}"),  // ATM withdrawals
        )
        
        for (pattern in patterns) {
            val match = pattern.find(description)
            if (match != null && match.groupValues.size > 1) {
                return match.groupValues[1].trim().lowercase()
            }
        }
        
        // Fallback: take first meaningful word
        return description
            .split("/", " ")
            .firstOrNull { it.length > 3 }
            ?.trim()
            ?.lowercase()
            ?: ""
    }

    /**
     * Check if a value is close to a target within a tolerance
     */
    private fun isCloseTo(value: Double, target: Double, tolerance: Double): Boolean {
        return abs(value - target) <= tolerance
    }

    /**
     * Run subscription detection on imported statement
     */
    suspend fun detectSubscriptionsInBatch(activities: List<Activity>) {
        val patterns = detectRecurringPayments()
        
        for (pattern in patterns) {
            // Save new patterns
            val existing = transactionRepository.findRecurringPattern(pattern.merchantName)
            if (existing == null) {
                transactionRepository.insertRecurringPattern(pattern)
            } else {
                // Update existing pattern with new data
                transactionRepository.updateRecurringPattern(
                    existing.copy(
                        lastTransactionDate = pattern.lastTransactionDate,
                        nextExpectedDate = pattern.nextExpectedDate,
                        occurrenceCount = pattern.occurrenceCount,
                        averageAmount = pattern.averageAmount,
                        confidenceScore = pattern.confidenceScore
                    )
                )
            }
        }
    }
}
