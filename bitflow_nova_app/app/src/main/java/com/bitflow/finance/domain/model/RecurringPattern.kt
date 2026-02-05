package com.bitflow.finance.domain.model

import java.time.LocalDate

/**
 * Detected recurring payment pattern (subscription detective)
 */
data class RecurringPattern(
    val id: Long = 0,
    val userId: String,
    val merchantName: String,
    val averageAmount: Double,
    val frequency: RecurrenceFrequency,
    val intervalDays: Int,
    val occurrenceCount: Int,
    val lastTransactionDate: LocalDate,
    val nextExpectedDate: LocalDate,
    val confidenceScore: Float,
    val isConfirmedSubscription: Boolean = false,
    val isDismissed: Boolean = false,
    val categoryId: Long?,
    val type: ActivityType = ActivityType.EXPENSE
)

enum class RecurrenceFrequency {
    DAILY,
    WEEKLY,
    MONTHLY,
    YEARLY
}

/**
 * UI-friendly subscription card data
 */
data class SubscriptionDetectionCard(
    val id: Long,
    val merchantName: String,
    val averageAmount: Double,
    val frequency: String, // "monthly", "weekly", etc.
    val confidenceScore: Float,
    val nextExpectedDate: LocalDate
)
