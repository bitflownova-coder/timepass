package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.bitflow.finance.data.local.entity.ExpenseRecordEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ExpenseRecordDao {
    
    @Query("SELECT * FROM expense_records WHERE userId = :userId ORDER BY expenseDate DESC")
    fun getAllExpenses(userId: String): Flow<List<ExpenseRecordEntity>>
    
    @Query("SELECT * FROM expense_records WHERE expenseType = :type AND userId = :userId ORDER BY expenseDate DESC")
    fun getExpensesByType(type: String, userId: String): Flow<List<ExpenseRecordEntity>>
    
    @Query("SELECT * FROM expense_records WHERE category = :category AND userId = :userId ORDER BY expenseDate DESC")
    fun getExpensesByCategory(category: String, userId: String): Flow<List<ExpenseRecordEntity>>
    
    @Query("SELECT * FROM expense_records WHERE isRecurring = 1 AND userId = :userId ORDER BY nextDueDate ASC")
    fun getSubscriptions(userId: String): Flow<List<ExpenseRecordEntity>>
    
    @Query("SELECT * FROM expense_records WHERE id = :id AND userId = :userId")
    suspend fun getExpenseById(id: Long, userId: String): ExpenseRecordEntity?
    
    @Query("SELECT SUM(amount) FROM expense_records WHERE userId = :userId")
    fun getTotalExpenses(userId: String): Flow<Double?>
    
    @Query("SELECT SUM(amount) FROM expense_records WHERE expenseDate >= :startDate AND expenseDate <= :endDate AND userId = :userId")
    fun getExpensesForPeriod(startDate: Long, endDate: Long, userId: String): Flow<Double?>
    
    @Query("SELECT SUM(amount) FROM expense_records WHERE expenseType = 'subscription' AND userId = :userId")
    fun getTotalSubscriptions(userId: String): Flow<Double?>
    
    @Query("SELECT SUM(amount) FROM expense_records WHERE expenseType = 'one_time' AND userId = :userId")
    fun getTotalOneTime(userId: String): Flow<Double?>
    
    @Query("""
        SELECT category, SUM(amount) as total 
        FROM expense_records 
        WHERE userId = :userId 
        GROUP BY category 
        ORDER BY total DESC
    """)
    fun getExpensesByCategories(userId: String): Flow<List<CategoryTotal>>
    
    @Query("""
        SELECT strftime('%Y-%m', expenseDate/1000, 'unixepoch') as month, SUM(amount) as total 
        FROM expense_records 
        WHERE userId = :userId 
        GROUP BY month 
        ORDER BY month DESC 
        LIMIT 12
    """)
    fun getMonthlyExpenses(userId: String): Flow<List<MonthlyTotal>>
    
    @Query("SELECT * FROM expense_records WHERE billAttached = 0 AND userId = :userId ORDER BY expenseDate DESC")
    fun getExpensesWithoutBill(userId: String): Flow<List<ExpenseRecordEntity>>
    
    @Query("SELECT * FROM expense_records WHERE isRecurring = 1 AND nextDueDate <= :date AND userId = :userId")
    fun getUpcomingSubscriptions(date: Long, userId: String): Flow<List<ExpenseRecordEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertExpense(expense: ExpenseRecordEntity): Long
    
    @Update
    suspend fun updateExpense(expense: ExpenseRecordEntity)
    
    @Delete
    suspend fun deleteExpense(expense: ExpenseRecordEntity)
    
    @Query("UPDATE expense_records SET billAttached = 1, billPath = :billPath WHERE id = :id")
    suspend fun attachBill(id: Long, billPath: String)
}

data class CategoryTotal(
    val category: String,
    val total: Double
)
