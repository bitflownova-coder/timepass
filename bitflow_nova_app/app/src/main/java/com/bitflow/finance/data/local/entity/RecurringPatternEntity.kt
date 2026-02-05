package com.bitflow.finance.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import java.time.LocalDate

/**
 * Stores detected recurring payment patterns (e.g., subscriptions).
 * Used by the "Subscription Detective" feature.
 */
@Entity(
    tableName = "recurring_patterns",
    indices = [Index(value = ["userId", "merchantName"])]
)
data class RecurringPatternEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val userId: String,
    val merchantName: String,
    val averageAmount: Double,
    val frequency: String, // "Daily", "Weekly", "Monthly", "Yearly"
    val intervalDays: Int,
    val occurrenceCount: Int,
    val lastTransactionDate: LocalDate,
    val nextExpectedDate: LocalDate,
    val confidenceScore: Float,
    val isConfirmedSubscription: Boolean = false,
    val isDismissed: Boolean = false,
    val categoryId: Long?,
    val type: String = "EXPENSE" // "INCOME" or "EXPENSE"
)
