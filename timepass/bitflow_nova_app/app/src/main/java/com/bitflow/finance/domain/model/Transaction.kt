package com.bitflow.finance.domain.model

import java.time.LocalDate
import java.time.LocalDateTime

enum class ActivityType {
    EXPENSE, INCOME, TRANSFER
}

data class Activity(
    val id: Long = 0,
    val accountId: Long,
    val activityDate: LocalDate,
    val valueDate: LocalDate?,
    val description: String,
    val reference: String?,
    val amount: Double,
    val type: ActivityType,
    val categoryId: Long?,
    val tags: List<String> = emptyList(),
    val billPhotoUri: String? = null,
    val notes: String? = null,
    val balanceAfterTxn: Double? = null, // Balance from bank statement
    val createdAt: LocalDateTime = LocalDateTime.now(),
    val updatedAt: LocalDateTime = LocalDateTime.now(),
    // Auto-learning fields
    val isAutoCategorized: Boolean = false,
    val confidenceScore: Float? = null,
    val context: AppMode = AppMode.PERSONAL,
    val linkedGoalId: Long? = null // Phase 4: Intent-Based Finance
)

// Legacy type alias for backward compatibility during migration
@Deprecated("Use Activity instead", ReplaceWith("Activity"))
typealias Transaction = Activity

@Deprecated("Use ActivityType instead", ReplaceWith("ActivityType"))
typealias TransactionDirection = ActivityType
