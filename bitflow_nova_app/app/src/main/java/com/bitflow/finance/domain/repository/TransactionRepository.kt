package com.bitflow.finance.domain.repository

import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.model.Category
import com.bitflow.finance.domain.model.CategoryLearningRule
import com.bitflow.finance.domain.model.RecurringPattern
import com.bitflow.finance.domain.model.SubscriptionDetectionCard
import kotlinx.coroutines.flow.Flow
import java.time.LocalDate

interface TransactionRepository {
    // Activity methods (legacy Transaction name for compatibility)
    fun getAllTransactions(): Flow<List<Activity>>
    fun getTransactionsForAccount(accountId: Long): Flow<List<Activity>>
    fun getTransactionsInPeriod(startDate: LocalDate, endDate: LocalDate): Flow<List<Activity>>
    suspend fun insertTransaction(transaction: Activity): Long
    suspend fun insertTransactions(transactions: List<Activity>)
    suspend fun updateTransaction(transaction: Activity)
    suspend fun findExistingTransaction(accountId: Long, date: LocalDate, amount: Double, description: String): Activity?
    suspend fun getTransactionById(id: Long): Activity?
    
    // Category methods
    fun getAllCategories(): Flow<List<Category>>
    suspend fun insertCategory(category: Category): Long
    suspend fun incrementCategoryUsage(categoryId: Long)
    suspend fun mergeCategories(sourceCategoryId: Long, targetCategoryId: Long)
    suspend fun uncategorizeActivities(categoryId: Long)
    suspend fun deleteCategory(categoryId: Long)
    suspend fun updateCategory(category: Category)
    
    // Transaction deletion
    suspend fun deleteTransaction(activityId: Long)
    
    // Auto-learning methods
    suspend fun insertLearningRule(rule: CategoryLearningRule)
    suspend fun updateLearningRule(rule: CategoryLearningRule)
    suspend fun findLearningRule(pattern: String): CategoryLearningRule?
    suspend fun getAllLearningRules(): Flow<List<CategoryLearningRule>>
    
    // Subscription detection methods
    suspend fun insertRecurringPattern(pattern: RecurringPattern)
    suspend fun updateRecurringPattern(pattern: RecurringPattern)
    suspend fun findRecurringPattern(merchantName: String): RecurringPattern?
    suspend fun getUnconfirmedSubscriptions(): List<SubscriptionDetectionCard>
    suspend fun confirmSubscription(patternId: Long)
    suspend fun dismissSubscription(patternId: Long)
    
    // Daily Pulse calculation methods
    suspend fun getMonthlyIncome(): Double
    suspend fun getMonthlyFixedExpenses(): Double
    suspend fun getTodayExpenses(): Double
    suspend fun getRecentTransactions(limit: Int): Flow<List<Activity>>
    
    // Subscription detection - get raw TransactionEntity for pattern analysis
    suspend fun getTransactionsForSubscriptionDetection(startDate: LocalDate): List<com.bitflow.finance.data.local.entity.TransactionEntity>
    
    // Performance optimization methods
    suspend fun getAllTransactionsForDeduplication(accountId: Long): List<Activity>
    suspend fun calculateAccountBalance(accountId: Long, initialBalance: Double): Double
    
    // Get the latest transaction balance from statements
    suspend fun getLatestTransactionBalance(accountId: Long): Double?

    // Tax Helper
    fun getTaxDeductibleTransactions(startDate: LocalDate, endDate: LocalDate): Flow<List<Activity>>

    // Audit Logs
    fun getAuditLogs(transactionId: Long): Flow<List<com.bitflow.finance.data.local.entity.TransactionAuditLogEntity>>
}
