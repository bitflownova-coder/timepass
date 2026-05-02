package com.bitflow.finance.domain.model

import com.bitflow.finance.data.local.entity.*

data class BackupData(
    val version: Int = 1,
    val timestamp: Long = System.currentTimeMillis(),
    val transactions: List<TransactionEntity>,
    val categories: List<CategoryEntity>,
    val savingsGoals: List<SavingsGoalEntity>,
    val billReminders: List<BillReminderEntity>,
    val learningRules: List<LearningRuleEntity>,
    val recurringPatterns: List<RecurringPatternEntity>,
    val auditLogs: List<TransactionAuditLogEntity>
)
