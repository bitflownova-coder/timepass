package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.CategoryDao
import com.bitflow.finance.data.local.dao.LearningRuleDao
import com.bitflow.finance.data.local.dao.RecurringPatternDao
import com.bitflow.finance.data.local.dao.TransactionDao
import com.bitflow.finance.data.local.entity.CategoryEntity
import com.bitflow.finance.data.local.entity.LearningRuleEntity
import com.bitflow.finance.data.local.entity.RecurringPatternEntity
import com.bitflow.finance.data.local.entity.TransactionEntity
import com.bitflow.finance.domain.model.Activity
import com.bitflow.finance.domain.model.ActivityType
import com.bitflow.finance.domain.model.Category
import com.bitflow.finance.domain.model.CategoryLearningRule
import com.bitflow.finance.domain.model.RecurringPattern
import com.bitflow.finance.domain.model.SubscriptionDetectionCard
import com.bitflow.finance.domain.repository.TransactionRepository
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.repository.SettingsRepository
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import java.time.LocalDate
import java.time.ZoneId
import javax.inject.Inject

class TransactionRepositoryImpl @Inject constructor(
    private val transactionDao: TransactionDao,
    private val categoryDao: CategoryDao,
    private val learningRuleDao: LearningRuleDao,
    private val recurringPatternDao: RecurringPatternDao,
    private val transactionAuditDao: com.bitflow.finance.data.local.dao.TransactionAuditDao,
    private val authRepository: AuthRepository,
    private val settingsRepository: SettingsRepository
) : TransactionRepository {

    override fun getAllTransactions(): Flow<List<Activity>> {
        return combine(authRepository.currentUserId, settingsRepository.appMode) { userId, mode ->
            Pair(userId, mode)
        }.flatMapLatest { (userId, mode) ->
            transactionDao.getAllTransactions(userId, mode).map { entities -> entities.map { it.toDomain() } }
        }
    }

    override fun getTransactionsForAccount(accountId: Long): Flow<List<Activity>> {
        return authRepository.currentUserId.flatMapLatest { userId ->
            transactionDao.getTransactionsForAccount(accountId, userId).map { entities -> entities.map { it.toDomain() } }
        }
    }

    override fun getTransactionsInPeriod(startDate: LocalDate, endDate: LocalDate): Flow<List<Activity>> {
        return combine(authRepository.currentUserId, settingsRepository.appMode) { userId, mode ->
            Pair(userId, mode)
        }.flatMapLatest { (userId, mode) ->
            transactionDao.getTransactionsInPeriod(startDate, endDate, userId, mode).map { entities -> entities.map { it.toDomain() } }
        }
    }

    override suspend fun insertTransaction(transaction: Activity): Long {
        val userId = authRepository.currentUserId.first()
        val id = transactionDao.insertTransaction(transaction.toEntity(userId))
        logAudit(
            transactionId = id,
            userId = userId,
            action = com.bitflow.finance.data.local.entity.AuditAction.CREATE,
            newValue = "Created: ${transaction.amount} - ${transaction.description}"
        )
        return id
    }

    override suspend fun insertTransactions(transactions: List<Activity>) {
        // Batch insert without per-transaction logging for performance
        if (transactions.isNotEmpty()) {
            val userId = authRepository.currentUserId.first()
            println("[TransactionRepository] Batch inserting ${transactions.size} transactions")
            transactionDao.insertTransactions(transactions.map { it.toEntity(userId) })
            println("[TransactionRepository] Batch insert completed")
        }
    }

    override suspend fun updateTransaction(transaction: Activity) {
        val userId = authRepository.currentUserId.first()
        val oldTransaction = transactionDao.getTransactionById(transaction.id, userId)?.toDomain()
        
        transactionDao.updateTransaction(transaction.toEntity(userId))
        
        if (oldTransaction != null) {
            if (oldTransaction.amount != transaction.amount) {
                logAudit(transaction.id, userId, com.bitflow.finance.data.local.entity.AuditAction.UPDATE, "amount", oldTransaction.amount.toString(), transaction.amount.toString())
            }
            if (oldTransaction.description != transaction.description) {
                logAudit(transaction.id, userId, com.bitflow.finance.data.local.entity.AuditAction.UPDATE, "description", oldTransaction.description, transaction.description)
            }
            if (oldTransaction.activityDate != transaction.activityDate) {
                logAudit(transaction.id, userId, com.bitflow.finance.data.local.entity.AuditAction.UPDATE, "date", oldTransaction.activityDate.toString(), transaction.activityDate.toString())
            }
        }
    }

    override suspend fun findExistingTransaction(
        accountId: Long,
        date: LocalDate,
        amount: Double,
        description: String
    ): Activity? {
        val userId = authRepository.currentUserId.first()
        return transactionDao.findExistingTransaction(accountId, date, amount, description, userId)?.toDomain()
    }

    override suspend fun getTransactionById(id: Long): Activity? {
        val userId = authRepository.currentUserId.first()
        return transactionDao.getTransactionById(id, userId)?.toDomain()
    }

    private fun TransactionEntity.toDomain(): Activity {
        return Activity(
            id = id,
            accountId = accountId,
            activityDate = txnDate,
            valueDate = valueDate,
            description = description,
            reference = reference,
            amount = amount,
            type = direction,
            categoryId = categoryId,
            tags = tags,
            billPhotoUri = billPhotoUri,
            notes = notes,
            balanceAfterTxn = balanceAfterTxn,
            isAutoCategorized = isAutoCategorized,
            createdAt = createdAt,
            updatedAt = updatedAt,
            context = context,
            linkedGoalId = linkedGoalId
        )
    }

    private fun Activity.toEntity(userId: String): TransactionEntity {
        return TransactionEntity(
            id = id,
            userId = userId,
            accountId = accountId,
            txnDate = activityDate,
            valueDate = valueDate,
            description = description,
            reference = reference,
            amount = amount,
            direction = type,
            categoryId = categoryId,
            tags = tags,
            billPhotoUri = billPhotoUri,
            notes = notes,
            balanceAfterTxn = balanceAfterTxn,
            isAutoCategorized = isAutoCategorized,
            createdAt = createdAt,
            updatedAt = updatedAt,
            context = context,
            linkedGoalId = linkedGoalId
        )
    }
    
    // Category methods
    override fun getAllCategories(): Flow<List<Category>> {
        return authRepository.currentUserId.flatMapLatest { userId ->
            categoryDao.getAllCategories(userId).map { entities -> 
                entities.map { it.toDomain() } 
            }
        }
    }

    override suspend fun insertCategory(category: Category): Long {
        val userId = authRepository.currentUserId.first()
        return categoryDao.insertCategory(category.toEntity(userId))
    }
    
    override suspend fun incrementCategoryUsage(categoryId: Long) {
        categoryDao.incrementUsageCount(categoryId)
    }
    
    override suspend fun mergeCategories(sourceCategoryId: Long, targetCategoryId: Long) {
        val userId = authRepository.currentUserId.first()
        // Update all transactions to use target category
        transactionDao.updateTransactionsCategory(sourceCategoryId, targetCategoryId, userId)
        
        // Update learning rules
        learningRuleDao.updateRulesCategory(sourceCategoryId, targetCategoryId, userId)
        
        // Add source usage count to target
        val sourceCategory = categoryDao.getCategoryById(sourceCategoryId, userId)
        val targetCategory = categoryDao.getCategoryById(targetCategoryId, userId)
        if (sourceCategory != null && targetCategory != null) {
            categoryDao.insertCategory(
                targetCategory.copy(usageCount = targetCategory.usageCount + sourceCategory.usageCount)
            )
        }
    }
    
    override suspend fun uncategorizeActivities(categoryId: Long) {
        val userId = authRepository.currentUserId.first()
        // Move to uncategorized (ID 0 or null)
        transactionDao.updateTransactionsCategory(categoryId, 0L, userId)
    }
    
    override suspend fun deleteCategory(categoryId: Long) {
        val userId = authRepository.currentUserId.first()
        categoryDao.deleteCategory(categoryId, userId)
    }
    
    override suspend fun updateCategory(category: Category) {
        val userId = authRepository.currentUserId.first()
        categoryDao.insertCategory(category.toEntity(userId))
    }
    
    // Learning rule methods
    override suspend fun insertLearningRule(rule: CategoryLearningRule) {
        val userId = authRepository.currentUserId.first()
        learningRuleDao.insertRule(rule.toEntity(userId))
    }
    
    override suspend fun updateLearningRule(rule: CategoryLearningRule) {
        val userId = authRepository.currentUserId.first()
        learningRuleDao.updateRule(rule.toEntity(userId))
    }
    
    override suspend fun findLearningRule(pattern: String): CategoryLearningRule? {
        val userId = authRepository.currentUserId.first()
        return learningRuleDao.findRuleByMerchant(pattern, userId)?.toDomain()
    }
    
    override suspend fun getAllLearningRules(): Flow<List<CategoryLearningRule>> {
        return authRepository.currentUserId.flatMapLatest { userId ->
            learningRuleDao.getAllRules(userId).map { entities ->
                entities.map { it.toDomain() }
            }
        }
    }
    
    // Recurring pattern methods (subscriptions)
    override suspend fun insertRecurringPattern(pattern: RecurringPattern) {
        val userId = authRepository.currentUserId.first()
        recurringPatternDao.insert(pattern.toEntity(userId))
    }
    
    override suspend fun updateRecurringPattern(pattern: RecurringPattern) {
        val userId = authRepository.currentUserId.first()
        recurringPatternDao.update(pattern.toEntity(userId))
    }
    
    override suspend fun findRecurringPattern(merchantName: String): RecurringPattern? {
        val userId = authRepository.currentUserId.first()
        return recurringPatternDao.findByMerchant(userId, merchantName.lowercase())?.toDomain()
    }
    
    override suspend fun getUnconfirmedSubscriptions(): List<SubscriptionDetectionCard> {
        val userId = authRepository.currentUserId.first()
        return recurringPatternDao.getUnconfirmedPatterns(userId).map { entity ->
            SubscriptionDetectionCard(
                id = entity.id,
                merchantName = entity.merchantName,
                averageAmount = entity.averageAmount,
                frequency = entity.frequency,
                confidenceScore = entity.confidenceScore,
                nextExpectedDate = entity.nextExpectedDate
            )
        }
    }
    
    override suspend fun confirmSubscription(patternId: Long) {
        recurringPatternDao.confirmSubscription(patternId)
    }
    
    override suspend fun dismissSubscription(patternId: Long) {
        recurringPatternDao.dismissSubscription(patternId)
    }
    
    // Entity <-> Domain conversions for RecurringPattern
    private fun RecurringPattern.toEntity(userId: String): RecurringPatternEntity {
        return RecurringPatternEntity(
            id = this.id,
            userId = userId,
            merchantName = this.merchantName.lowercase(),
            averageAmount = this.averageAmount,
            frequency = this.frequency.name,
            intervalDays = this.intervalDays,
            occurrenceCount = this.occurrenceCount,
            lastTransactionDate = this.lastTransactionDate,
            nextExpectedDate = this.nextExpectedDate,
            confidenceScore = this.confidenceScore,
            isConfirmedSubscription = this.isConfirmedSubscription,
            isDismissed = false,
            categoryId = this.categoryId,
            type = this.type.name
        )
    }
    
    private fun RecurringPatternEntity.toDomain(): RecurringPattern {
        return RecurringPattern(
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
    
    // Daily Pulse calculation methods
    // Use explicit timezone to prevent date shifting when user travels
    private val appTimeZone = ZoneId.of("Asia/Kolkata")
    
    override suspend fun getMonthlyIncome(): Double {
        val userId = authRepository.currentUserId.first()
        val mode = settingsRepository.appMode.first()
        val today = LocalDate.now(appTimeZone)
        val startOfMonth = today.withDayOfMonth(1)
        val endOfMonth = today.withDayOfMonth(today.lengthOfMonth())
        
        return transactionDao.getTransactionsInPeriod(startOfMonth, endOfMonth, userId, mode)
            .first()
            .filter { it.direction == ActivityType.INCOME }
            .sumOf { it.amount }
    }
    
    override suspend fun getMonthlyFixedExpenses(): Double {
        // Calculate recurring expenses from historical data
        // A "fixed expense" is one that appears 2+ months in a row with similar amount
        val userId = authRepository.currentUserId.first()
        val mode = settingsRepository.appMode.first()
        val today = LocalDate.now(appTimeZone)
        val threeMonthsAgo = today.minusMonths(3)
        
        val transactions = transactionDao.getTransactionsInPeriod(threeMonthsAgo, today, userId, mode)
            .first()
            .filter { it.direction == ActivityType.EXPENSE }
        
        // Group by normalized description (merchant)
        val groupedByMerchant = transactions
            .groupBy { it.description.trim().lowercase().take(20) } // Normalize merchant name
            .filter { it.value.size >= 2 } // Must appear 2+ times
        
        // Sum up the average amount for each recurring expense
        return groupedByMerchant.values.sumOf { merchantTransactions ->
            val avgAmount = merchantTransactions.map { it.amount }.average()
            // Check if amounts are consistent (within 20% variance)
            val isConsistent = merchantTransactions.all { 
                kotlin.math.abs(it.amount - avgAmount) / avgAmount <= 0.20 
            }
            if (isConsistent) avgAmount else 0.0
        }
    }
    
    override suspend fun getTodayExpenses(): Double {
        val userId = authRepository.currentUserId.first()
        val mode = settingsRepository.appMode.first()
        val today = LocalDate.now(appTimeZone)
        
        return transactionDao.getTransactionsInPeriod(today, today, userId, mode)
            .first()
            .filter { it.direction == ActivityType.EXPENSE }
            .sumOf { it.amount }
    }
    
    override suspend fun getRecentTransactions(limit: Int): Flow<List<Activity>> {
        return combine(authRepository.currentUserId, settingsRepository.appMode) { userId, mode ->
            Pair(userId, mode)
        }.flatMapLatest { (userId, mode) ->
            transactionDao.getRecentTransactions(limit, userId, mode).map { entities ->
                entities.map { it.toDomain() }
            }
        }
    }
    
    override suspend fun getTransactionsForSubscriptionDetection(startDate: LocalDate): List<com.bitflow.finance.data.local.entity.TransactionEntity> {
        val userId = authRepository.currentUserId.first()
        return transactionDao.getTransactionsForSubscriptionDetection(startDate, userId)
    }
    
    // Transaction deletion
    override suspend fun deleteTransaction(activityId: Long) {
        val userId = authRepository.currentUserId.first()
        val oldTransaction = transactionDao.getTransactionById(activityId, userId)?.toDomain()
        
        transactionDao.deleteTransaction(activityId, userId)
        
        if (oldTransaction != null) {
             logAudit(
                transactionId = activityId,
                userId = userId,
                action = com.bitflow.finance.data.local.entity.AuditAction.DELETE,
                oldValue = "Deleted: ${oldTransaction.amount} - ${oldTransaction.description}"
            )
        }
    }
    
    override suspend fun getAllTransactionsForDeduplication(accountId: Long): List<Activity> {
        val userId = authRepository.currentUserId.first()
        return transactionDao.getAllTransactionsSync(accountId, userId).map { it.toDomain() }
    }
    
    override suspend fun calculateAccountBalance(accountId: Long, initialBalance: Double): Double {
        val userId = authRepository.currentUserId.first()
        return transactionDao.calculateBalance(accountId, initialBalance, userId)
    }

    override fun getAuditLogs(transactionId: Long): Flow<List<com.bitflow.finance.data.local.entity.TransactionAuditLogEntity>> {
        return transactionAuditDao.getLogsForTransaction(transactionId)
    }

    private suspend fun logAudit(
        transactionId: Long,
        userId: String,
        action: com.bitflow.finance.data.local.entity.AuditAction,
        fieldName: String? = null,
        oldValue: String? = null,
        newValue: String? = null
    ) {
        transactionAuditDao.insertLog(
            com.bitflow.finance.data.local.entity.TransactionAuditLogEntity(
                transactionId = transactionId,
                userId = userId,
                action = action,
                fieldName = fieldName,
                oldValue = oldValue,
                newValue = newValue
            )
        )
    }

    
    override suspend fun getLatestTransactionBalance(accountId: Long): Double? {
        val userId = authRepository.currentUserId.first()
        // Get the most recent transaction that has a balance recorded
        val latestTransaction = transactionDao.getLatestTransactionWithBalance(accountId, userId)
        return latestTransaction?.balanceAfterTxn?.takeIf { it > 0.0 }
    }

    override fun getTaxDeductibleTransactions(startDate: LocalDate, endDate: LocalDate): Flow<List<Activity>> {
        return authRepository.currentUserId.flatMapLatest { userId ->
            kotlinx.coroutines.flow.flow {
                val entities = transactionDao.getTaxDeductibleTransactions(startDate, endDate, userId)
                emit(entities.map { it.toDomain() })
            }
        }
    }
    
    // Conversion functions
    private fun CategoryEntity.toDomain(): Category {
        return Category(
            id = id,
            name = name,
            type = type,
            icon = icon,
            color = color,
            usageCount = usageCount,
            isUserDeletable = isUserDeletable,
            isHidden = isHidden,
            lastUsedAt = 0L // TODO: Add timestamp tracking in entity
        )
    }
    
    private fun Category.toEntity(userId: String?): CategoryEntity {
        return CategoryEntity(
            id = id,
            userId = userId,
            name = name,
            type = type,
            icon = icon,
            color = color,
            usageCount = usageCount,
            isUserDeletable = isUserDeletable,
            isHidden = isHidden
        )
    }
    
    private fun LearningRuleEntity.toDomain(): CategoryLearningRule {
        return CategoryLearningRule(
            id = id,
            descriptionPattern = merchantPattern,
            categoryId = categoryId,
            confidenceScore = confidenceScore,
            usageCount = usageCount,
            createdAt = createdAt,
            lastAppliedAt = lastUsedAt,
            createdByUserCorrection = true
        )
    }
    
    private fun CategoryLearningRule.toEntity(userId: String): LearningRuleEntity {
        return LearningRuleEntity(
            id = id,
            userId = userId,
            merchantPattern = descriptionPattern,
            categoryId = categoryId,
            confidenceScore = confidenceScore,
            usageCount = usageCount,
            createdAt = createdAt ?: java.time.LocalDateTime.now(),
            lastUsedAt = lastAppliedAt ?: java.time.LocalDateTime.now()
        )
    }
}
