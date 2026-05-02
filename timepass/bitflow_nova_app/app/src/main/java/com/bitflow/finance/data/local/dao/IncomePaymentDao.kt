package com.bitflow.finance.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.bitflow.finance.data.local.entity.IncomePaymentEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface IncomePaymentDao {
    
    @Query("SELECT * FROM income_payments WHERE userId = :userId ORDER BY paymentDate DESC")
    fun getAllPayments(userId: String): Flow<List<IncomePaymentEntity>>
    
    @Query("SELECT * FROM income_payments WHERE clientId = :clientId AND userId = :userId ORDER BY paymentDate DESC")
    fun getPaymentsByClient(clientId: Long, userId: String): Flow<List<IncomePaymentEntity>>
    
    @Query("SELECT * FROM income_payments WHERE id = :id AND userId = :userId")
    suspend fun getPaymentById(id: Long, userId: String): IncomePaymentEntity?
    
    @Query("SELECT * FROM income_payments WHERE invoiceGenerated = 0 AND userId = :userId ORDER BY paymentDate DESC")
    fun getPaymentsWithoutInvoice(userId: String): Flow<List<IncomePaymentEntity>>
    
    @Query("SELECT SUM(amount) FROM income_payments WHERE userId = :userId")
    fun getTotalIncome(userId: String): Flow<Double?>
    
    @Query("SELECT SUM(amount) FROM income_payments WHERE paymentDate >= :startDate AND paymentDate <= :endDate AND userId = :userId")
    fun getIncomeForPeriod(startDate: Long, endDate: Long, userId: String): Flow<Double?>
    
    @Query("SELECT SUM(amount) FROM income_payments WHERE clientId = :clientId AND userId = :userId")
    fun getTotalIncomeFromClient(clientId: Long, userId: String): Flow<Double?>
    
    @Query("""
        SELECT strftime('%Y-%m', paymentDate/1000, 'unixepoch') as month, SUM(amount) as total 
        FROM income_payments 
        WHERE userId = :userId 
        GROUP BY month 
        ORDER BY month DESC 
        LIMIT 12
    """)
    fun getMonthlyIncome(userId: String): Flow<List<MonthlyTotal>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPayment(payment: IncomePaymentEntity): Long
    
    @Update
    suspend fun updatePayment(payment: IncomePaymentEntity)
    
    @Delete
    suspend fun deletePayment(payment: IncomePaymentEntity)
    
    @Query("DELETE FROM income_payments WHERE discussionId = :discussionId AND userId = :userId")
    suspend fun deletePaymentByDiscussionId(discussionId: Long, userId: String)
    
    @Query("UPDATE income_payments SET invoiceGenerated = 1, invoiceNumber = :invoiceNumber, invoiceId = :invoiceId WHERE id = :id")
    suspend fun markInvoiceGenerated(id: Long, invoiceNumber: String, invoiceId: Long)
}

data class MonthlyTotal(
    val month: String,
    val total: Double
)
