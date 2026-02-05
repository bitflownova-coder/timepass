package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.bitflow.finance.data.local.entity.TransactionEntity
import kotlinx.coroutines.flow.Flow
import java.time.LocalDate
import com.bitflow.finance.domain.model.AppMode

@Dao
interface TransactionDao {
    @Query("SELECT * FROM transactions WHERE userId = :userId AND accountId = :accountId ORDER BY txnDate DESC")
    fun getTransactionsForAccount(accountId: Long, userId: String): Flow<List<TransactionEntity>>

    @Query("SELECT * FROM transactions WHERE userId = :userId AND context = :context ORDER BY txnDate DESC")
    fun getAllTransactions(userId: String, context: AppMode): Flow<List<TransactionEntity>>

    @Query("SELECT * FROM transactions WHERE userId = :userId AND context = :context AND txnDate BETWEEN :startDate AND :endDate ORDER BY txnDate DESC")
    fun getTransactionsInPeriod(startDate: LocalDate, endDate: LocalDate, userId: String, context: AppMode): Flow<List<TransactionEntity>>

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertTransaction(transaction: TransactionEntity): Long

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertTransactions(transactions: List<TransactionEntity>)

    @Update
    suspend fun updateTransaction(transaction: TransactionEntity)
    
    @Query("SELECT * FROM transactions WHERE userId = :userId AND accountId = :accountId AND txnDate = :date AND amount = :amount AND description = :description")
    suspend fun findExistingTransaction(accountId: Long, date: LocalDate, amount: Double, description: String, userId: String): TransactionEntity?

    @Query("SELECT * FROM transactions WHERE id = :id AND userId = :userId")
    suspend fun getTransactionById(id: Long, userId: String): TransactionEntity?
    
    /**
     * Bulk update transactions to new category (for category merge/delete)
     */
    @Query("UPDATE transactions SET categoryId = :newCategoryId WHERE categoryId = :oldCategoryId AND userId = :userId")
    suspend fun updateTransactionsCategory(oldCategoryId: Long, newCategoryId: Long, userId: String)
    
    /**
     * Get transactions by merchant for pattern detection
     */
    @Query("SELECT * FROM transactions WHERE userId = :userId AND merchantName = :merchantName ORDER BY txnDate DESC")
    suspend fun getTransactionsByMerchant(merchantName: String, userId: String): List<TransactionEntity>
    
    /**
     * Find recurring patterns - transactions in last 3 months grouped by merchant
     */
    @Query("""
        SELECT * FROM transactions 
        WHERE userId = :userId AND txnDate >= :startDate 
        AND merchantName IS NOT NULL 
        ORDER BY merchantName, txnDate DESC
    """)
    suspend fun getTransactionsForSubscriptionDetection(startDate: LocalDate, userId: String): List<TransactionEntity>
    
    /**
     * Get recent transactions (for home screen)
     */
    @Query("SELECT * FROM transactions WHERE userId = :userId AND context = :context ORDER BY txnDate DESC, createdAt DESC LIMIT :limit")
    fun getRecentTransactions(limit: Int = 5, userId: String, context: AppMode): Flow<List<TransactionEntity>>
    
    /**
     * Delete transaction by ID (with undo support)
     */
    @Query("DELETE FROM transactions WHERE id = :id AND userId = :userId")
    suspend fun deleteTransaction(id: Long, userId: String)
    
    /**
     * Performance optimization: Get all transactions synchronously for deduplication
     */
    @Query("SELECT * FROM transactions WHERE userId = :userId AND accountId = :accountId")
    suspend fun getAllTransactionsSync(accountId: Long, userId: String): List<TransactionEntity>
    
    /**
     * Performance optimization: Calculate balance directly in database
     */
    @Query("""
        SELECT :initialBalance + 
        COALESCE((SELECT SUM(amount) FROM transactions WHERE userId = :userId AND accountId = :accountId AND direction = 'INCOME'), 0) -
        COALESCE((SELECT SUM(amount) FROM transactions WHERE userId = :userId AND accountId = :accountId AND direction = 'EXPENSE'), 0)
    """)
    suspend fun calculateBalance(accountId: Long, initialBalance: Double, userId: String): Double
    
    /**
     * Get the most recent transaction with a recorded balance
     */
    @Query("SELECT * FROM transactions WHERE userId = :userId AND accountId = :accountId ORDER BY txnDate DESC, createdAt DESC LIMIT 1")
    suspend fun getLatestTransactionWithBalance(accountId: Long, userId: String): TransactionEntity?
    
    /**
     * Get total spent in a category within a date range (for budget tracking)
     */
    @Query("""
        SELECT COALESCE(SUM(amount), 0) FROM transactions 
        WHERE userId = :userId AND categoryId = :categoryId 
        AND direction = 'EXPENSE'
        AND createdAt BETWEEN :startDate AND :endDate
    """)
    suspend fun getTotalSpentInCategory(categoryId: Long, userId: String, startDate: Long, endDate: Long): Double

    @Query("""
        SELECT t.* FROM transactions t
        INNER JOIN categories c ON t.categoryId = c.id
        WHERE t.userId = :userId 
        AND c.isTaxDeductible = 1
        AND t.txnDate BETWEEN :startDate AND :endDate
        ORDER BY t.txnDate DESC
    """)
    suspend fun getTaxDeductibleTransactions(startDate: LocalDate, endDate: LocalDate, userId: String): List<TransactionEntity>

    @Query("SELECT * FROM transactions")
    suspend fun getAllTransactionsRaw(): List<TransactionEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTransactionRaw(transaction: TransactionEntity)
}
